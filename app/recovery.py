from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
from typing import Any

from app.config import settings
from app.db import utc_now


BUNDLE_FORMAT = "goreecloud.research.recovery/1"
DATABASE_FILE = "research-library.sqlite3"
MANIFEST_FILE = "manifest.json"
SUPPORTED_SCHEMA_VERSION = 2
DURABLE_TABLES = (
    "sources",
    "snapshots",
    "claims",
    "schema_migrations",
    "projects",
    "project_sources",
    "source_relationships",
    "saved_searches",
)
MANIFEST_KEYS = {
    "format",
    "created_at",
    "schema_version",
    "database_file",
    "sha256",
    "size_bytes",
    "table_counts",
}


class RecoveryError(RuntimeError):
    """Raised when a recovery bundle cannot be safely created, verified, or restored."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_regular_file(path: Path, label: str) -> None:
    if path.is_symlink():
        raise RecoveryError(f"{label} must not be a symbolic link: {path}")
    if not path.is_file():
        raise RecoveryError(f"{label} must be a regular file: {path}")


def _reject_existing_symlink_components(path: Path) -> None:
    absolute = path.expanduser().absolute()
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current = current / part
        if current.exists() or current.is_symlink():
            if current.is_symlink():
                raise RecoveryError(f"Recovery path contains a symbolic-link component: {current}")


def _database_summary(path: Path) -> dict[str, Any]:
    _require_regular_file(path, "Database")
    uri = path.resolve().as_uri() + "?mode=ro"
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(uri, uri=True, timeout=5)
        connection.row_factory = sqlite3.Row
        integrity = [row[0] for row in connection.execute("PRAGMA integrity_check").fetchall()]
        if integrity != ["ok"]:
            raise RecoveryError(f"SQLite integrity check failed: {integrity!r}")

        foreign_key_failures = connection.execute("PRAGMA foreign_key_check").fetchall()
        if foreign_key_failures:
            raise RecoveryError("SQLite foreign-key check failed")

        existing_tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        missing = [name for name in DURABLE_TABLES if name not in existing_tables]
        if missing:
            raise RecoveryError(f"Database is missing required durable tables: {', '.join(missing)}")

        version_row = connection.execute(
            "SELECT MAX(version) AS version FROM schema_migrations"
        ).fetchone()
        schema_version = int(version_row["version"] or 0)
        table_counts = {
            table: int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
            for table in DURABLE_TABLES
        }
        return {
            "schema_version": schema_version,
            "table_counts": table_counts,
        }
    except sqlite3.Error as exc:
        raise RecoveryError(f"Unable to inspect SQLite database: {exc}") from exc
    finally:
        if connection is not None:
            connection.close()


def _validate_manifest(manifest: Any) -> dict[str, Any]:
    if not isinstance(manifest, dict):
        raise RecoveryError("Recovery manifest must be a JSON object")
    if set(manifest) != MANIFEST_KEYS:
        missing = sorted(MANIFEST_KEYS - set(manifest))
        unknown = sorted(set(manifest) - MANIFEST_KEYS)
        details = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if unknown:
            details.append("unknown " + ", ".join(unknown))
        raise RecoveryError("Invalid recovery manifest fields: " + "; ".join(details))

    if manifest["format"] != BUNDLE_FORMAT:
        raise RecoveryError("Unsupported recovery bundle format")
    if manifest["database_file"] != DATABASE_FILE:
        raise RecoveryError("Recovery manifest references an unexpected database file")

    if type(manifest["schema_version"]) is not int:
        raise RecoveryError("Recovery manifest schema_version must be an integer")
    if manifest["schema_version"] != SUPPORTED_SCHEMA_VERSION:
        raise RecoveryError(
            f"Recovery bundle schema {manifest['schema_version']} is not supported by this build"
        )

    created_at = manifest["created_at"]
    if not isinstance(created_at, str):
        raise RecoveryError("Recovery manifest created_at must be a string")
    try:
        parsed = datetime.fromisoformat(created_at)
    except ValueError as exc:
        raise RecoveryError("Recovery manifest created_at must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise RecoveryError("Recovery manifest created_at must include a timezone")

    sha256 = manifest["sha256"]
    if (
        not isinstance(sha256, str)
        or len(sha256) != 64
        or sha256 != sha256.lower()
        or any(character not in "0123456789abcdef" for character in sha256)
    ):
        raise RecoveryError("Recovery manifest sha256 must be a lowercase SHA-256 digest")

    if type(manifest["size_bytes"]) is not int or manifest["size_bytes"] < 0:
        raise RecoveryError("Recovery manifest size_bytes must be a non-negative integer")

    table_counts = manifest["table_counts"]
    if not isinstance(table_counts, dict) or set(table_counts) != set(DURABLE_TABLES):
        raise RecoveryError("Recovery manifest table_counts must cover the exact durable table set")
    for table, count in table_counts.items():
        if type(count) is not int or count < 0:
            raise RecoveryError(f"Recovery manifest row count for {table} is invalid")

    return manifest


def _write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    payload = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    fd, temporary_name = tempfile.mkstemp(prefix=".manifest-", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        temporary.unlink(missing_ok=True)
        raise


def create_backup(database_path: Path, bundle_dir: Path) -> dict[str, Any]:
    database_path = database_path.expanduser()
    bundle_dir = bundle_dir.expanduser()
    _reject_existing_symlink_components(database_path)
    _require_regular_file(database_path, "Source database")

    source_summary = _database_summary(database_path)
    if source_summary["schema_version"] != SUPPORTED_SCHEMA_VERSION:
        raise RecoveryError(
            f"Source database schema {source_summary['schema_version']} is not supported "
            f"by this recovery build"
        )

    _reject_existing_symlink_components(bundle_dir.parent)
    if bundle_dir.exists() or bundle_dir.is_symlink():
        raise RecoveryError(f"Recovery bundle destination already exists: {bundle_dir}")

    bundle_created = False
    source_connection: sqlite3.Connection | None = None
    backup_connection: sqlite3.Connection | None = None
    try:
        bundle_dir.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        bundle_dir.mkdir(mode=0o700)
        bundle_created = True

        backup_path = bundle_dir / DATABASE_FILE
        source_connection = sqlite3.connect(database_path, timeout=5)
        backup_connection = sqlite3.connect(backup_path, timeout=5)
        source_connection.backup(backup_connection)
        backup_connection.commit()
        backup_connection.close()
        backup_connection = None
        source_connection.close()
        source_connection = None
        os.chmod(backup_path, 0o600)

        backup_summary = _database_summary(backup_path)
        if backup_summary["schema_version"] != SUPPORTED_SCHEMA_VERSION:
            raise RecoveryError("Backup snapshot schema changed unexpectedly during backup")

        manifest = {
            "format": BUNDLE_FORMAT,
            "created_at": utc_now(),
            "schema_version": backup_summary["schema_version"],
            "database_file": DATABASE_FILE,
            "sha256": _sha256(backup_path),
            "size_bytes": backup_path.stat().st_size,
            "table_counts": backup_summary["table_counts"],
        }
        _write_manifest(bundle_dir / MANIFEST_FILE, manifest)
        return verify_backup(bundle_dir)
    except Exception:
        if bundle_created:
            shutil.rmtree(bundle_dir, ignore_errors=True)
        raise
    finally:
        if backup_connection is not None:
            backup_connection.close()
        if source_connection is not None:
            source_connection.close()


def verify_backup(bundle_dir: Path) -> dict[str, Any]:
    bundle_dir = bundle_dir.expanduser()
    _reject_existing_symlink_components(bundle_dir)
    if bundle_dir.is_symlink() or not bundle_dir.is_dir():
        raise RecoveryError(f"Recovery bundle must be a real directory: {bundle_dir}")

    manifest_path = bundle_dir / MANIFEST_FILE
    backup_path = bundle_dir / DATABASE_FILE
    _require_regular_file(manifest_path, "Recovery manifest")
    _require_regular_file(backup_path, "Recovery database")

    try:
        manifest = _validate_manifest(json.loads(manifest_path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError) as exc:
        raise RecoveryError(f"Unable to read recovery manifest: {exc}") from exc

    actual_size = backup_path.stat().st_size
    if actual_size != manifest["size_bytes"]:
        raise RecoveryError(
            f"Recovery database size mismatch: expected {manifest['size_bytes']}, got {actual_size}"
        )
    actual_digest = _sha256(backup_path)
    if actual_digest != manifest["sha256"]:
        raise RecoveryError("Recovery database SHA-256 mismatch")

    summary = _database_summary(backup_path)
    if summary["schema_version"] != manifest["schema_version"]:
        raise RecoveryError("Recovery database schema version does not match manifest")
    if summary["table_counts"] != manifest["table_counts"]:
        raise RecoveryError("Recovery database row counts do not match manifest")

    return manifest


def restore_backup(bundle_dir: Path, target_database_path: Path) -> dict[str, Any]:
    manifest = verify_backup(bundle_dir)
    source_path = bundle_dir.expanduser() / DATABASE_FILE
    target_database_path = target_database_path.expanduser()

    _reject_existing_symlink_components(target_database_path.parent)
    if target_database_path.exists() or target_database_path.is_symlink():
        raise RecoveryError(f"Restore target already exists: {target_database_path}")

    target_database_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{target_database_path.name}.restore-",
        dir=target_database_path.parent,
    )
    temporary = Path(temporary_name)
    published = False
    try:
        os.fchmod(fd, 0o600)
        with source_path.open("rb") as source, os.fdopen(fd, "wb") as target:
            shutil.copyfileobj(source, target, length=1024 * 1024)
            target.flush()
            os.fsync(target.fileno())

        if temporary.stat().st_size != manifest["size_bytes"]:
            raise RecoveryError("Restored temporary database size does not match manifest")
        if _sha256(temporary) != manifest["sha256"]:
            raise RecoveryError("Restored temporary database SHA-256 does not match manifest")
        summary = _database_summary(temporary)
        if summary["schema_version"] != manifest["schema_version"]:
            raise RecoveryError("Restored temporary database schema does not match manifest")
        if summary["table_counts"] != manifest["table_counts"]:
            raise RecoveryError("Restored temporary database row counts do not match manifest")

        try:
            os.link(temporary, target_database_path)
        except FileExistsError as exc:
            raise RecoveryError(f"Restore target appeared during restore: {target_database_path}") from exc
        except OSError as exc:
            raise RecoveryError(f"Unable to publish restored database atomically: {exc}") from exc
        published = True
        os.chmod(target_database_path, 0o600)
        temporary.unlink()

        final_summary = _database_summary(target_database_path)
        if final_summary["schema_version"] != manifest["schema_version"]:
            raise RecoveryError("Published restore schema does not match manifest")
        if final_summary["table_counts"] != manifest["table_counts"]:
            raise RecoveryError("Published restore row counts do not match manifest")
        if _sha256(target_database_path) != manifest["sha256"]:
            raise RecoveryError("Published restore SHA-256 does not match manifest")

        return manifest
    except Exception:
        temporary.unlink(missing_ok=True)
        if published:
            target_database_path.unlink(missing_ok=True)
        raise


def _path(value: str) -> Path:
    return Path(value).expanduser()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create, verify, or restore a GoreeCloud Research Library recovery bundle."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    backup = subparsers.add_parser("backup", help="Create a verified schema-v2 recovery bundle.")
    backup.add_argument("--output", required=True, type=_path, help="New bundle directory.")
    backup.add_argument(
        "--database",
        type=_path,
        default=settings.database_path,
        help="Source SQLite database (defaults to configured Research Library database).",
    )

    verify = subparsers.add_parser("verify", help="Verify an existing recovery bundle.")
    verify.add_argument("--bundle", required=True, type=_path, help="Recovery bundle directory.")

    restore = subparsers.add_parser(
        "restore",
        help="Restore a verified recovery bundle into a database path that does not exist.",
    )
    restore.add_argument("--bundle", required=True, type=_path, help="Recovery bundle directory.")
    restore.add_argument(
        "--target-database",
        type=_path,
        default=settings.database_path,
        help="Clean target database path (defaults to configured Research Library database).",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "backup":
            manifest = create_backup(args.database, args.output)
        elif args.command == "verify":
            manifest = verify_backup(args.bundle)
        else:
            manifest = restore_backup(args.bundle, args.target_database)
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return 0
    except RecoveryError as exc:
        print(f"Recovery error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
