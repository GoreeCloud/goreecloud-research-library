from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any, Iterable


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


SCHEMA = """
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 5000;

CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL UNIQUE,
    canonical_url TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    author TEXT NOT NULL DEFAULT '',
    publisher TEXT NOT NULL DEFAULT '',
    published_at TEXT NOT NULL DEFAULT '',
    source_type TEXT NOT NULL DEFAULT 'web',
    source_classification TEXT NOT NULL DEFAULT 'unknown-verification-required',
    evidence_status TEXT NOT NULL DEFAULT 'source-reported-vendor-claim',
    tags TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    excerpt TEXT NOT NULL DEFAULT '',
    content TEXT NOT NULL DEFAULT '',
    content_hash TEXT NOT NULL DEFAULT '',
    http_status INTEGER,
    content_type TEXT NOT NULL DEFAULT '',
    fetched_at TEXT NOT NULL DEFAULT '',
    accessed_at TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_changed_at TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    fetched_at TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    content TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    UNIQUE(source_id, content_hash)
);

CREATE TABLE IF NOT EXISTS claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER REFERENCES sources(id) ON DELETE SET NULL,
    statement TEXT NOT NULL,
    classification TEXT NOT NULL,
    confidence TEXT NOT NULL DEFAULT 'medium',
    evidence_note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL,
    description TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sources_updated_at ON sources(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_sources_classification ON sources(source_classification);
CREATE INDEX IF NOT EXISTS idx_snapshots_source_id ON snapshots(source_id, fetched_at DESC);
CREATE INDEX IF NOT EXISTS idx_claims_source_id ON claims(source_id, created_at DESC);
"""

MIGRATION_2 = """
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    question TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    tags TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS project_sources (
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    notes TEXT NOT NULL DEFAULT '',
    added_at TEXT NOT NULL,
    PRIMARY KEY(project_id, source_id)
);

CREATE TABLE IF NOT EXISTS source_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    to_source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    relationship TEXT NOT NULL,
    strength TEXT NOT NULL DEFAULT 'medium',
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    CHECK(from_source_id != to_source_id),
    UNIQUE(from_source_id, to_source_id, relationship)
);

CREATE TABLE IF NOT EXISTS saved_searches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    query TEXT NOT NULL DEFAULT '',
    classification TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_project_sources_source ON project_sources(source_id, project_id);
CREATE INDEX IF NOT EXISTS idx_relationships_from ON source_relationships(from_source_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_relationships_to ON source_relationships(to_source_id, created_at DESC);
"""


