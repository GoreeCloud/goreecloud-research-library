from app.db import Database


def capture_payload(content: str, content_hash: str):
    return {
        "url": "https://example.org/source",
        "canonical_url": "https://example.org/source",
        "title": "Example source",
        "author": "Example Author",
        "publisher": "Example Org",
        "published_at": "2026-09-01",
        "source_type": "web",
        "excerpt": content[:80],
        "content": content,
        "content_hash": content_hash,
        "http_status": 200,
        "content_type": "text/html",
        "fetched_at": "2026-09-06T14:00:00+00:00",
        "accessed_at": "2026-09-06T14:00:00+00:00",
    }


def test_capture_creates_source_snapshot_and_change_history(database: Database):
    source, created, changed = database.save_capture(capture_payload("alpha", "hash-alpha"))
    assert created is True
    assert changed is True
    assert len(database.list_snapshots(source["id"])) == 1

    source2, created2, changed2 = database.save_capture(capture_payload("alpha", "hash-alpha"))
    assert source2["id"] == source["id"]
    assert created2 is False
    assert changed2 is False
    assert len(database.list_snapshots(source["id"])) == 1

    source3, _, changed3 = database.save_capture(capture_payload("beta", "hash-beta"))
    assert source3["id"] == source["id"]
    assert changed3 is True
    assert len(database.list_snapshots(source["id"])) == 2


def test_metadata_and_claims_are_research_classified(database: Database):
    source, _, _ = database.save_capture(capture_payload("evidence", "hash-evidence"))
    updated = database.update_source_metadata(
        source["id"],
        {
            "source_classification": "external-primary",
            "evidence_status": "verified-fact",
            "tags": "standards, docs",
            "notes": "Checked against the primary source.",
        },
    )
    assert updated["source_classification"] == "external-primary"
    claim = database.add_claim(
        source["id"],
        "A directly supported statement.",
        "verified-fact",
        "high",
        "Supported by the source text.",
    )
    assert claim["classification"] == "verified-fact"
    assert database.list_claims(source["id"])[0]["confidence"] == "high"
