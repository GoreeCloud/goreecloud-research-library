from app.citations import bibtex_citation, markdown_citation


SOURCE = {
    "title": "A Useful Research Source",
    "author": "Ada Example",
    "publisher": "Example Institute",
    "published_at": "2026-09-01",
    "accessed_at": "2026-09-06T14:00:00+00:00",
    "url": "https://example.org/research",
}


def test_markdown_citation_contains_traceability_fields():
    text = markdown_citation(SOURCE)
    assert "Ada Example" in text
    assert "A Useful Research Source" in text
    assert "2026-09-01" in text
    assert "Accessed 2026-09-06" in text


def test_bibtex_citation_contains_url_and_date():
    text = bibtex_citation(SOURCE)
    assert text.startswith("@online{")
    assert "https://example.org/research" in text
    assert "urldate = {2026-09-06}" in text
