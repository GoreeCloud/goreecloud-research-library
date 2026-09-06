# GoreeCloud Research Library — Specifications

## Document status

- Product: GoreeCloud Research Library
- Repository: `GoreeCloud/goreecloud-research-library`
- Development model: original native GoreeCloud application
- Lifecycle: Development
- Current code version: `0.2.0-dev`
- Current implementation boundary: functional local/private research library with projects and evidence relationships
- Production approval: No

## 1. Role and purpose

GoreeCloud Research Library is the first-party research-source collection and evidence workspace for GoreeCloud. Its primary job is to turn links and public resources into durable, searchable research records with enough metadata and provenance to distinguish what was observed, what a source claimed, what changed, how sources relate, and what still requires verification.

The application is not intended to be a general-purpose web crawler, paywall bypass tool, credentialed scraper, or replacement for the original source. The original source URL remains part of every record.

## 2. Intended users

Current scope is a single authorized GoreeCloud operator or researcher using a trusted local/private deployment. Research projects are implemented for organizing one operator's work. Multi-user sharing, GoreeCloud Identity authentication, role-based authorization, and collaborative editing are not implemented.

## 3. Required capabilities

### 3.1 Source capture

The application accepts a pasted HTTP(S) URL and gathers information from publicly reachable resources. The current implementation supports HTML/XHTML, PDF, plain text, Markdown, JSON, XML, RSS, and Atom content types.

A capture records at least the final URL, content type, HTTP status, title when available, cleaned research text, access/fetch time, and content hash. HTML/PDF metadata is captured when the source exposes it.

### 3.2 Provenance and evidence

Every source retains an access date and source URL. Users can classify sources and record evidence statements using GoreeCloud research classifications rather than mixing fact, claim, inference, recommendation, and unknown state into one undifferentiated note.

Source and statement classification remain researcher-controlled metadata. Successful capture does not make a statement verified.

### 3.3 Change history

The application detects whether newly extracted text differs from the current stored text. A new extracted-text snapshot is preserved when the content hash changes. Re-fetching an unchanged source does not create duplicate snapshots.

### 3.4 Search and saved discovery

Captured sources are searchable by useful research fields. FTS5 is preferred when available; fallback search remains available if FTS5 is unavailable. A named saved-search record can preserve a query and optional source-classification filter for repeatable discovery.

### 3.5 Research projects

A Project is a bounded research workspace identified by a name, research question, description, tags, status, and source memberships. A source may belong to multiple projects. A project membership may carry a project-specific note describing why the source belongs in that investigation.

Projects do not create a second copy of a source. Source identity remains global to the local Research Library database.

### 3.6 Source relationships and triangulation

The Development application supports explicit researcher-authored relationships between two different captured sources:

- `supports` — one source provides corroborating evidence;
- `contradicts` — material evidence conflicts;
- `duplicates` — substantially redundant evidence;
- `updates` — later evidence revises or supersedes relevant information;
- `references` — one source explicitly cites or depends on another;
- `contextualizes` — one source adds scope or interpretation without necessarily confirming a claim.

Each relationship includes a strength level and optional evidence/limitation note. Project relationship entry requires both source records to belong to the project. Relationship records are source-global evidence metadata; removing a source from a project removes the project view of the relationship but does not silently delete the underlying relationship.

A project-level summary counts recorded relationship types and displays a visible warning when contradiction relationships exist. This is a research-navigation aid, not an automatic truth or consensus engine.

### 3.7 Citation portability

The library provides:

- readable citation helper;
- BibTeX `@online` helper;
- CSL JSON source and library export;
- RIS source and library export.

These preserve citation metadata and improve interoperability. They do not constitute a complete APA/MLA/Chicago renderer or direct Zotero integration.

### 3.8 Portability

The library provides machine-readable export without a proprietary hosted dependency. JSON export v2 includes sources, claims, snapshots, project memberships, source relationships, projects, and saved searches. CSV remains a source-level tabular export. CSL JSON and RIS provide citation-oriented portability.

