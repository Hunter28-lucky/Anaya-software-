import re
from urllib.parse import urlparse, urljoin, parse_qsl, urlencode, urlunparse
from typing import List, Set, Tuple, Optional
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

# Keywords in URLs or text that indicate core business/service information
HIGH_PRIORITY_KEYWORDS = [
    "about", "about-us", "who-we-are", "company", "our-story", "overview",
    "service", "services", "solutions", "treatments", "procedures", "offerings",
    "international", "patients", "international-patients", "medical-travel",
    "destinations", "packages", "quote", "contact", "contact-us", "facilities"
]

# Keywords that indicate blog/editorial/ancillary content
LOW_PRIORITY_KEYWORDS = [
    "blog", "news", "articles", "press", "media", "posts", "insights",
    "author", "category", "tag", "privacy", "terms", "policy", "disclaimer",
    "careers", "jobs", "investors", "feed", "rss", "login", "signup"
]


def normalize_domain(url: str) -> str:
    """Extract clean domain name without www or ports."""
    try:
        parsed = urlparse(url if "://" in url else f"https://{url}")
        host = parsed.netloc.lower()
        if ":" in host:
            host = host.split(":")[0]
        if host.startswith("www."):
            host = host[4:]
        return host
    except Exception:
        return url.lower()


def normalize_url(raw_url: str) -> str:
    """
    Standardize URL:
    - Default to https if no scheme
    - Lowercase hostname
    - Strip tracking query parameters (utm_*, ref, fbclid, etc.)
    - Remove fragment
    - Remove trailing slash unless root path
    """
    if not raw_url:
        return ""
    url = raw_url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = parsed.path or "/"

    # Normalize trailing slash
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]

    # Clean query parameters
    filtered_queries = []
    if parsed.query:
        for k, v in parse_qsl(parsed.query, keep_blank_values=True):
            k_lower = k.lower()
            if not (k_lower.startswith("utm_") or k_lower in ("ref", "fbclid", "gclid", "yclid", "mc_cid")):
                filtered_queries.append((k, v))

    clean_query = urlencode(filtered_queries) if filtered_queries else ""

    return urlunparse((scheme, netloc, path, parsed.params, clean_query, ""))


def score_link_priority(url: str, anchor_text: str = "") -> int:
    """
    Scores how likely a page is to contain core business information vs noise.
    Higher score = fetched earlier.
    """
    score = 10
    url_lower = url.lower()
    text_lower = anchor_text.lower()

    # Boost high-priority sections
    for kw in HIGH_PRIORITY_KEYWORDS:
        if kw in url_lower or kw in text_lower:
            score += 25

    # Penalize low-priority / noise sections
    for kw in LOW_PRIORITY_KEYWORDS:
        if kw in url_lower:
            score -= 30

    # Shorter paths generally indicate top-level navigation
    path_depth = len([p for p in urlparse(url).path.split("/") if p])
    if path_depth <= 2:
        score += 5
    elif path_depth > 4:
        score -= 10

    return score


def extract_internal_links(base_url: str, html_content: str, max_links: int = 40) -> List[Tuple[str, int]]:
    """
    Extracts, filters, and ranks internal links from HTML.
    Returns list of (normalized_url, score) tuples sorted by descending score.
    """
    base_domain = normalize_domain(base_url)
    soup = BeautifulSoup(html_content, "html.parser")
    candidates = {}

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:", "whatsapp:")):
            continue

        try:
            absolute = urljoin(base_url, href)
            target_domain = normalize_domain(absolute)
            if target_domain != base_domain:
                continue  # Skip external links

            clean_target = normalize_url(absolute)
            # Skip non-HTML file extensions
            if re.search(r"\.(pdf|jpg|jpeg|png|gif|svg|zip|rar|mp4|mp3|exe|doc|docx|xls|xlsx)$", clean_target, re.I):
                continue

            anchor_text = a.get_text(strip=True)
            score = score_link_priority(clean_target, anchor_text)

            if clean_target not in candidates or candidates[clean_target] < score:
                candidates[clean_target] = score
        except Exception:
            continue

    sorted_links = sorted(candidates.items(), key=lambda x: x[1], reverse=True)
    return sorted_links[:max_links]


def parse_sitemap_urls(xml_content: str, base_url: str, max_urls: int = 50) -> List[str]:
    """Parse XML sitemap for internal URLs."""
    urls = []
    base_domain = normalize_domain(base_url)
    try:
        soup = BeautifulSoup(xml_content, "xml")
        for loc in soup.find_all("loc"):
            url_str = loc.get_text(strip=True)
            if url_str and normalize_domain(url_str) == base_domain:
                urls.append(normalize_url(url_str))
            if len(urls) >= max_urls:
                break
    except Exception as e:
        logger.debug(f"Failed to parse sitemap: {e}")
    return urls
