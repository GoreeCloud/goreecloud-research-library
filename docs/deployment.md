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

For an important Development library, prefer the application-owned Recovery Bundle v1 instead of copying only the live SQLite main database file:

```bash
python -m app.recovery backup --output /protected/path/research-library-backup
```

The backup command uses SQLite's backup API, which produces a consistent snapshot of the WAL-mode database. The new output directory contains `research-library.sqlite3` and a strict `manifest.json` binding schema version, SHA-256, byte size, and durable table row counts. Creation fails if the destination already exists or path safety checks fail.

Verify a bundle independently before relying on it:

```bash
python -m app.recovery verify --bundle /protected/path/research-library-backup
```

Verification also requires SQLite integrity and foreign-key checks to pass and the complete schema-v2 durable table set to be present.

A stopped-instance SQLite-aware copy remains a valid low-level operator technique when performed correctly, but a filesystem copy of only the live main SQLite file is unsafe because WAL state may be omitted.

JSON export is an additional portability/recovery artifact, not a complete replacement for database backup because it does not preserve every future schema detail by definition. CSL JSON/RIS/CSV exports are specialized portability formats and are not database backups.

Before upgrading an important library, preserve a verified recovery bundle plus a current JSON export.

## Restore

Recovery Bundle v1 restores only into a database path that does not already exist:

```bash
python -m app.recovery restore \
  --bundle /protected/path/research-library-backup \
  --target-database /clean/path/research-library.sqlite3
```

The command verifies the source bundle before copying, writes a private temporary database in the target directory, re-verifies the temporary copy, publishes it with a same-filesystem no-overwrite hard link, and verifies the published target again. Existing targets and symbolic-link path components fail closed.

After restore:

1. configure the application to use the restored database path;
2. start the same or a compatible application version;
3. confirm `/healthz` reports `status: ok` and schema version 2;
4. open representative source records and searches;
5. verify snapshots, claims, projects, project source memberships, saved searches, and source relationships;
6. verify JSON and citation export behavior.

`tests/test_recovery.py` performs an automated clean-target round trip with representative schema-v2 state and verifies restored search behavior. This establishes Development evidence for the application-owned recovery primitive only. Formal Everkeep orchestration, protected backup custody, target-host recovery acceptance, retention/deletion policy, disaster recovery, and production/Stable acceptance remain open.

See `docs/recovery-bundle.md` for the complete format and safety contract.

## Upgrade and schema migrations

Version `0.2.0-dev` introduces the first explicit local schema-migration registry. Current schema version is **2**.

- Migration 1 records the initial source, snapshot, and claim schema as the baseline.
- Migration 2 adds projects, project-source membership, source relationships, saved searches, and supporting indexes.

Migration 2 is additive: it does not intentionally delete source/snapshot/claim data. The application records an applied migration once it completes.

For an important database:

1. stop writes or use Recovery Bundle v1 to take a verified SQLite snapshot;
2. preserve the verified recovery bundle in protected storage;
3. preserve a JSON export;
4. start the new application version and allow the declared migration to apply;
5. confirm `/healthz` reports `schema_version: 2`;
6. validate representative existing sources/snapshots/claims plus new project/search functions;
7. retain the pre-upgrade recovery bundle until rollback/recovery confidence is established.

Future incompatible schema changes must define governed forward migration, backup, rollback/recovery behavior, and tests before acceptance rather than relying on ad hoc database edits.

## Uninstall / retirement

Stop the process/container and preserve or deliberately export/delete the data volume and recovery bundles according to the user's retention decision. Do not remove a research database or recovery bundle that is the only remaining copy of important evidence.
