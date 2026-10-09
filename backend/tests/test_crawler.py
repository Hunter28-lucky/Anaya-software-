from app.crawler.discovery import (
    normalize_url,
    normalize_domain,
    score_link_priority,
    extract_internal_links,
)


def test_normalize_url():
    # Removes UTM and tracking tags
    raw = "https://example.com/services/?utm_source=google&utm_medium=cpc&ref=twitter#team"
    clean = normalize_url(raw)
    assert clean == "https://example.com/services"

    # Handles missing scheme
    assert normalize_url("example.com/about/") == "https://example.com/about"


def test_normalize_domain():
    assert normalize_domain("https://www.example.com/path") == "example.com"
    assert normalize_domain("http://healthtravel.co.uk:8080/intl") == "healthtravel.co.uk"


def test_score_link_priority():
    high_score = score_link_priority("https://example.com/international-patients", "International Services")
    low_score = score_link_priority("https://example.com/blog/2023/10/medical-trends", "Blog Article")
    assert high_score > low_score


def test_extract_internal_links():
    html = """
    <html>
      <body>
        <a href="/about-us">About Us</a>
        <a href="/services/orthopedic-travel">Medical Travel Packages</a>
        <a href="/blog/news-article-1">Latest News Post</a>
        <a href="https://otherdomain.com/outside">External Link</a>
        <a href="/brochure.pdf">Download PDF</a>
      </body>
    </html>
    """
    links = extract_internal_links("https://example.com", html)
    urls = [url for url, score in links]
    assert "https://example.com/about-us" in urls
    assert "https://example.com/services/orthopedic-travel" in urls
    # External link should be omitted
    assert "https://otherdomain.com/outside" not in urls
    # PDF should be omitted
    assert not any(u.endswith(".pdf") for u in urls)
