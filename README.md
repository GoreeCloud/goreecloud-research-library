# GoreeCloud Research Library

GoreeCloud Research Library is a native GoreeCloud research workspace for collecting public web sources into a traceable, searchable local library. Paste a URL and the application fetches the public resource, extracts useful text and metadata, records access time and a SHA-256 content identity, preserves extracted-text snapshots, and gives the source an evidence record that can be reviewed later.

**Lifecycle:** Development / initial MVP (`0.1.0-dev`). This repository is not Stable and is not approved for Internet-facing or production use.

## What is implemented now

- Public HTTP(S) URL capture with redirect limits, timeouts, response-size limits, and credential-in-URL rejection.
- Default SSRF guard that rejects private, loopback, link-local, reserved, and otherwise non-public resolved addresses.
- `robots.txt` checking enabled by default.
- Extraction for HTML/XHTML, PDF, plain text, Markdown, JSON, XML, RSS, and Atom resources.
- HTML metadata extraction for title, author, publisher/site, publication date, and canonical URL when available.
- Local SQLite source library with preserved extracted-text snapshots and SHA-256 change detection.
- Search across captured title, content, tags, author, and publisher; SQLite FTS5 is used when available, with a fallback search path.
- GoreeCloud research/evidence classifications for source records and individual statements.
- Research notes, tags, confidence levels, and evidence/limitation notes.
- Markdown-style and BibTeX citation helpers.
- JSON and CSV export.
- Human UI plus a small `/api/v1` capture/read API and `/healthz` health signal.
- Loopback-first Docker Compose deployment with a persistent data volume.
- Automated tests and GitHub Actions CI.

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

## Capture model

A normal capture records:

1. final fetched URL and canonical URL metadata when present;
2. title, author, publisher/organization, publication/update date when extractable;
3. access/fetch time, HTTP status, content type, and source type;
4. cleaned extracted text and excerpt;
5. SHA-256 content identity;
6. a snapshot only when a new extracted-text hash is observed;
7. source classification, evidence status, tags, notes, and optional research statements.

The application stores extracted research text rather than executable page HTML. It does not intentionally bypass logins, paywalls, anti-bot controls, or access restrictions.

## Evidence classifications

The research ledger supports: Verified Fact, Source-Reported / Vendor Claim, Direct Observation, Test Result, Inference, Recommendation, Decision, Planned Configuration, Assumption, Estimate, Historical, and Unknown / Verification Required.

Source-origin classes include GoreeCloud authoritative, external primary, independent technical, community evidence, retail/availability, and unknown/verification required.

## Security boundary

The Development MVP has **no user authentication or GoreeCloud Identity integration yet**. Keep it loopback-only or otherwise behind an approved authenticated boundary. Public-source fetching is an outbound network capability and must be treated as a security-sensitive feature.

The default configuration blocks non-public destinations, enforces fetch limits, and respects robots.txt. DNS rebinding, parser complexity, hostile documents, and deployment egress policy still require further hardening before Internet-facing production acceptance. See [SECURITY.md](SECURITY.md) and [docs/security-model.md](docs/security-model.md).

## GoreeCloud platform status

The repository declares its current state in [`goreecloud.platform.yaml`](goreecloud.platform.yaml). The application is intentionally **nonconformant / Development** while mandatory platform integrations and acceptance work remain incomplete.

- Glaze UI: interface is aligned to the current Stable 1.1 visual principles, but formal contract/rendered acceptance has not been completed.
- Wardveil Security: not yet integrated/accepted.
- Privacy Shield: not yet integrated/accepted.
- Everkeep: export and local durability primitives exist, but Everkeep contract integration and restore acceptance are not complete.
- GoreeCloud Mesh: planned, not implemented.
- GoreeCloud Identity: planned, not implemented.
- GoreeCloud Manager: future visibility/launch integration; not required for the standalone Development MVP.

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
- [docs/security-model.md](docs/security-model.md) — fetch and deployment threat model

## License

AGPL-3.0-only. See [LICENSE](LICENSE).
