from app.citations import bibtex_citation, csl_json_citation, markdown_citation, ris_citation


SOURCE = {
    "id": 7,
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


def test_csl_json_contains_portable_webpage_metadata():
    item = csl_json_citation(SOURCE)
    assert item["id"] == "goreecloud-source-7"
    assert item["type"] == "webpage"
    assert item["title"] == "A Useful Research Source"
    assert item["author"] == [{"literal": "Ada Example"}]
    assert item["issued"] == {"date-parts": [[2026, 9, 1]]}
    assert item["accessed"] == {"date-parts": [[2026, 9, 6]]}


def test_ris_contains_source_traceability_fields():
    text = ris_citation(SOURCE)
    assert text.startswith("TY  - ELEC")
    assert "TI  - A Useful Research Source" in text
    assert "AU  - Ada Example" in text
    assert "UR  - https://example.org/research" in text
    assert text.endswith("ER  -")
