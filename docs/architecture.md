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
       +--> SQLite source store
       |       +-- current source record
       |       +-- extracted-text snapshots
       |       +-- claims / evidence statements
       |       +-- FTS5 search index (when available)
       |
       +--> JSON / CSV / citation export
```

## Design choices

### Local-first SQLite

The first implementation uses one portable SQLite database to minimize deployment burden and make backup/export straightforward. WAL mode improves local concurrent read behavior. A future multi-user deployment may require PostgreSQL or another approved database after requirements justify the added operational surface.

### Server-rendered UI

The MVP deliberately avoids a JavaScript application framework. FastAPI + Jinja keeps the trusted code surface and build chain small while still supporting a responsive research UI. Client-side enhancement may be added later without making core capture/search/export depend on JavaScript.

### Bounded supporting dependencies

FastAPI, HTTPX, Beautiful Soup, Jinja2, pypdf, and SQLite are technical foundations. The application architecture, data model, evidence model, workflows, UI, and product behavior are GoreeCloud-owned rather than inherited from an upstream complete application.

### Extracted-text snapshots instead of raw pages

The MVP stores normalized text and source metadata rather than arbitrary executable HTML. This reduces stored active-content risk and keeps research indexing compact. It is not equivalent to a forensic web archive; a future immutable-artifact mode must define copyright, retention, privacy, malware, file-type, and backup controls before implementation.

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

## Data ownership

The SQLite database is application-owned state. External web sources remain external authority for their own content. A capture is evidence of what the application extracted at a specific time; it must not be treated as proof that every statement in the source is true.

## Planned architecture extensions

- authenticated user/session layer through GoreeCloud Identity;
- project/collection and source-relation tables;
- Privacy Shield metadata and privacy policy hooks;
- Wardveil ingestion/security policy and accepted parser controls;
- Everkeep backup/restore orchestration and evidence;
- sandboxed browser-rendering worker for public JavaScript-heavy sources;
- GoreeCloud AI adapter for optional local, source-grounded analysis;
- GoreeCloud Mesh capabilities/events for research relationships and cross-app discovery;
- optional object storage for explicitly approved binary artifacts.
