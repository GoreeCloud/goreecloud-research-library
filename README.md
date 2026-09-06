# GoreeCloud Research Library

GoreeCloud Research Library is a native GoreeCloud research workspace for collecting public web sources into a traceable, searchable local library. Paste a URL and the application fetches the public resource, extracts useful text and metadata, records access time and a SHA-256 content identity, preserves extracted-text snapshots, and gives the source an evidence record that can be reviewed later.

**Lifecycle:** Development (`0.2.0-dev`). This repository is not Stable and is not approved for Internet-facing or production use.

## What is implemented now

- Public HTTP(S) URL capture with redirect limits, timeouts, response-size limits, credential-in-URL rejection, default public-address validation, and robots.txt handling.
- Extraction for HTML/XHTML, PDF, plain text, Markdown, JSON, XML, RSS, and Atom resources.
- Metadata extraction for title, author, publisher/site, publication date, and canonical URL when available.
- Local SQLite source library with extracted-text snapshots, SHA-256 change detection, and schema-migration records.
- Search across captured title, content, tags, author, and publisher; SQLite FTS5 is used when available, with a fallback search path.
- Saved searches for repeatable research discovery.
- GoreeCloud research/evidence classifications for source records and individual statements.
- Research notes, tags, confidence levels, and evidence/limitation notes.
- Research projects with a question, description, tags, and explicit source membership.
- Source-to-source evidence relationships: supports, contradicts, duplicates, updates, references, and contextualizes.
- Relationship strength and researcher-authored evidence/limitation notes.
- Project-level relationship summary with a visible contradiction warning when explicit conflicts are recorded.
- Readable citation, BibTeX, CSL JSON, and RIS citation helpers.
- JSON, CSV, CSL JSON, and RIS exports.
- Application-owned Recovery Bundle v1 creation/verification and clean-target schema-v2 restore with SQLite integrity, foreign-key, SHA-256, size, table-count, and symlink/no-overwrite checks.
- Automated clean-environment recovery drill for representative schema-v2 source, snapshot, claim, project, relationship, saved-search, and search state.
- Human UI plus `/api/v1` source/project read APIs, capture API, and `/healthz` health signal.
- Loopback-first Docker Compose deployment with a persistent data volume.
- Automated tests, GitHub Actions CI, and GoreeCloud Platform Contract validation.

## Quick start

Requires Python 3.12 or later.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --host 127.0.0.1 --port 8088
```

Open `http://127.0.0.1:8088`.

Docker Compose is also provided:

```bash
docker compose up --build
```

The Compose configuration publishes only to `127.0.0.1:8088` by default.

## Research workflow

1. Capture a public source URL.
2. Review extracted metadata and source classification.
3. Record research statements with explicit classification, confidence, and limitations.
4. Create a research project for a bounded question, investigation, or decision.
5. Add related captured sources to the project.
6. Record only evidence-supported source relationships such as `supports` or `contradicts`.
7. Use the relationship summary as a navigation aid, not an automatic truth verdict.
8. Save useful library searches for repeatable discovery.
9. Export the library or citation data when needed.

A relationship is researcher-authored metadata. GoreeCloud Research Library does not automatically promote a source, relationship, summary, or AI-generated statement into a Verified Fact.

## Capture model

A normal capture records the final fetched URL, canonical URL metadata when present, source metadata, access/fetch time, HTTP/content type, cleaned extracted text, excerpt, SHA-256 content identity, a new snapshot when the extracted-text hash changes, and user-controlled research classification/notes.

The application stores extracted research text rather than executable page HTML. It does not intentionally bypass logins, paywalls, anti-bot controls, or access restrictions.

## Local recovery workflow

Recovery Bundle v1 creates a consistent schema-v2 SQLite backup plus a strict integrity manifest. It is suitable for Development backup verification and clean-target recovery testing; it does not replace Everkeep or establish production recovery acceptance.

Create a new bundle directory:

```bash
python -m app.recovery backup --output /protected/path/research-library-backup
```

Verify it later:

```bash
python -m app.recovery verify --bundle /protected/path/research-library-backup
```

Restore only into a database path that does not already exist:

```bash
python -m app.recovery restore \
  --bundle /protected/path/research-library-backup \
  --target-database /clean/path/research-library.sqlite3
```

The restore command deliberately refuses to overwrite an existing database. See [docs/recovery-bundle.md](docs/recovery-bundle.md) for the complete contract, security boundary, and Everkeep limitation.

## Security boundary

The Development application has **no user authentication or GoreeCloud Identity integration yet**. Keep it loopback-only or otherwise behind an approved authenticated boundary. Public-source fetching is an outbound network capability and must be treated as security-sensitive.

The default configuration blocks non-public destinations, enforces fetch limits, and respects robots.txt. DNS rebinding, parser complexity, hostile documents, deployment egress policy, abuse controls, and platform-system acceptance remain open before Internet-facing production use. See [SECURITY.md](SECURITY.md) and [docs/security-model.md](docs/security-model.md).

Research databases and recovery bundles can contain sensitive research context. Recovery manifest hashes provide integrity checking, not encryption, creator authentication, or authorization.

## GoreeCloud platform status

The repository declares its current state in [`goreecloud.platform.yaml`](goreecloud.platform.yaml). It remains intentionally **nonconformant / Development** while mandatory platform integrations and acceptance work remain incomplete.

- Glaze UI: Development interface targets current Stable 1.1.0; formal contract/rendered/accessibility acceptance is pending.
- Wardveil Security: not yet integrated or accepted.
- Privacy Shield: not yet integrated or accepted.
- Everkeep: Recovery Bundle v1, export, migration, local durability, and automated clean-target recovery evidence exist; Everkeep orchestration, protected-storage policy, operational restore acceptance, and broader continuity acceptance remain incomplete.
- GoreeCloud Mesh: planned; no capability/event integration yet.
- GoreeCloud Identity: required before multi-user or Internet-facing authenticated use.
- GoreeCloud Manager: future launch/discovery/status integration; no integration is claimed.

No missing integration is represented as complete.

## Documentation

- [SPECIFICATIONS.md](SPECIFICATIONS.md) — product and implementation specification
- [FEATURES.md](FEATURES.md) — implemented and planned capability matrix
- [BENEFITS.md](BENEFITS.md) — supportable product value
- [COMPETITIVE-OBJECTIVES.md](COMPETITIVE-OBJECTIVES.md) — benchmark and differentiation objectives
- [BRANDING.md](BRANDING.md) — app branding and Glaze UI requirements
- [USER-MANUAL.md](USER-MANUAL.md) — current user workflow
- [SECURITY.md](SECURITY.md) — vulnerability and deployment-safety guidance
- [docs/architecture.md](docs/architecture.md) — component and data-flow architecture
- [docs/research-model.md](docs/research-model.md) — evidence and provenance model
- [docs/deployment.md](docs/deployment.md) — local/Compose operation and recovery
- [docs/recovery-bundle.md](docs/recovery-bundle.md) — application-owned Recovery Bundle v1 contract and clean-target restore workflow
- [docs/security-model.md](docs/security-model.md) — fetch and deployment threat model

## License

AGPL-3.0-only. See [LICENSE](LICENSE).