## 4. Current architecture

- Runtime: Python 3.12+
- Web framework/API: FastAPI
- Server-rendered UI: Jinja2 templates
- HTTP client: HTTPX
- HTML parser/extractor: Beautiful Soup with GoreeCloud-owned extraction logic
- PDF parser: pypdf as a bounded supporting dependency
- Database: SQLite with WAL mode; FTS5 when available
- Local schema migrations: application-owned migration registry; current schema version 2
- Deployment: local Python process or Docker Compose
- Persistent path: `${GORECLOUD_RESEARCH_DATA_DIR}/research-library.sqlite3`

The product behavior, data model, application flow, source handling, evidence workflow, project model, source relationship semantics, and UI are GoreeCloud-owned. External packages are bounded framework/protocol/parser foundations rather than inherited complete-product implementations.

## 5. Capture security requirements

The current fetch boundary must:

- accept only HTTP and HTTPS;
- reject embedded URL credentials;
- normalize and validate redirect destinations;
- resolve the target and reject non-public addresses by default;
- impose request timeouts and a redirect ceiling;
- impose a maximum downloaded response size;
- restrict accepted content types;
- avoid executing fetched JavaScript or HTML;
- store extracted text instead of executable raw page markup;
- respect robots.txt by default;
- never attempt to defeat authentication, paywalls, or access controls.

`GORECLOUD_RESEARCH_ALLOW_PRIVATE_FETCH=true` is an explicit Development override for trusted private-source research and weakens the default SSRF boundary. It must not be enabled casually on an Internet-accessible deployment.

## 6. Data model

### Source

A Source is the current research record for one final fetched URL. It contains source metadata, classification, notes, current extracted content, content identity, capture metadata, and update/change timestamps.

### Snapshot

A Snapshot is a preserved extracted-text revision keyed by source and content hash. The application intentionally does not preserve executable raw HTML. Future archival modes may store approved immutable source artifacts separately with retention, privacy, copyright, and security controls.

### Claim / research statement

A Claim is a user-recorded research statement associated with a source. Each statement carries a GoreeCloud research classification, confidence level, optional evidence/limitation note, and creation time.

### Project

A Project stores a bounded research question/investigation with name, question, description, status, tags, and timestamps.

### Project Source

A Project Source membership links one global Source to one Project with an optional project-specific note and membership timestamp.

### Source Relationship

A Source Relationship links two different Source records with a controlled relationship type, strength, note, and creation time. Duplicate relationship triples are prevented by the local schema.

### Saved Search

A Saved Search stores a reusable name, text query, optional source classification, and timestamps.

### Schema Migration

A Schema Migration records the applied local database schema version, time, and description so Development upgrades remain explicit rather than relying only on implicit table creation.

## 7. API

Current Development API and export surfaces include:

- `GET /api/v1/sources`
- `GET /api/v1/sources/{id}`
- `POST /api/v1/capture`
- `GET /api/v1/projects`
- `GET /api/v1/projects/{id}`
- `GET /healthz`
- `GET /export.json`
- `GET /export.csv`
- `GET /export.csl.json`
- `GET /export.ris`

The API is unauthenticated and therefore inherits the local/private deployment boundary. It is not an approved public API. Project mutation routes are presently server-rendered form workflows rather than a declared public REST write contract.

## 8. User interface

The UI uses a GoreeCloud-owned server-rendered interface aligned with current Stable Glaze UI 1.1.0 principles: readable work areas use solid surfaces; navigation/search/control chrome may use glazed surfaces; Deep Teal + Soft Amber remain subordinate accents; semantic state and accessibility remain higher priority than decoration.

The interface includes library capture/search, saved-search management, source detail/evidence ledger, projects, project source membership, relationship entry and review, contradiction warning, capture history, and citation helpers.

Formal rendered Glaze UI/accessibility acceptance has not been completed, so Platform Contract status remains nonconformant.

## 9. Platform-system evaluation

