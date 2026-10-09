import re
import hashlib
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from app.crawler.fetcher import FetchedPage

# Tags to completely drop
BOILERPLATE_TAGS = [
    "script", "style", "noscript", "svg", "canvas", "iframe",
    "nav", "footer", "header", "aside", "form"
]

# Classes or IDs that indicate cookie notices, ads, or navigation chrome
NOISE_SELECTORS = [
    ".cookie", "#cookie", ".consent", "#consent", ".gdpr",
    ".nav", ".navbar", ".menu", ".footer", ".sidebar",
    ".advertisement", ".ad-banner", ".social-share", ".popup",
    ".modal-cookie", ".tracking"
]


def clean_html_page(html_content: str, max_chars: int = 8000) -> str:
    """
    Cleans raw HTML into a structured, evidence-preserving text representation.
    Removes boilerplate, navigation, scripts, ads, and cookie banners.
    Preserves headings, lists, paragraphs, and business-relevant text.
    """
    if not html_content:
        return ""

    soup = BeautifulSoup(html_content, "html.parser")

    # 1. Remove unwanted tags
    for tag in soup(BOILERPLATE_TAGS):
        tag.decompose()

    # 2. Remove noise by CSS class / ID patterns
    for element in soup.find_all(True):
        if element.attrs:
            cls = " ".join(element.attrs.get("class", []))
            elem_id = str(element.attrs.get("id", ""))
            combined = f"{cls} {elem_id}".lower()
            if any(term in combined for term in ["cookie", "consent", "gdpr", "social-share", "newsletter-signup"]):
                element.decompose()

    # 3. Extract text hierarchically with headings preserved
    chunks = []
    for elem in soup.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
        txt = elem.get_text(separator=" ", strip=True)
        if not txt:
            continue
        # Deduplicate consecutive identical lines
        if chunks and chunks[-1] == txt:
            continue

        tag_name = elem.name.lower()
        if tag_name in ("h1", "h2"):
            chunks.append(f"\n## {txt}\n")
        elif tag_name in ("h3", "h4"):
            chunks.append(f"\n### {txt}\n")
        elif tag_name == "li":
            chunks.append(f"- {txt}")
        else:
            chunks.append(txt)

    raw_text = "\n".join(chunks)

    # 4. Collapse whitespace
    cleaned = re.sub(r"[ \t]+", " ", raw_text)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()

    return cleaned[:max_chars]


def build_compact_website_dossier(
    pages: List[FetchedPage],
    max_total_chars: int = 24000,
    per_page_budget: int = 4000
) -> Dict[str, Any]:
    """
    Aggregates cleaned pages into an evidence dossier prioritized by business value:
    - Prioritizes SERVICES, INTERNATIONAL_PROGRAM, ABOUT, HOMEPAGE
    - Deprioritizes BLOG and OTHER
    - Returns structured dossier text with explicit source URLs and page types
    """
    # Priority order
    type_priority = {
        "INTERNATIONAL_PROGRAM": 1,
        "SERVICES": 2,
        "ABOUT": 3,
        "HOMEPAGE": 4,
        "CONTACT": 5,
        "OTHER": 6,
        "BLOG": 7,
    }

    # Sort pages by priority
    sorted_pages = sorted(
        [p for p in pages if p.is_success and p.raw_html],
        key=lambda p: type_priority.get(p.page_type, 99)
    )

    dossier_sections = []
    total_chars = 0
    pages_included = []

    for p in sorted_pages:
        # Determine budget: blogs get much smaller character budget
        budget = per_page_budget if p.page_type != "BLOG" else min(per_page_budget // 2, 1200)
        clean_text = clean_html_page(p.raw_html, max_chars=budget)
        p.clean_text = clean_text
        p.tokens_estimated = len(clean_text) // 4

        if not clean_text or len(clean_text) < 50:
            continue

        if total_chars + len(clean_text) > max_total_chars:
            remaining = max_total_chars - total_chars
            if remaining > 300:
                clean_text = clean_text[:remaining] + "\n...[Content truncated for token budget]"
            else:
                break

        section = f"--- [PAGE START] ---\n"
        section += f"URL: {p.url}\n"
        section += f"PAGE_TYPE: {p.page_type}\n"
        section += f"PAGE_TITLE: {p.page_title or 'N/A'}\n"
        section += f"CONTENT:\n{clean_text}\n"
        section += f"--- [PAGE END] ---\n"

        dossier_sections.append(section)
        total_chars += len(section)
        pages_included.append({
            "url": p.url,
            "page_type": p.page_type,
            "title": p.page_title,
            "chars": len(clean_text)
        })

    combined_dossier = "\n\n".join(dossier_sections)
    dossier_hash = hashlib.sha256(combined_dossier.encode("utf-8")).hexdigest()

    return {
        "dossier_text": combined_dossier,
        "dossier_hash": dossier_hash,
        "total_chars": len(combined_dossier),
        "pages_included": pages_included,
        "total_pages": len(pages_included)
    }
