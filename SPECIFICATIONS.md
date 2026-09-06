# GoreeCloud Research Library — Specifications

## Document status

- Product: GoreeCloud Research Library
- Repository: `GoreeCloud/goreecloud-research-library`
- Development model: original native GoreeCloud application
- Lifecycle: Development
- Current code version: `0.1.0-dev`
- Current implementation boundary: initial functional MVP
- Production approval: No

## 1. Role and purpose

GoreeCloud Research Library is the first-party research-source collection and evidence workspace for GoreeCloud. Its primary job is to turn a set of links and public resources into durable, searchable research records with enough metadata and provenance to distinguish what was observed, what a source claimed, what changed, and what still requires verification.

The application is not intended to be a general-purpose web crawler, a paywall bypass tool, a credentialed scraper, or a replacement for the original source. The original source URL remains part of every record.

## 2. Intended users

Initial scope is a single authorized GoreeCloud operator or researcher using a trusted local/private deployment. Multi-user sharing, GoreeCloud Identity, role-based access, and controlled collaborative projects are planned but not implemented in the MVP.

## 3. Required capabilities

### 3.1 Source capture

The application must accept a pasted HTTP(S) URL and gather information from publicly reachable resources. The current implementation supports HTML/XHTML, PDF, plain text, Markdown, JSON, XML, RSS, and Atom content types.

A capture records at least the final URL, content type, HTTP status, title when available, cleaned research text, access/fetch time, and content hash. HTML/PDF metadata is captured when the source exposes it.

### 3.2 Provenance and evidence

Every source must retain an access date and source URL. Users must be able to classify a source and record evidence statements using the GoreeCloud research classifications rather than mixing fact, claim, inference, recommendation, and unknown state into one undifferentiated note.

### 3.3 Change history

The application must detect whether newly extracted text differs from the current stored text. A new extracted-text snapshot must be preserved when the content hash changes. Re-fetching an unchanged source must not create duplicate snapshots.

### 3.4 Search and retrieval

Captured sources must be searchable by useful research fields. FTS5 is preferred when available. Search must still work through a fallback path if FTS5 is unavailable in the linked SQLite build.

### 3.5 Portability

The library must provide machine-readable export without a proprietary hosted dependency. The current MVP provides JSON and CSV source export. JSON includes associated claims and snapshots.

## 4. Current architecture

- Runtime: Python 3.12+
- Web framework/API: FastAPI
- Server-rendered UI: Jinja2 templates
- HTTP client: HTTPX
- HTML parser/extractor: Beautiful Soup with GoreeCloud-owned extraction logic
- PDF parser: pypdf as a bounded supporting dependency
- Database: SQLite with WAL mode; FTS5 when available
- Deployment: local Python process or Docker Compose
- Persistent path: `${GORECLOUD_RESEARCH_DATA_DIR}/research-library.sqlite3`

The product behavior, data model, application flow, source handling, evidence workflow, and UI are GoreeCloud-owned. External packages are bounded framework/protocol/parser foundations rather than inherited complete-product implementations.

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

A Snapshot is a preserved extracted-text revision keyed by source and content hash. The MVP intentionally does not preserve raw executable HTML. Future archival modes may store approved immutable source artifacts separately with retention, privacy, copyright, and security controls.

### Claim / research statement

A Claim is a user-recorded research statement associated with a source. Each statement carries a GoreeCloud research classification, confidence level, optional evidence/limitation note, and creation time.

## 7. API

Current Development API:

- `GET /api/v1/sources`
- `GET /api/v1/sources/{id}`
- `POST /api/v1/capture`
- `GET /healthz`
- `GET /export.json`
- `GET /export.csv`

The API is unauthenticated in the MVP and therefore inherits the local/private deployment boundary. It is not an approved public API.

## 8. User interface

The UI uses a GoreeCloud-owned server-rendered interface aligned with the current Stable Glaze UI 1.1 principles: readable work areas use solid surfaces; navigation/search/control chrome may use glazed surfaces; Deep Teal + Soft Amber are subordinate accents; semantic state and accessibility remain higher priority than decoration.

Formal Glaze UI contract validation has not been completed, so Platform Contract status remains nonconformant.

## 9. Platform-system evaluation

### GoreeCloud Manager

Future role: launch/discovery/status visibility and, if justified, sanitized health/operational information. No Manager integration is currently implemented.

### Privacy Shield

Applicable because research records can contain sensitive browsing/research context. Required future capabilities include privacy classification, redaction/export policies, privacy-safe logging, and user-visible privacy controls. Not yet integrated.

### Wardveil Security

Applicable because the application performs outbound fetching and parses hostile content. Required future work includes current Wardveil contract integration, security status evidence, and accepted fetch/parser hardening. Not yet integrated.

### Everkeep

Applicable because the research library is durable user data. The MVP supports deterministic SQLite storage and export; Everkeep-managed backup/restore contract integration and restore validation are still required.

### Glaze UI

Applicable to all visible UI. Current implementation targets Stable 1.1 principles but has not passed governed conformance/rendered acceptance.

### GoreeCloud Mesh

Applicable when research sources, projects, citations, claims, or capability events need cross-application discovery and coordination. Planned; not implemented.

### GoreeCloud Identity

Required before multi-user or Internet-facing authenticated use. Planned; not implemented.

## 10. Privacy requirements

- No application telemetry is required by the MVP.
- No research content is sent to third-party AI or hosted analysis services.
- No external trackers are included in the UI.
- Source fetching necessarily discloses the deployment's outbound IP and user-agent to the source site.
- Stored research context may itself be sensitive and must be protected at the deployment boundary.
- Logs must not include captured page bodies or reusable credentials.

## 11. Backup and recovery

Before the library becomes important or production-dependent, the SQLite database and any future durable artifact store must be included in an approved backup system. The present portable recovery path is database-file backup plus JSON export. A clean-environment restore test and Everkeep acceptance are required before Stable.

## 12. Explicitly excluded from the current MVP

- authentication and multi-user authorization;
- JavaScript/browser rendering for dynamic pages;
- authenticated/paywalled source capture;
- recursive crawling or site-wide spidering;
- browser extension capture;
- OCR;
- automatic AI-generated summaries or claim verification;
- collaborative research projects/workspaces;
- full citation-style engine (APA/MLA/Chicago/CSL);
- immutable binary artifact preservation;
- GoreeCloud platform-system acceptance.

These may be added through governed development rather than being implied by the first implementation.

## 13. Next development priorities

1. GoreeCloud Identity and authorization model.
2. Wardveil and Privacy Shield contract integrations around fetch, parsing, logging, and research privacy.
3. Everkeep backup/restore orchestration and restore evidence.
4. Glaze UI contract validation against the current Stable release.
5. Research projects/collections, normalized tags, saved searches, and source relationships.
6. Browser-assisted capture for JavaScript-heavy public pages using a sandboxed rendering service.
7. Citation/CSL support and bibliography exports.
8. Source conflict/triangulation workflows and verification status dashboards.
9. Optional local GoreeCloud AI integration for on-device summarization, question answering, entity extraction, and claim assistance with source-grounded citations.
10. GoreeCloud Mesh capabilities/events for cross-application research relationships and discovery.
