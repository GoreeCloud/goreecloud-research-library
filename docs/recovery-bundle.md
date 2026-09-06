# Recovery Bundle v1

## Status

GoreeCloud Research Library Recovery Bundle v1 is an **application-owned Development recovery primitive** for the current schema-v2 SQLite library. It is not, by itself, GoreeCloud Everkeep integration or production recovery acceptance.

The implementation lives in `app/recovery.py` and is intentionally narrow: create a consistent SQLite backup, bind it to a strict integrity manifest, verify it, and restore it only into a clean target path.

## Bundle format

A bundle is a private directory containing exactly the two files required by the current recovery contract:

- `research-library.sqlite3` — SQLite backup produced with SQLite's backup API;
- `manifest.json` — `goreecloud.research.recovery/1` integrity and schema metadata.

The manifest binds:

- bundle format;
- creation time;
- schema version;
- fixed database filename;
- SHA-256 of the database backup;
- database byte size;
- durable row counts for sources, snapshots, claims, schema migrations, projects, project memberships, source relationships, and saved searches.

The verifier additionally requires SQLite `PRAGMA integrity_check` to return `ok`, requires `PRAGMA foreign_key_check` to return no failures, requires the complete schema-v2 durable table set, and compares the database's observed schema and row counts with the manifest.

## Create a backup

From the repository environment:

```bash
python -m app.recovery backup --output /protected/path/research-library-backup-20260906
```

The command uses the configured Research Library database by default. To select a specific database explicitly:

```bash
python -m app.recovery backup \
  --database /path/to/research-library.sqlite3 \
  --output /protected/path/research-library-backup-20260906
```

The output directory must not already exist. Existing symbolic-link path components are rejected. The SQLite backup API is used so a WAL-mode database can be copied consistently without relying on an unsafe single-file copy of a live database.

## Verify a bundle

```bash
python -m app.recovery verify \
  --bundle /protected/path/research-library-backup-20260906
```

Verification fails closed for malformed or unknown manifest fields, an unsupported schema version, missing durable tables, SQLite integrity or foreign-key failures, row-count disagreement, byte-size mismatch, SHA-256 mismatch, or symbolic-link substitution of the bundle/database/manifest path.

## Restore into a clean target

```bash
python -m app.recovery restore \
  --bundle /protected/path/research-library-backup-20260906 \
  --target-database /clean/path/research-library.sqlite3
```

Restore deliberately refuses to overwrite an existing database. It copies the verified database into a private temporary file in the target directory, re-verifies the temporary copy, then publishes it through a same-filesystem no-overwrite hard link. The published target is rechecked again before success is returned.

This clean-target rule is intended to prevent a recovery action from silently replacing the only existing database. Replacing an existing deployment remains a separate, explicitly governed operational migration/rollback workflow.

## Automated clean-environment drill

`tests/test_recovery.py` creates representative schema-v2 state containing:

- two sources and three snapshots;
- source metadata and one claim;
- one research project with two source memberships;
- one source relationship;
- one saved search.

The test creates a Recovery Bundle v1, verifies it, restores it into a database path that did not exist, initializes the restored database, and checks representative content, snapshots, claims, project membership, relationship state, saved search state, schema version, and search behavior. Additional tests require tampered bundle data and manifest shape changes to fail verification and require existing/symlinked restore targets to fail closed.

This is automated Development evidence for the application-owned recovery primitive. It does not establish Everkeep service orchestration, scheduled backup policy, retention/deletion policy, encrypted off-device custody, target-host operational recovery, disaster recovery, or Release Candidate/Stable acceptance.

## Security and privacy

A recovery bundle contains the same research state as the source database and can expose sensitive research topics, project questions, source history, notes, claims, and relationships. Store bundles only in an appropriately protected location. Do not commit them to Git, publish them as CI artifacts containing private data, or treat the SHA-256 manifest as encryption or authorization.

The current format intentionally contains no credentials and no reusable secrets. Integrity verification detects accidental or unauthorized byte changes after bundle creation, but it is not a signature and does not prove who created or authorized the backup.

## Everkeep boundary

Recovery Bundle v1 strengthens the Research Library's local durability and clean-environment recovery evidence, but GoreeCloud Everkeep remains `applicable-migration-required` in the Platform Contract. Everkeep integration is not complete until approved orchestration, policy, protected storage, recovery evidence, operational acceptance, and other applicable continuity requirements are implemented and verified.
