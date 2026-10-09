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
        Executes a targeted, high-speed crawl on the given company website.
        Fetches homepage first, discovers top commercial links,
        and fetches up to 2 high-value subpages in parallel.
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

        async with httpx.AsyncClient(verify=True, limits=httpx.Limits(max_connections=10)) as client:
            # 1. Fetch Homepage
            resp, error = await self._safe_fetch_page(client, start_url)
            if error or not resp or resp.status_code >= 400:
                err_msg = error or (f"HTTP {resp.status_code}" if resp else "Empty response")
                page = FetchedPage(
                    url=start_url,
                    page_type="HOMEPAGE",
                    http_status=resp.status_code if resp else None,
                    error_reason=err_msg,
                    is_success=False,
                )
                result.pages_failed += 1
                result.pages.append(page)
                result.status = "BLOCKED" if "robots.txt" in err_msg.lower() else "FAILED"
                result.failure_reason = err_msg
                result.crawl_coverage = "FAILED"
                return result

            # Parse Homepage
            html_text = resp.text
            content_hash = hashlib.sha256(html_text.encode("utf-8")).hexdigest()
            soup = BeautifulSoup(html_text, "html.parser")
            title_tag = soup.find("title")
            title = title_tag.get_text(strip=True) if title_tag else ""

            home_page = FetchedPage(
                url=start_url,
                page_type="HOMEPAGE",
                page_title=title[:500],
                http_status=resp.status_code,
                content_hash=content_hash,
                raw_html=html_text,
                is_success=True,
            )
            result.pages_fetched += 1
            result.pages.append(home_page)

            # 2. Extract and Prioritize Subpages
            discovered = extract_internal_links(start_url, html_text, max_links=30)
            result.pages_discovered = 1 + len(discovered)

            # Sort discovered links by business value
            priority_subpages = []
            for next_url, priority_score in discovered:
                p_type = classify_page_type(next_url)
                if p_type in ("SERVICES", "INTERNATIONAL_PROGRAM", "ABOUT", "TEAM"):
                    priority_subpages.append((priority_score + 10, next_url))
                elif p_type != "BLOG":
                    priority_subpages.append((priority_score, next_url))

            priority_subpages.sort(key=lambda x: x[0], reverse=True)
            max_subpages = max(1, self.max_pages - 1)
            candidate_urls = [u for _, u in priority_subpages[:max_subpages]]

            # 3. Parallel Fetch Subpages
            if candidate_urls:
                async def fetch_one_subpage(target_u: str):
                    s_resp, s_err = await self._safe_fetch_page(client, target_u)
                    if s_err or not s_resp or s_resp.status_code >= 400:
                        return FetchedPage(
                            url=target_u,
                            page_type=classify_page_type(target_u),
                            http_status=s_resp.status_code if s_resp else None,
                            error_reason=s_err or (f"HTTP {s_resp.status_code}" if s_resp else "Error"),
                            is_success=False,
                        )
                    s_html = s_resp.text
                    s_hash = hashlib.sha256(s_html.encode("utf-8")).hexdigest()
                    s_soup = BeautifulSoup(s_html, "html.parser")
                    s_title_tag = s_soup.find("title")
                    s_title = s_title_tag.get_text(strip=True) if s_title_tag else ""
                    return FetchedPage(
                        url=target_u,
                        page_type=classify_page_type(target_u, s_title),
                        page_title=s_title[:500],
                        http_status=s_resp.status_code,
                        content_hash=s_hash,
                        raw_html=s_html,
                        is_success=True,
                    )

                subpage_results = await asyncio.gather(*(fetch_one_subpage(u) for u in candidate_urls), return_exceptions=True)
                for sp in subpage_results:
                    if isinstance(sp, FetchedPage):
                        if sp.is_success:
                            result.pages_fetched += 1
                        else:
                            result.pages_failed += 1
                        result.pages.append(sp)

        # 4. Final status
        successful_pages = [p for p in result.pages if p.is_success]
        if not successful_pages:
            result.status = "FAILED"
            result.crawl_coverage = "FAILED"
        elif len(successful_pages) == 1:
            result.status = "COMPLETED"
            result.crawl_coverage = "SHALLOW"
        else:
            result.status = "COMPLETED"
            result.crawl_coverage = "FULL"

        return result
