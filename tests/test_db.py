from app.db import Database


def capture_payload(content: str, content_hash: str, url: str = "https://example.org/source"):
    return {
        "url": url,
        "canonical_url": url,
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


def test_project_membership_and_evidence_relationships(database: Database):
    first, _, _ = database.save_capture(
        capture_payload("first evidence", "hash-first", "https://example.org/first")
    )
    second, _, _ = database.save_capture(
        capture_payload("second evidence", "hash-second", "https://example.org/second")
    )
    project = database.create_project(
        "Evidence comparison",
        "Do the sources agree?",
        "Compare two public sources.",
        "comparison",
    )
    database.add_source_to_project(project["id"], first["id"], "Primary reference")
    database.add_source_to_project(project["id"], second["id"], "Independent check")

    members = database.list_project_sources(project["id"])
    assert {source["id"] for source in members} == {first["id"], second["id"]}
    assert database.get_project(project["id"])["source_count"] == 2

    relationship = database.upsert_relationship(
        first["id"],
        second["id"],
        "supports",
        "high",
        "Both sources independently report the same bounded fact.",
    )
    assert relationship["relationship"] == "supports"
    project_relationships = database.list_project_relationships(project["id"])
    assert len(project_relationships) == 1
    assert project_relationships[0]["strength"] == "high"
    assert len(database.list_source_relationships(first["id"])) == 1


def test_saved_searches_are_repeatable_and_updatable(database: Database):
    saved = database.save_search("Primary docs", "DNSSEC", "external-primary")
    assert saved["query"] == "DNSSEC"
    database.save_search("Primary docs", "DNSSEC validation", "external-primary")
    searches = database.list_saved_searches()
    assert len(searches) == 1
    assert searches[0]["query"] == "DNSSEC validation"
    database.delete_saved_search(searches[0]["id"])
    assert database.list_saved_searches() == []


def test_schema_migration_version_is_recorded(database: Database):
    assert database.schema_version() == 2
