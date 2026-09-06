# Deployment and Recovery

## Development mode

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --host 127.0.0.1 --port 8088
```

Runtime state defaults to `./data/research-library.sqlite3`.

## Docker Compose

```bash
docker compose up --build -d
```

The supplied Compose file publishes the container on `127.0.0.1:8088`, drops Linux capabilities, enables `no-new-privileges`, uses a read-only root filesystem, and stores application state in a named volume mounted at `/data`.

The loopback binding is deliberate because the Development application has no application authentication.

## Configuration

See `.env.example`.

Important options:

- `GORECLOUD_RESEARCH_DATA_DIR`
- `GORECLOUD_RESEARCH_MAX_FETCH_BYTES`
- `GORECLOUD_RESEARCH_MAX_EXTRACT_CHARS`
- `GORECLOUD_RESEARCH_TIMEOUT_SECONDS`
- `GORECLOUD_RESEARCH_MAX_REDIRECTS`
- `GORECLOUD_RESEARCH_RESPECT_ROBOTS`
- `GORECLOUD_RESEARCH_ALLOW_PRIVATE_FETCH`

No reusable secret is required by the current Development application.

## Backup

For a stopped local instance, copy the SQLite database and preserve file integrity. For a live instance using WAL mode, prefer an SQLite-aware backup method or stop writes before filesystem copying so the database, WAL, and shared-memory state are handled correctly.

JSON export is an additional portability/recovery artifact, not a complete replacement for database backup because it does not preserve every future schema detail by definition. CSL JSON/RIS/CSV exports are specialized portability formats and are not database backups.

Before upgrading an important library, preserve a database backup plus a current JSON export.

## Restore

Development restore procedure:

1. stop the application;
2. provision the same or a compatible application version;
3. place the protected SQLite database at the configured data path;
4. start the application;
5. confirm `/healthz` reports `status: ok` and the expected schema version;
6. open representative source records and searches;
7. verify snapshots, claims, projects, project source memberships, saved searches, and source relationships;
8. verify JSON and citation export behavior.

A formal Everkeep-managed clean-environment restore test is still required before production/Stable acceptance.

## Upgrade and schema migrations

Version `0.2.0-dev` introduces the first explicit local schema-migration registry. Current schema version is **2**.

- Migration 1 records the initial source, snapshot, and claim schema as the baseline.
- Migration 2 adds projects, project-source membership, source relationships, saved searches, and supporting indexes.

Migration 2 is additive: it does not intentionally delete source/snapshot/claim data. The application records an applied migration once it completes.

For an important database:

1. stop writes or stop the application;
2. make a protected SQLite-aware backup;
3. preserve a JSON export;
4. start the new application version and allow the declared migration to apply;
5. confirm `/healthz` reports `schema_version: 2`;
6. validate representative existing sources/snapshots/claims plus new project/search functions;
7. retain the pre-upgrade backup until rollback/recovery confidence is established.

Future incompatible schema changes must define governed forward migration, backup, rollback/recovery behavior, and tests before acceptance rather than relying on ad hoc database edits.

## Uninstall / retirement

Stop the process/container and preserve or deliberately export/delete the data volume according to the user's retention decision. Do not remove a research database that is the only remaining copy of important evidence.
