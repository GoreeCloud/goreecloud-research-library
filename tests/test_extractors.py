from app.extractors import content_hash, extract_html, extract_text


def test_html_extraction_prefers_article_and_metadata():
    html = b"""
    <html><head>
      <title>Fallback title</title>
      <meta property="og:title" content="Research title">
      <meta name="author" content="Ada Example">
      <meta property="og:site_name" content="Example Institute">
      <meta property="article:published_time" content="2026-09-01">
      <link rel="canonical" href="/canonical">
    </head><body>
      <nav>Noise</nav>
      <article><h1>Research title</h1><p>This is the useful evidence paragraph with enough material to retain.</p>
      <p>Second paragraph for the source record and research extraction.</p></article>
    </body></html>
    """
    doc = extract_html(html, "https://example.org/story", 20_000)
    assert doc.title == "Research title"
    assert doc.author == "Ada Example"
    assert doc.publisher == "Example Institute"
    assert doc.published_at == "2026-09-01"
    assert doc.canonical_url == "https://example.org/canonical"
    assert "useful evidence paragraph" in doc.content
    assert "Noise" not in doc.content


def test_text_extraction_and_hash_are_deterministic():
    doc = extract_text(b"Hello\n\nresearch world", "https://example.org/file.txt", 500)
    assert doc.source_type == "text"
    assert doc.content == "Hello\n\nresearch world"
    assert content_hash(doc.content) == content_hash(doc.content)
