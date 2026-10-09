from app.services.content_cleaner import clean_html_page, build_compact_website_dossier
from app.crawler.fetcher import FetchedPage


def test_clean_html_page():
    raw_html = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>Global Care - International Surgery</title>
        <style>.hero { color: red; }</style>
        <script>console.log("tracking");</script>
      </head>
      <body>
        <div class="cookie-banner">We use cookies to enhance your experience. Accept.</div>
        <nav><a href="/">Home</a><a href="/about">About</a></nav>
        <h1>Global Care Facilitation</h1>
        <p>We coordinate cross-border medical treatments in top accredited hospitals in Bangkok and Istanbul.</p>
        <h2>Our Services</h2>
        <ul>
          <li>Free medical quote and doctor consultation</li>
          <li>Airport transfer and English coordinator</li>
          <li>Hospital admission assistance</li>
        </ul>
        <footer>Copyright 2026. All rights reserved.</footer>
      </body>
    </html>
    """
    clean_text = clean_html_page(raw_html)
    assert "cross-border medical treatments" in clean_text
    assert "Airport transfer and English coordinator" in clean_text
    # Boilerplate removed
    assert "We use cookies" not in clean_text
    assert "console.log" not in clean_text
    assert "Copyright 2026" not in clean_text


def test_build_compact_website_dossier():
    p1 = FetchedPage(
        url="https://example.com",
        page_type="HOMEPAGE",
        page_title="Home",
        raw_html="<h1>Welcome to Example Medical</h1><p>We arrange medical surgery abroad.</p>",
        is_success=True
    )
    p2 = FetchedPage(
        url="https://example.com/blog/tips",
        page_type="BLOG",
        page_title="Blog Tips",
        raw_html="<h1>5 Travel Tips</h1><p>Here are some packing tips when flying.</p>",
        is_success=True
    )
    dossier = build_compact_website_dossier([p1, p2])
    assert dossier["total_pages"] == 2
    assert "https://example.com" in dossier["dossier_text"]
    assert len(dossier["dossier_hash"]) == 64