### GoreeCloud Manager

Future role: launch/discovery/status visibility and, if justified, sanitized health/operational information. No Manager integration is implemented.

### Privacy Shield

Applicable because research records, project membership, saved searches, and relationship notes may expose sensitive research context. Required future capabilities include privacy classification, minimization, deletion/retention controls, redaction/export policies, privacy-safe logging, and user-visible privacy controls. Not yet integrated.

### Wardveil Security

Applicable because the application performs outbound fetching and parses hostile content. Required future work includes current Wardveil contract integration, security status evidence, hostile-document/parser acceptance, abuse controls, and hardened network egress. Not yet integrated.

### Everkeep

Applicable because the research library is durable user data. SQLite storage, schema migration records, and JSON/CSV/CSL/RIS exports provide recovery/portability primitives; Everkeep-managed backup/restore contract integration and clean-environment restore validation remain required.

### Glaze UI

Applicable to all visible UI. The current Development implementation targets the live current Stable Glaze UI 1.1.0 authority but has not passed governed rendered/accessibility/downstream acceptance.

### GoreeCloud Mesh

Applicable when research sources, projects, citations, claims, or capability events need cross-application discovery and coordination. Planned; not implemented.

### GoreeCloud Identity

Required before multi-user or Internet-facing authenticated use. Planned; not implemented.

## 10. Privacy requirements

- No application telemetry is required by the Development implementation.
- No research content is sent to third-party AI or hosted analysis services.
- No external trackers are included in the UI.
- Source fetching necessarily discloses the deployment's outbound IP and user-agent to the source site.
- Stored research context, saved searches, project questions, notes, and relationship notes may themselves be sensitive and must be protected at the deployment boundary.
- Logs must not include captured page bodies or reusable credentials.

## 11. Backup, migration, and recovery

The SQLite database and any future durable artifact store must be included in an approved backup system before the library becomes production-dependent. The present portable recovery path is database-file backup plus exported data.

Schema version 2 is applied additively and records migration state. Before any incompatible future schema change, backup/rollback expectations must be defined and tested. A clean-environment restore test covering sources, snapshots, claims, projects, memberships, saved searches, relationships, search, and export plus Everkeep acceptance is required before Stable.

## 12. Explicitly excluded from the current Development scope

- GoreeCloud Identity authentication and multi-user authorization;
- collaborative multi-user editing/conflict resolution;
- JavaScript/browser rendering for dynamic pages;
- authenticated/paywalled source capture or access-control bypass;
- recursive crawling or site-wide spidering;
- browser extension/share-sheet capture;
- OCR/image extraction;
- automatic AI-generated truth or claim verification;
- complete citation-style rendering engine;
- direct Zotero account/API synchronization;
- immutable binary artifact preservation;
- production/public API authorization;
- GoreeCloud platform-system acceptance and Stable qualification.

## 13. Next development priorities

1. GoreeCloud Identity authentication and authorization before non-loopback/multi-user use.
2. Wardveil Security and Privacy Shield integrations around fetching, parsing, logging, retention, deletion, export, and research privacy.
3. Everkeep backup/restore orchestration and clean-environment restore evidence covering schema version 2 state.
4. Governed rendered/accessibility validation against current Stable Glaze UI 1.1.0.
5. Stronger hostile-content isolation, outbound network egress controls, rate/abuse controls, and fetch auditability.
6. Sandboxed browser-assisted capture for JavaScript-heavy public pages without bypassing authentication or access controls.
7. More complete CSL/style rendering and optional standards-based reference-manager interoperability.
8. Optional local GoreeCloud AI for source-grounded summaries, question answering, entity extraction, comparison assistance, and claim drafting with explicit citations; generated output must never silently become authoritative fact.
9. GoreeCloud Mesh capabilities/events where cross-application research relationships and discovery materially benefit.
10. GoreeCloud Manager launch/discovery/status integration when operationally useful.
11. Production deployment, recovery, rollback, performance, accessibility, and Stable acceptance gates.
