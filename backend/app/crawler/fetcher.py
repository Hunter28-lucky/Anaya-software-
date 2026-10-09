import asyncio
import hashlib
import time
import logging
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup

from app.core.config import settings
from app.core.ssrf import validate_and_resolve_url, SSRFValidationError
from app.crawler.discovery import (
    normalize_url,
    normalize_domain,
    extract_internal_links,
    parse_sitemap_urls,
)
from app.crawler.robots import RobotsValidator

logger = logging.getLogger(__name__)


@dataclass
class FetchedPage:
    url: str
    page_type: str
    page_title: Optional[str] = None
    http_status: Optional[int] = None
    content_hash: Optional[str] = None
    raw_html: Optional[str] = None
    clean_text: Optional[str] = None
    error_reason: Optional[str] = None
    is_success: bool = False
    tokens_estimated: int = 0


@dataclass
class CrawlResult:
    domain: str
    starting_url: str
    status: str  # COMPLETED, PARTIAL, FAILED, BLOCKED, NO_USABLE_CONTENT
    pages_discovered: int = 0
    pages_fetched: int = 0
    pages_failed: int = 0
    crawl_coverage: str = "NONE"  # FULL, PARTIAL, SHALLOW, FAILED
    pages: List[FetchedPage] = field(default_factory=list)
    failure_reason: Optional[str] = None


def classify_page_type(url: str, title: str = "") -> str:
    """Classify the page type based on URL path and title."""
    parsed = urlparse(url)
    path = parsed.path.lower().strip("/")
    title_lower = (title or "").lower()

    if not path or path == "":
        return "HOMEPAGE"
    if any(k in path for k in ("about", "who-we-are", "company", "our-story")):
        return "ABOUT"
    if any(k in path for k in ("service", "services", "treatment", "procedure", "offering", "solution")):
        return "SERVICES"
    if any(k in path for k in ("international", "foreign", "travel", "medical-travel", "destination", "package")):
        return "INTERNATIONAL_PROGRAM"
    if any(k in path for k in ("contact", "get-in-touch", "location", "quote", "book")):
        return "CONTACT"
    if any(k in path for k in ("blog", "news", "article", "post", "press")):
        return "BLOG"
    if any(k in path for k in ("doctor", "physician", "specialist", "team")):
        return "TEAM"
    if any(k in title_lower for k in ("about us", "who we are")):
        return "ABOUT"
    if any(k in title_lower for k in ("service", "treatment", "package")):
        return "SERVICES"
    return "OTHER"


