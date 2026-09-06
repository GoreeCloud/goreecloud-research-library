# GoreeCloud Research Library — Features

Status legend: **Implemented**, **Partial**, **Planned**, or **Not approved/implemented**.

| Capability | Status | Current evidence / boundary |
|---|---|---|
| Paste a public URL and capture a source | Implemented | `app/fetcher.py`, `/capture`, `/api/v1/capture` |
| HTML readable-text extraction | Implemented | `app/extractors.py` |
| PDF text extraction | Implemented | pypdf-backed bounded extraction |
| Plain text / Markdown / JSON / XML / feed capture | Implemented | text extraction path |
| Metadata extraction | Implemented | title, author, publisher/site, date, canonical URL where exposed |
| SSRF-oriented destination validation | Implemented, Development | rejects non-public resolved IPs by default; production egress hardening remains open |
| Redirect, timeout, size, MIME controls | Implemented | fetch limits in `app/fetcher.py` |
| robots.txt respect | Implemented | default enabled; configurable for controlled Development use |
| Extracted-content hash and change detection | Implemented | SHA-256 |
| Extracted-text snapshots | Implemented | unique by source + content hash |
| Research evidence classification | Implemented | source and statement classifications |
| Research notes and tags | Implemented | source metadata form |
| Individual claims/statements | Implemented | classification, confidence, limitation/evidence note |
| Full-text search | Implemented | FTS5 when available, fallback search otherwise |
| Markdown citation helper | Implemented | simple reusable citation, not a complete style engine |
| BibTeX helper | Implemented | lightweight `@online` export |
| JSON export | Implemented | source + claims + snapshots |
| CSV export | Implemented | source-level export |
| Health endpoint | Implemented | `/healthz` |
| Server-rendered responsive UI | Implemented | Development UI |
| Glaze UI Stable contract conformance | Partial | visual alignment only; governed validation pending |
| GoreeCloud Identity | Planned | required before multi-user/public authenticated deployment |
| Privacy Shield | Planned | privacy contract integration pending |
| Wardveil Security | Planned | security contract integration pending |
| Everkeep | Partial | portable data exists; contract integration and restore acceptance pending |
| GoreeCloud Mesh | Planned | no capability/event integration yet |
| GoreeCloud Manager | Planned | no Manager visibility/launch integration yet |
| Collections / research projects | Planned | normalized project model not yet implemented |
| Saved searches / smart collections | Planned | not implemented |
| Source relationship graph | Planned | not implemented |
| Source conflict and triangulation UI | Planned | classification primitives exist; dedicated workflow not yet implemented |
| Browser-rendered dynamic-page capture | Planned | current fetcher does not execute page JavaScript |
| Browser extension / share-sheet capture | Planned | not implemented |
| CSL / Zotero-compatible citation workflow | Planned | not implemented |
| Local AI summarization and Q&A | Planned | no AI calls are made by the MVP |
| OCR and image research extraction | Not approved/implemented | requires separate threat/privacy/performance design |
| Authenticated/paywall bypass | Not approved/implemented | intentionally outside product behavior |
