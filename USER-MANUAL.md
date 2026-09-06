# GoreeCloud Research Library — User Manual

**Applies to:** Development `0.2.0-dev`

## 1. Start the application

For local development:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --host 127.0.0.1 --port 8088
```

Then open `http://127.0.0.1:8088`.

Do not expose the current Development application directly to the Internet. It does not yet have GoreeCloud Identity or an application authorization layer.

## 2. Capture a source

1. Copy a public HTTP(S) URL.
2. Paste it into **Source URL**.
3. Select **Capture source**.
4. Wait for the source page to open.

A successful capture records the final fetched URL, metadata available from the source, extracted text, access/fetch time, HTTP/content-type data, and a SHA-256 content identity.

The fetch may refuse a URL if it points to a private/local address, contains embedded credentials, exceeds size/redirect/time limits, returns an unsupported media type, or is disallowed by the site's robots policy.

## 3. Review source metadata

On the source page, review and correct:

- title;
- author;
- publisher/organization;
- publication/update date;
- source classification;
- primary evidence status;
- tags;
- research notes.

Automatic extraction is an aid, not an authority. Metadata from webpages can be missing or incorrect.

## 4. Classify the source

Choose the source-origin class that best describes why the source is being used:

- GoreeCloud Authoritative;
- External Primary;
- Independent Technical;
- Community Evidence;
- Retail / Availability;
- Unknown / Verification Required.

Then select the primary evidence status. Do not mark a vendor statement as Verified Fact simply because it was captured successfully.

## 5. Record research statements

In **Claims and research statements**:

1. write the statement you want to preserve;
2. choose its classification;
3. choose a confidence level;
4. add the supporting evidence, limitation, conflict, or verification note when useful;
5. save the statement.

Statements remain linked to the source record. A statement classification is researcher-authored metadata, not an automatic verification result.

## 6. Refresh a source

Use **Refresh capture** to fetch the public source again.

- If the extracted text hash is unchanged, the existing snapshot remains the current evidence revision.
- If the extracted text hash changes, a new snapshot is preserved and the source's change time is updated.

This is extracted-text change detection, not a forensic archive of every byte or visual layout of a webpage.

## 7. Search and save useful searches

Use the Library search box to search title, content, author, publisher, URL, and tags. Optionally filter by source classification.

SQLite FTS5 is used where available. A simpler fallback search is used otherwise.

To preserve a useful search:

1. run the search and optional source-classification filter;
2. enter a name under **Saved searches**;
3. select **Save current search**.

Selecting a saved-search name later restores its query and classification filter. Use **Remove** to delete a saved-search record. Deleting a saved search does not delete research sources.

## 8. Create a research project

Open **Projects** from the application navigation.

Create a project with:

- a project name;
- an optional research question;
- an optional description/scope;
- optional tags.

A project is a workspace for a bounded question, decision, comparison, or investigation. It does not duplicate source content.

## 9. Add sources to a project

On a project page:

1. choose a previously captured source;
2. optionally enter a project-specific note explaining why the source matters;
3. select **Add source to project**.

You can also add a source to a project from the individual source page.

A source can belong to multiple projects. Removing a source from one project does not delete the source from the Research Library.

## 10. Record source relationships

After a project contains at least two sources, use **Source relationships** to record an evidence-supported relationship between two different sources.

Available relationship types are:

- **Supports** — one source provides corroborating evidence;
- **Contradicts** — material evidence conflicts;
- **Duplicates** — the evidence is substantially redundant;
- **Updates** — later information revises or supersedes relevant information;
- **References** — one source explicitly cites or depends on another;
- **Contextualizes** — one source adds scope or interpretation without necessarily confirming the claim.

Choose a relationship strength and add an evidence/limitation note whenever practical.

Relationships are researcher-authored evidence metadata. They are not automatically inferred truth, consensus, or verification. The project page displays a contradiction warning when one or more explicit `contradicts` relationships are present so disputed evidence is easier to review.

## 11. Citations

The source page provides:

- a readable citation helper;
- BibTeX `@online` output;
- CSL JSON metadata;
- RIS metadata.

These formats improve portability and reference-manager interoperability. They are not yet a complete APA/MLA/Chicago style engine or direct Zotero synchronization. Verify publication-specific style requirements before use.

## 12. Export

Use **Export JSON** for the richest portable library export. Export format v2 includes sources, claims, snapshots, projects, project memberships, source relationships, and saved searches.

Use **Export CSV** for a source-level tabular export.

Use **CSL JSON** or **RIS** for citation-oriented library export.

Keep exports protected if your research topics, project questions, notes, saved searches, relationship notes, or source history are sensitive.

## 13. Schema upgrades and backup

The Development database records local schema migrations. Version `0.2.0-dev` uses schema version 2.

Before upgrading an important library, back up the SQLite database and preserve a current JSON export. Formal Everkeep integration and clean-environment restore acceptance are still required before production or Stable use.

## 14. Private-source override

`GORECLOUD_RESEARCH_ALLOW_PRIVATE_FETCH=true` allows private/local resolved addresses. This is a Development override for trusted environments and weakens the default SSRF defense. Do not enable it on a deployment reachable by untrusted users.

## 15. Current limitations

The Development application does not yet:

- authenticate users or provide multi-user authorization;
- execute webpage JavaScript for dynamic-page capture;
- sign into websites or bypass access controls/paywalls;
- recursively crawl entire sites;
- perform OCR or image research extraction;
- provide collaborative multi-user editing;
- provide a full citation-style renderer or direct reference-manager account sync;
- automatically verify claims or promote AI-generated output to facts;
- complete Wardveil Security, Privacy Shield, Everkeep, GoreeCloud Mesh, GoreeCloud Manager, or GoreeCloud Identity integration/acceptance;
- qualify as production-ready or Stable.

Future local GoreeCloud AI assistance may summarize or compare captured material only through a separately governed, source-grounded workflow with explicit citations and user-visible uncertainty.
