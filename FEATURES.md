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
| Additive local schema-migration tracking | Implemented, Development | `schema_migrations`, current schema version 2 |
| Research evidence classification | Implemented | source and statement classifications |
| Research notes and tags | Implemented | source metadata form |
| Individual claims/statements | Implemented | classification, confidence, limitation/evidence note |
| Full-text search | Implemented | FTS5 when available, fallback search otherwise |
| Saved searches / smart discovery | Implemented | named repeatable query + source-classification filters |
| Collections / research projects | Implemented, Development | project question, description, tags, source membership, project-specific notes |
| Source relationship graph | Implemented, Development | supports, contradicts, duplicates, updates, references, contextualizes |
| Source conflict and triangulation UI | Implemented, Development | project relationship summary plus explicit contradiction warning; relationships remain researcher-authored metadata |
| Markdown citation helper | Implemented | simple reusable citation, not a complete style engine |
| BibTeX helper | Implemented | lightweight `@online` export |
| CSL JSON citation portability | Implemented, Development | source-level and library export; not a complete citation-style renderer |
| RIS citation portability | Implemented, Development | source-level and library export |
| JSON export | Implemented | export v2 contains sources, claims, snapshots, projects, memberships, relationships, and saved searches |
| CSV export | Implemented | source-level export |
| Recovery Bundle v1 creation | Implemented, Development | `app/recovery.py` uses SQLite backup API and emits strict schema-v2 integrity manifest; local primitive only |
| Recovery Bundle v1 verification | Implemented, Development | SHA-256/size/schema/table-count checks plus SQLite integrity/foreign-key checks and symlink rejection |
| Clean-target recovery drill | Implemented, Development | `tests/test_recovery.py` verifies representative schema-v2 state round trip and restored search; not Everkeep/platform/production acceptance |
| Existing-database replacement/rollback orchestration | Planned | clean-target restore deliberately refuses overwrite; governed migration/rollback workflow remains separate |
| Health endpoint | Implemented | `/healthz`, includes schema version and FTS state |
| Server-rendered responsive UI | Implemented | Development UI |
| Development source/project API | Implemented | `/api/v1/sources`, `/api/v1/projects`, capture endpoint |
| GoreeCloud Platform Contract validation | Implemented for Development manifest validation | reusable canonical workflow; current manifest intentionally remains nonconformant while platform integrations are incomplete |
| Glaze UI Stable contract conformance | Partial | current Stable 1.1.0 alignment target; governed rendered/accessibility acceptance pending |
| GoreeCloud Identity | Planned | required before multi-user/public authenticated deployment |
| Privacy Shield | Planned | privacy contract integration pending |
| Wardveil Security | Planned | security contract integration pending |
| Everkeep | Partial | local recovery bundle, portable data, migration records, and automated clean-target drill exist; Everkeep orchestration/policy/operational acceptance remain pending |
| GoreeCloud Mesh | Planned | no capability/event integration yet |
| GoreeCloud Manager | Planned | no Manager visibility/launch integration yet |
| Browser-rendered dynamic-page capture | Planned | current fetcher does not execute page JavaScript |
| Browser extension / share-sheet capture | Planned | not implemented |
| Full CSL style engine / direct Zotero workflow | Partial / Planned | CSL JSON and RIS portability implemented; full style rendering and direct integration not implemented |
| Local AI summarization and Q&A | Planned | no AI calls are made by the Development application; future output must remain source-grounded and citation-linked |
| OCR and image research extraction | Not approved/implemented | requires separate threat/privacy/performance design |
| Authenticated/paywall bypass | Not approved/implemented | intentionally outside product behavior |
