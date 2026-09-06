from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.db import Database
from app.recovery import (
    DATABASE_FILE,
    MANIFEST_FILE,
    RecoveryError,
    create_backup,
    restore_backup,
    verify_backup,
)


def capture_payload(content: str, content_hash: str, url: str):
    return {
        "url": url,
        "canonical_url": url,
        "title": f"Source {content}",
        "author": "Research Author",
        "publisher": "Research Publisher",
        "published_at": "2026-09-06",
        "source_type": "web",
        "excerpt": content,
        "content": content,
        "content_hash": content_hash,
        "http_status": 200,
        "content_type": "text/html",
        "fetched_at": "2026-09-06T17:00:00+00:00",
        "accessed_at": "2026-09-06T17:00:00+00:00",
    }


def seed_schema_v2_state(database: Database) -> tuple[int, int, int]:
    first, _, _ = database.save_capture(
        capture_payload("alpha evidence", "hash-alpha", "https://example.org/alpha")
    )
    database.save_capture(
        capture_payload("alpha evidence revised", "hash-alpha-2", "https://example.org/alpha")
    )
    second, _, _ = database.save_capture(
        capture_payload("beta evidence", "hash-beta", "https://example.org/beta")
    )
    database.update_source_metadata(
        first["id"],
        {
            "source_classification": "external-primary",
            "evidence_status": "verified-fact",
            "tags": "recovery, evidence",
            "notes": "Schema-v2 recovery fixture.",
        },
    )
    database.add_claim(
        first["id"],
        "A recovery fixture claim.",
        "verified-fact",
        "high",
        "Used to prove clean-target recovery preserves claims.",
    )
    project = database.create_project(
        "Recovery drill",
        "Can all schema-v2 durable state be restored?",
        "Automated clean-target recovery acceptance fixture.",
        "recovery",
    )
    database.add_source_to_project(project["id"], first["id"], "Primary")
    database.add_source_to_project(project["id"], second["id"], "Corroborating")
    database.upsert_relationship(
        first["id"],
        second["id"],
        "supports",
        "high",
        "Recovery relationship fixture.",
    )
    database.save_search("Recovery evidence", "alpha", "external-primary")
    return first["id"], second["id"], project["id"]


def test_recovery_bundle_round_trip_preserves_schema_v2_state(database: Database, tmp_path: Path):
    first_id, second_id, project_id = seed_schema_v2_state(database)
    bundle = tmp_path / "recovery-bundle"

    manifest = create_backup(database.path, bundle)
    assert manifest["format"] == "goreecloud.research.recovery/1"
    assert manifest["schema_version"] == 2
    assert manifest["table_counts"]["sources"] == 2
    assert manifest["table_counts"]["snapshots"] == 3
    assert manifest["table_counts"]["claims"] == 1
    assert manifest["table_counts"]["projects"] == 1
    assert manifest["table_counts"]["project_sources"] == 2
    assert manifest["table_counts"]["source_relationships"] == 1
    assert manifest["table_counts"]["saved_searches"] == 1
    assert (bundle / DATABASE_FILE).is_file()
    assert (bundle / MANIFEST_FILE).is_file()
    assert verify_backup(bundle) == manifest

    restored_path = tmp_path / "clean-target" / "research-library.sqlite3"
    restored_manifest = restore_backup(bundle, restored_path)
    assert restored_manifest == manifest

    restored = Database(restored_path)
    restored.initialize()
    assert restored.schema_version() == 2
    assert restored.get_source(first_id)["content"] == "alpha evidence revised"
    assert restored.get_source(second_id)["content"] == "beta evidence"
    assert len(restored.list_snapshots(first_id)) == 2
    assert restored.list_claims(first_id)[0]["statement"] == "A recovery fixture claim."
    assert restored.get_project(project_id)["source_count"] == 2
    assert len(restored.list_project_relationships(project_id)) == 1
    assert restored.list_saved_searches()[0]["name"] == "Recovery evidence"
    assert [row["id"] for row in restored.list_sources(query="alpha")] == [first_id]


def test_recovery_bundle_rejects_database_tampering(database: Database, tmp_path: Path):
    seed_schema_v2_state(database)
    bundle = tmp_path / "recovery-bundle"
    create_backup(database.path, bundle)

    with (bundle / DATABASE_FILE).open("ab") as handle:
        handle.write(b"tamper")

    with pytest.raises(RecoveryError, match="size mismatch"):
        verify_backup(bundle)


def test_recovery_bundle_rejects_manifest_shape_tampering(database: Database, tmp_path: Path):
    seed_schema_v2_state(database)
    bundle = tmp_path / "recovery-bundle"
    create_backup(database.path, bundle)

    manifest_path = bundle / MANIFEST_FILE
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["unexpected"] = True
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(RecoveryError, match="Invalid recovery manifest fields"):
        verify_backup(bundle)


def test_restore_refuses_to_overwrite_existing_database(database: Database, tmp_path: Path):
    seed_schema_v2_state(database)
    bundle = tmp_path / "recovery-bundle"
    create_backup(database.path, bundle)

    target = tmp_path / "existing.sqlite3"
    target.write_bytes(b"do-not-overwrite")
    original = target.read_bytes()

    with pytest.raises(RecoveryError, match="already exists"):
        restore_backup(bundle, target)

    assert target.read_bytes() == original


def test_restore_rejects_symlink_target_component(database: Database, tmp_path: Path):
    seed_schema_v2_state(database)
    bundle = tmp_path / "recovery-bundle"
    create_backup(database.path, bundle)

    real_dir = tmp_path / "real"
    real_dir.mkdir()
    linked_dir = tmp_path / "linked"
    linked_dir.symlink_to(real_dir, target_is_directory=True)

    with pytest.raises(RecoveryError, match="symbolic-link component"):
        restore_backup(bundle, linked_dir / "research-library.sqlite3")
