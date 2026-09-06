# Changelog

This repository-local changelog records source revisions. Canonical GoreeCloud project change records remain governed by the project documentation system.

## Unreleased — 0.2.0-dev

### Added

- Research projects with research question, description, tags, source membership, and project-specific source notes.
- Explicit researcher-authored source relationships: supports, contradicts, duplicates, updates, references, and contextualizes.
- Relationship strength and evidence/limitation notes.
- Project-level relationship summary and contradiction warning for easier triangulation review.
- Named saved searches for repeatable query and source-classification discovery.
- CSL JSON and RIS citation helpers and library exports.
- JSON export v2 with projects, memberships, source relationships, and saved searches.
- Additive SQLite schema-migration registry; current schema version 2.
- Development source/project API expansion and health schema-version reporting.
- Recovery Bundle v1 with SQLite-backup-API snapshotting, strict SHA-256/size/schema/table-count manifest verification, SQLite integrity and foreign-key checks, symlink rejection, and clean-target no-overwrite restore.
- Automated clean-environment recovery drill covering representative schema-v2 sources, snapshots, claims, projects, memberships, relationships, saved searches, and restored search behavior, plus tamper and overwrite rejection tests.
- Recovery Bundle v1 operator documentation in `docs/recovery-bundle.md`.
- Regression tests for projects, relationships, saved searches, migrations, CSL JSON, and RIS.

### Changed

- Development version advanced to `0.2.0-dev`.
- Source detail now shows project memberships, source relationships, and expanded citation portability.
- Navigation now exposes research projects and citation-oriented exports.
- Repository documentation and Platform Contract declaration synchronized to the 0.2 Development boundary.
- Local continuity evidence now includes an application-owned verified clean-target recovery primitive; this does not promote Everkeep integration status or lifecycle state.

### Boundaries

- Source relationships remain researcher-authored evidence metadata and are not automatic verification or truth claims.
- Recovery Bundle v1 integrity metadata is not encryption, a signature, identity evidence, authorization, off-device custody, or Everkeep service acceptance.
- The application remains local/private Development software without GoreeCloud Identity, Wardveil Security, Privacy Shield, accepted Everkeep orchestration, GoreeCloud Mesh, GoreeCloud Manager, production, or Stable acceptance.

## 0.1.0-dev — Initial functional MVP

### Added

- Initial native GoreeCloud Research Library application architecture.
- Public URL capture and bounded remote-resource ingestion.
- HTML, PDF, text, Markdown, JSON, XML, RSS, and Atom extraction paths.
- Source metadata, SHA-256 change identity, extracted-text snapshots, and SQLite persistence.
- Research source/evidence classifications, claims, confidence, notes, and tags.
- Local full-text/fallback search, citation helpers, JSON/CSV export, UI, API, and health endpoint.
- Initial responsive Glaze UI 1.1-aligned Development interface.
- SSRF-oriented public-destination blocking, robots checking, timeout/redirect/download limits, and no-script extraction model.
- Docker Compose, tests, CI, Platform Contract declaration/validation, and repository governance documentation.