class CustomWebsiteCrawler:
    """
    Production-minded, SSRF-safe, polite web crawler.
    Crawls website entry point, discovers high-value business pages,
    respects robots.txt and limits, and records precise crawl status.
    """

    def __init__(
        self,
        max_pages: int = settings.CRAWLER_MAX_PAGES_PER_DOMAIN,
        timeout: float = settings.CRAWLER_TIMEOUT_SECONDS,
        user_agent: str = settings.CRAWLER_USER_AGENT,
        max_content_bytes: int = settings.CRAWLER_MAX_CONTENT_BYTES,
    ):
        self.max_pages = max_pages
        self.timeout = timeout
        self.user_agent = user_agent
        self.max_content_bytes = max_content_bytes
        self.robots_validator = RobotsValidator(user_agent=user_agent)

    async def _safe_fetch_page(
        self,
        client: httpx.AsyncClient,
        target_url: str,
        visited_redirects: Optional[Set[str]] = None,
    ) -> Tuple[Optional[httpx.Response], Optional[str]]:
        """
        Safely fetches a single URL, validating every redirect hop against SSRF.
        """
        if visited_redirects is None:
            visited_redirects = set()

        current_url = target_url
        max_redirects = 5

        for _ in range(max_redirects):
            # SSRF validation before network trip
            try:
                normalized, _ = validate_and_resolve_url(current_url)
                current_url = normalized
            except SSRFValidationError as e:
                return None, f"Blocked by SSRF Guard: {e}"

            if current_url in visited_redirects:
                return None, "Circular redirect detected"
            visited_redirects.add(current_url)

            # Check robots.txt
            allowed_by_robots = await self.robots_validator.can_fetch(client, current_url)
            if not allowed_by_robots:
                return None, "Disallowed by robots.txt"

            try:
                # Do not follow redirects automatically so we can validate each hop against SSRF
                resp = await client.get(
                    current_url,
                    follow_redirects=False,
                    timeout=self.timeout,
                    headers={"User-Agent": self.user_agent, "Accept": "text/html,application/xhtml+xml,*/*"},
                )

                # Check redirect status
                if resp.status_code in (301, 302, 303, 307, 308):
                    location = resp.headers.get("location")
                    if not location:
                        return None, f"Redirect HTTP {resp.status_code} with missing Location header"
                    # Resolve relative redirect
                    from urllib.parse import urljoin
                    next_url = urljoin(current_url, location)
                    current_url = next_url
                    continue

                # Content-Type check
                content_type = resp.headers.get("content-type", "").lower()
                if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
                    return None, f"Skipped non-HTML content type: {content_type}"

                # Size check
                content_length = resp.headers.get("content-length")
                if content_length and int(content_length) > self.max_content_bytes:
                    return None, f"Response size exceeds max budget ({content_length} bytes)"

                return resp, None

            except httpx.TimeoutException:
                return None, f"Connection timed out ({self.timeout}s)"
            except httpx.ConnectError as e:
                return None, f"Connection failed: {e}"
            except Exception as e:
                return None, f"HTTP fetch error: {str(e)}"

        return None, "Too many redirects"

    async def crawl_site(self, raw_start_url: str) -> CrawlResult:
        """
        Executes a targeted crawl on the given company website.
        """
        clean_url = normalize_url(raw_start_url)
        domain = normalize_domain(clean_url)
        result = CrawlResult(domain=domain, starting_url=clean_url, status="CRAWLING")

        # Initial SSRF check
        try:
            start_url, _ = validate_and_resolve_url(clean_url)
        except SSRFValidationError as e:
            result.status = "BLOCKED"
            result.failure_reason = f"SSRF Guard: {e}"
            return result

        discovered_urls: Set[str] = {start_url}
        visited_urls: Set[str] = set()
        queue: List[str] = [start_url]

        async with httpx.AsyncClient(verify=True, limits=httpx.Limits(max_connections=5)) as client:
            # Step 1: Optional Sitemap Discovery
            try:
                sitemap_url = f"https://{domain}/sitemap.xml"
                s_resp, _ = await self._safe_fetch_page(client, sitemap_url)
                if s_resp and s_resp.status_code == 200:
                    sitemap_links = parse_sitemap_urls(s_resp.text, start_url, max_urls=20)
                    for sl in sitemap_links:
                        if sl not in discovered_urls:
                            discovered_urls.add(sl)
                            queue.append(sl)
            except Exception as e:
                logger.debug(f"Sitemap check error: {e}")

            # Step 2: Crawl high-priority pages in queue up to self.max_pages
            while queue and len(result.pages) < self.max_pages:
                curr_url = queue.pop(0)
                if curr_url in visited_urls:
                    continue
                visited_urls.add(curr_url)

                # Polite delay
                await asyncio.sleep(settings.CRAWLER_PER_DOMAIN_DELAY)

                resp, error = await self._safe_fetch_page(client, curr_url)
                if error:
                    page = FetchedPage(
                        url=curr_url,
                        page_type=classify_page_type(curr_url),
                        error_reason=error,
                        is_success=False,
                    )
                    result.pages_failed += 1
                    result.pages.append(page)
                    continue

                if not resp or resp.status_code >= 400:
                    page = FetchedPage(
                        url=curr_url,
                        page_type=classify_page_type(curr_url),
                        http_status=resp.status_code if resp else None,
                        error_reason=f"HTTP {resp.status_code}" if resp else "Empty response",
                        is_success=False,
                    )
                    result.pages_failed += 1
                    result.pages.append(page)
                    continue

                html_text = resp.text
                content_hash = hashlib.sha256(html_text.encode("utf-8")).hexdigest()

                # Parse basic meta
                soup = BeautifulSoup(html_text, "html.parser")
                title_tag = soup.find("title")
                title = title_tag.get_text(strip=True) if title_tag else ""
                p_type = classify_page_type(curr_url, title)

                page = FetchedPage(
                    url=curr_url,
                    page_type=p_type,
                    page_title=title[:500],
                    http_status=resp.status_code,
                    content_hash=content_hash,
                    raw_html=html_text,
                    is_success=True,
                )
                result.pages_fetched += 1
                result.pages.append(page)

                # Discover more internal links from successful page
                if len(result.pages) < self.max_pages:
                    discovered = extract_internal_links(curr_url, html_text, max_links=25)
                    for next_url, _ in discovered:
                        if next_url not in discovered_urls:
                            discovered_urls.add(next_url)
                            queue.append(next_url)

        result.pages_discovered = len(discovered_urls)

        # Determine overall crawl status
        successful_pages = [p for p in result.pages if p.is_success]
        if not successful_pages:
            if any("robots.txt" in (p.error_reason or "") for p in result.pages):
                result.status = "BLOCKED"
                result.failure_reason = "Blocked by website robots.txt or access policy"
            else:
                result.status = "FAILED"
                result.failure_reason = "No pages could be fetched successfully"
            result.crawl_coverage = "FAILED"
        elif len(successful_pages) == 1 and result.pages_discovered > 1:
            result.status = "PARTIAL"
            result.crawl_coverage = "SHALLOW"
        elif len(successful_pages) >= 2:
            if result.pages_failed == 0 and len(queue) == 0:
                result.status = "COMPLETED"
                result.crawl_coverage = "FULL"
            else:
                result.status = "PARTIAL"
                result.crawl_coverage = "PARTIAL"
        else:
            result.status = "COMPLETED"
            result.crawl_coverage = "SHALLOW"

        return result