class Database:
    def __init__(self, path: Path):
        self.path = path
        self.fts_enabled = False

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            conn.executescript(SCHEMA)
            applied = {
                row["version"]
                for row in conn.execute("SELECT version FROM schema_migrations").fetchall()
            }
            if 1 not in applied:
                conn.execute(
                    "INSERT INTO schema_migrations(version, applied_at, description) VALUES (?, ?, ?)",
                    (1, utc_now(), "Initial source, snapshot, and claim schema"),
                )
            if 2 not in applied:
                conn.executescript(MIGRATION_2)
                conn.execute(
                    "INSERT INTO schema_migrations(version, applied_at, description) VALUES (?, ?, ?)",
                    (2, utc_now(), "Projects, source relationships, and saved searches"),
                )
            try:
                conn.execute(
                    """
                    CREATE VIRTUAL TABLE IF NOT EXISTS sources_fts USING fts5(
                        source_id UNINDEXED,
                        title,
                        content,
                        tags,
                        author,
                        publisher
                    )
                    """
                )
                self.fts_enabled = True
                count = conn.execute("SELECT COUNT(*) AS c FROM sources_fts").fetchone()["c"]
                if count == 0:
                    rows = conn.execute(
                        "SELECT id, title, content, tags, author, publisher FROM sources"
                    ).fetchall()
                    for row in rows:
                        self._index_source(conn, row)
            except sqlite3.OperationalError:
                self.fts_enabled = False

    def schema_version(self) -> int:
        with self.connect() as conn:
            row = conn.execute("SELECT MAX(version) AS version FROM schema_migrations").fetchone()
            return int(row["version"] or 0)

    def _index_source(self, conn: sqlite3.Connection, row: sqlite3.Row | dict[str, Any]) -> None:
        if not self.fts_enabled:
            return
        source_id = row["id"]
        conn.execute("DELETE FROM sources_fts WHERE source_id = ?", (source_id,))
        conn.execute(
            "INSERT INTO sources_fts(source_id, title, content, tags, author, publisher) VALUES (?, ?, ?, ?, ?, ?)",
            (
                source_id,
                row["title"],
                row["content"],
                row["tags"],
                row["author"],
                row["publisher"],
            ),
        )

    @staticmethod
    def _dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
        return dict(row) if row is not None else None

    def save_capture(self, capture: dict[str, Any]) -> tuple[dict[str, Any], bool, bool]:
        now = utc_now()
        with self.connect() as conn:
            existing = conn.execute("SELECT * FROM sources WHERE url = ?", (capture["url"],)).fetchone()
            created = existing is None
            changed = created or existing["content_hash"] != capture["content_hash"]
            if created:
                cursor = conn.execute(
                    """
                    INSERT INTO sources(
                        url, canonical_url, title, author, publisher, published_at, source_type,
                        excerpt, content, content_hash, http_status, content_type, fetched_at,
                        accessed_at, created_at, updated_at, last_changed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        capture["url"],
                        capture.get("canonical_url") or capture["url"],
                        capture.get("title", ""),
                        capture.get("author", ""),
                        capture.get("publisher", ""),
                        capture.get("published_at", ""),
                        capture.get("source_type", "web"),
                        capture.get("excerpt", ""),
                        capture.get("content", ""),
                        capture["content_hash"],
                        capture.get("http_status"),
                        capture.get("content_type", ""),
                        capture.get("fetched_at", now),
                        capture.get("accessed_at", now),
                        now,
                        now,
                        now,
                    ),
                )
                source_id = cursor.lastrowid
            else:
                source_id = existing["id"]
                conn.execute(
                    """
                    UPDATE sources SET
                        canonical_url = ?, title = ?, author = CASE WHEN author = '' THEN ? ELSE author END,
                        publisher = CASE WHEN publisher = '' THEN ? ELSE publisher END,
                        published_at = CASE WHEN published_at = '' THEN ? ELSE published_at END,
                        source_type = ?, excerpt = ?, content = ?, content_hash = ?, http_status = ?,
                        content_type = ?, fetched_at = ?, accessed_at = ?, updated_at = ?,
                        last_changed_at = CASE WHEN content_hash != ? THEN ? ELSE last_changed_at END
                    WHERE id = ?
                    """,
                    (
                        capture.get("canonical_url") or capture["url"],
                        capture.get("title", ""),
                        capture.get("author", ""),
                        capture.get("publisher", ""),
                        capture.get("published_at", ""),
                        capture.get("source_type", "web"),
                        capture.get("excerpt", ""),
                        capture.get("content", ""),
                        capture["content_hash"],
                        capture.get("http_status"),
                        capture.get("content_type", ""),
                        capture.get("fetched_at", now),
                        capture.get("accessed_at", now),
                        now,
                        capture["content_hash"],
                        now,
                        source_id,
                    ),
                )

            metadata = {
                "canonical_url": capture.get("canonical_url", ""),
                "author": capture.get("author", ""),
                "publisher": capture.get("publisher", ""),
                "published_at": capture.get("published_at", ""),
                "content_type": capture.get("content_type", ""),
                "source_type": capture.get("source_type", "web"),
            }
            conn.execute(
                """
                INSERT OR IGNORE INTO snapshots(source_id, fetched_at, content_hash, title, content, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    source_id,
                    capture.get("fetched_at", now),
                    capture["content_hash"],
                    capture.get("title", ""),
                    capture.get("content", ""),
                    json.dumps(metadata, sort_keys=True),
                ),
            )
            row = conn.execute("SELECT * FROM sources WHERE id = ?", (source_id,)).fetchone()
            self._index_source(conn, row)
            return dict(row), created, changed

    def get_source(self, source_id: int) -> dict[str, Any] | None:
        with self.connect() as conn:
            return self._dict(conn.execute("SELECT * FROM sources WHERE id = ?", (source_id,)).fetchone())

    def list_sources(
        self,
        query: str = "",
        classification: str = "",
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        limit = max(1, min(limit, 500))
        with self.connect() as conn:
            parameters: list[Any] = []
            where: list[str] = []
            if classification:
                where.append("s.source_classification = ?")
                parameters.append(classification)

            rows: Iterable[sqlite3.Row]
            if query.strip() and self.fts_enabled:
                tokens = [token for token in query.split() if token]
                expression = " AND ".join('"' + token.replace('"', '""') + '"' for token in tokens)
                try:
                    sql = (
                        "SELECT s.* FROM sources_fts f JOIN sources s ON s.id = f.source_id "
                        "WHERE sources_fts MATCH ?"
                    )
                    parameters = [expression] + parameters
                    if where:
                        sql += " AND " + " AND ".join(where)
                    sql += " ORDER BY rank, s.updated_at DESC LIMIT ?"
                    parameters.append(limit)
                    rows = conn.execute(sql, parameters).fetchall()
                    return [dict(row) for row in rows]
                except sqlite3.OperationalError:
                    pass

            if query.strip():
                wildcard = f"%{query.strip()}%"
                where.append(
                    "(s.title LIKE ? OR s.content LIKE ? OR s.url LIKE ? OR s.tags LIKE ? OR s.author LIKE ? OR s.publisher LIKE ?)"
                )
                parameters.extend([wildcard] * 6)
            sql = "SELECT s.* FROM sources s"
            if where:
                sql += " WHERE " + " AND ".join(where)
            sql += " ORDER BY s.updated_at DESC LIMIT ?"
            parameters.append(limit)
            rows = conn.execute(sql, parameters).fetchall()
            return [dict(row) for row in rows]

    def list_snapshots(self, source_id: int) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM snapshots WHERE source_id = ? ORDER BY fetched_at DESC", (source_id,)
            ).fetchall()
            return [dict(row) for row in rows]

    def update_source_metadata(self, source_id: int, values: dict[str, str]) -> dict[str, Any] | None:
        allowed = {
            "title",
            "author",
            "publisher",
            "published_at",
            "source_classification",
            "evidence_status",
            "tags",
            "notes",
        }
        filtered = {key: value.strip() for key, value in values.items() if key in allowed}
        if not filtered:
            return self.get_source(source_id)
        fields = ", ".join(f"{key} = ?" for key in filtered)
        params = list(filtered.values()) + [utc_now(), source_id]
        with self.connect() as conn:
            conn.execute(f"UPDATE sources SET {fields}, updated_at = ? WHERE id = ?", params)
            row = conn.execute("SELECT * FROM sources WHERE id = ?", (source_id,)).fetchone()
            if row:
                self._index_source(conn, row)
            return self._dict(row)

    def add_claim(
        self,
        source_id: int,
        statement: str,
        classification: str,
        confidence: str,
        evidence_note: str,
    ) -> dict[str, Any]:
        now = utc_now()
        with self.connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO claims(source_id, statement, classification, confidence, evidence_note, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (source_id, statement.strip(), classification, confidence, evidence_note.strip(), now),
            )
            row = conn.execute("SELECT * FROM claims WHERE id = ?", (cursor.lastrowid,)).fetchone()
            return dict(row)

    def list_claims(self, source_id: int) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM claims WHERE source_id = ? ORDER BY created_at DESC", (source_id,)
            ).fetchall()
            return [dict(row) for row in rows]

    def create_project(self, name: str, question: str = "", description: str = "", tags: str = "") -> dict[str, Any]:
        now = utc_now()
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Project name is required")
        with self.connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO projects(name, question, description, tags, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (clean_name, question.strip(), description.strip(), tags.strip(), now, now),
            )
            row = conn.execute("SELECT * FROM projects WHERE id = ?", (cursor.lastrowid,)).fetchone()
            return dict(row)

    def list_projects(self, limit: int = 100) -> list[dict[str, Any]]:
        limit = max(1, min(limit, 500))
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT p.*, COUNT(ps.source_id) AS source_count
                FROM projects p
                LEFT JOIN project_sources ps ON ps.project_id = p.id
                GROUP BY p.id
                ORDER BY p.updated_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]

    def get_project(self, project_id: int) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT p.*, COUNT(ps.source_id) AS source_count
                FROM projects p
                LEFT JOIN project_sources ps ON ps.project_id = p.id
                WHERE p.id = ?
                GROUP BY p.id
                """,
                (project_id,),
            ).fetchone()
            return self._dict(row)

    def add_source_to_project(self, project_id: int, source_id: int, notes: str = "") -> None:
        now = utc_now()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO project_sources(project_id, source_id, notes, added_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(project_id, source_id) DO UPDATE SET notes = excluded.notes
                """,
                (project_id, source_id, notes.strip(), now),
            )
            conn.execute("UPDATE projects SET updated_at = ? WHERE id = ?", (now, project_id))

    def remove_source_from_project(self, project_id: int, source_id: int) -> None:
        with self.connect() as conn:
            conn.execute(
                "DELETE FROM project_sources WHERE project_id = ? AND source_id = ?",
                (project_id, source_id),
            )
            conn.execute("UPDATE projects SET updated_at = ? WHERE id = ?", (utc_now(), project_id))

    def list_project_sources(self, project_id: int) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT s.*, ps.notes AS project_notes, ps.added_at AS project_added_at
                FROM project_sources ps
                JOIN sources s ON s.id = ps.source_id
                WHERE ps.project_id = ?
                ORDER BY ps.added_at DESC
                """,
                (project_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def list_source_projects(self, source_id: int) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT p.*, ps.notes AS membership_notes, ps.added_at
                FROM project_sources ps
                JOIN projects p ON p.id = ps.project_id
                WHERE ps.source_id = ?
                ORDER BY p.updated_at DESC
                """,
                (source_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def upsert_relationship(
        self,
        from_source_id: int,
        to_source_id: int,
        relationship: str,
        strength: str,
        note: str,
    ) -> dict[str, Any]:
        if from_source_id == to_source_id:
            raise ValueError("A source cannot be related to itself")
        now = utc_now()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO source_relationships(
                    from_source_id, to_source_id, relationship, strength, note, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(from_source_id, to_source_id, relationship)
                DO UPDATE SET strength = excluded.strength, note = excluded.note
                """,
                (from_source_id, to_source_id, relationship, strength, note.strip(), now),
            )
            row = conn.execute(
                """
                SELECT * FROM source_relationships
                WHERE from_source_id = ? AND to_source_id = ? AND relationship = ?
                """,
                (from_source_id, to_source_id, relationship),
            ).fetchone()
            return dict(row)

    def list_source_relationships(self, source_id: int) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT r.*, fs.title AS from_title, fs.url AS from_url,
                       ts.title AS to_title, ts.url AS to_url
                FROM source_relationships r
                JOIN sources fs ON fs.id = r.from_source_id
                JOIN sources ts ON ts.id = r.to_source_id
                WHERE r.from_source_id = ? OR r.to_source_id = ?
                ORDER BY r.created_at DESC
                """,
                (source_id, source_id),
            ).fetchall()
            return [dict(row) for row in rows]

    def list_project_relationships(self, project_id: int) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT r.*, fs.title AS from_title, ts.title AS to_title
                FROM source_relationships r
                JOIN sources fs ON fs.id = r.from_source_id
                JOIN sources ts ON ts.id = r.to_source_id
                JOIN project_sources pf ON pf.source_id = r.from_source_id AND pf.project_id = ?
                JOIN project_sources pt ON pt.source_id = r.to_source_id AND pt.project_id = ?
                ORDER BY r.created_at DESC
                """,
                (project_id, project_id),
            ).fetchall()
            return [dict(row) for row in rows]

    def save_search(self, name: str, query: str = "", classification: str = "") -> dict[str, Any]:
        now = utc_now()
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Saved search name is required")
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO saved_searches(name, query, classification, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    query = excluded.query,
                    classification = excluded.classification,
                    updated_at = excluded.updated_at
                """,
                (clean_name, query.strip(), classification.strip(), now, now),
            )
            row = conn.execute("SELECT * FROM saved_searches WHERE name = ?", (clean_name,)).fetchone()
            return dict(row)

    def list_saved_searches(self) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM saved_searches ORDER BY updated_at DESC").fetchall()
            return [dict(row) for row in rows]

    def delete_saved_search(self, search_id: int) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM saved_searches WHERE id = ?", (search_id,))

    def all_sources(self) -> list[dict[str, Any]]:
        return self.list_sources(limit=500)
