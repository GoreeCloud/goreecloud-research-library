# Architecture

## Development architecture

```text
Browser / API client
       |
       v
FastAPI + Jinja UI
       |
       +--> capture service --> URL normalization / DNS policy / robots / HTTPX
       |                              |
       |                              v
       |                       public web resource
       |                              |
       |                              v
       |                   HTML / PDF / text extractor
       |                              |
       |                              v
       |                       normalized source record
       |
       +--> SQLite research store
       |       +-- current source records
       |       +-- extracted-text snapshots
       |       +-- claims / evidence statements
       |       +-- research projects + source memberships
       |       +-- source-to-source evidence relationships
       |       +-- saved searches
       |       +-- schema-migration registry
       |       +-- FTS5 search index (when available)
       |
       +--> JSON / CSV / CSL JSON / RIS / citation export
```

## Design choices

### Local-first SQLite

The current Development implementation uses one portable SQLite database to minimize deployment burden and make backup/export straightforward. WAL mode improves local concurrent read behavior. A future authenticated multi-user deployment may require PostgreSQL or another approved database after requirements justify the added operational surface.

### Additive schema migrations

The database records an application-owned schema migration version. Schema version 2 adds projects, project-source membership, source relationships, and saved searches without deleting the initial source/snapshot/claim model. Future incompatible migrations require explicit backup, rollback, and restore validation rather than relying on implicit table creation.

### Server-rendered UI

The application deliberately avoids a JavaScript application framework. FastAPI + Jinja keeps the trusted code surface and build chain small while still supporting a responsive research UI. Client-side enhancement may be added later without making core capture/search/projects/export depend on JavaScript.

### Bounded supporting dependencies

FastAPI, HTTPX, Beautiful Soup, Jinja2, pypdf, and SQLite are technical foundations. The application architecture, data model, evidence model, project/relationship workflows, UI, and product behavior are GoreeCloud-owned rather than inherited from an upstream complete application.

### Extracted-text snapshots instead of raw pages

The application stores normalized text and source metadata rather than arbitrary executable HTML. This reduces stored active-content risk and keeps research indexing compact. It is not equivalent to a forensic web archive; a future immutable-artifact mode must define copyright, retention, privacy, malware, file-type, and backup controls before implementation.

### Source-global identity with project membership

A captured source has one local Source identity. Projects reference that source through membership records rather than duplicating source content. This allows one source to participate in multiple investigations while retaining one provenance/capture history.

Source relationships are also attached to global Source identities. The project route allows a relationship to be entered only when both sources are project members, but the relationship remains durable research metadata if project membership later changes.

## Capture pipeline

1. Normalize the user URL.
2. Permit only `http` or `https`; reject embedded credentials.
3. Resolve the target and reject non-public address ranges unless the explicit Development override is enabled.
4. Check robots policy when enabled.
5. Fetch without automatic redirects.
6. Validate every redirect destination and enforce the redirect ceiling.
7. Enforce response timeout and maximum captured bytes.
8. Accept only supported research content types.
9. Extract normalized content and metadata without executing page scripts.
10. Hash the extracted text with SHA-256.
11. Upsert the current source record.
12. Preserve a new snapshot only when the source/hash pair is new.
13. Refresh the search index.

## Research relationship flow

1. Create a bounded Project with a research question/scope.
2. Link existing Source records into the Project.
3. Select two different Project sources.
4. Record a controlled relationship type, strength, and evidence/limitation note.
5. Preserve the relationship as researcher-authored metadata.
6. Summarize project relationship counts and surface explicit contradiction relationships for review.

No automatic algorithm converts relationship counts into truth or source authority.

## Export architecture

- JSON export v2 is the richest portable application export and includes projects/relationships/saved searches.
- CSV remains source-level tabular data.
- CSL JSON and RIS provide citation-oriented interoperability.
- BibTeX and readable citations are available per source.

Core data access does not require a proprietary hosted platform.

## Data ownership

The SQLite database is application-owned state. External web sources remain external authority for their own content. A capture is evidence of what the application extracted at a specific time; it must not be treated as proof that every statement in the source is true. Project relationships and confidence values are user-authored research metadata rather than external-source authority.

## Planned architecture extensions

- authenticated user/session/authorization layer through GoreeCloud Identity;
- Privacy Shield metadata, retention/deletion/export controls, and privacy policy hooks;
- Wardveil ingestion/security policy, hardened outbound egress, abuse controls, and accepted hostile-content parser controls;
- Everkeep backup/restore orchestration and clean-environment recovery evidence;
- governed Glaze UI 1.1.0 rendered/accessibility acceptance;
- sandboxed browser-rendering worker for public JavaScript-heavy sources without access-control bypass;
- GoreeCloud AI adapter for optional local, source-grounded analysis with explicit citations;
- GoreeCloud Mesh capabilities/events for research relationships and cross-app discovery when materially useful;
- GoreeCloud Manager launch/discovery/status integration when useful;
- optional object storage for explicitly approved binary artifacts.
