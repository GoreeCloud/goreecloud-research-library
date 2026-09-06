# GoreeCloud Research Library — User Manual

**Applies to:** Development MVP `0.1.0-dev`

## 1. Start the application

For local development:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --host 127.0.0.1 --port 8088
```

Then open `http://127.0.0.1:8088`.

Do not expose the current MVP directly to the Internet. It does not yet have GoreeCloud Identity or an application authorization layer.

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

Statements remain linked to the source record.

## 6. Refresh a source

Use **Refresh capture** to fetch the public source again.

- If the extracted text hash is unchanged, the existing snapshot remains the current evidence revision.
- If the extracted text hash changes, a new snapshot is preserved and the source's change time is updated.

This is extracted-text change detection, not a forensic archive of every byte or visual layout of a webpage.

## 7. Search

Use the Library search box to search title, content, author, publisher, URL, and tags. Optionally filter by source classification.

SQLite FTS5 is used where available. A simpler fallback search is used otherwise.

## 8. Citations

The source page includes a readable citation helper and a basic BibTeX `@online` representation. These helpers preserve source details but are not yet a complete APA/MLA/Chicago/CSL citation engine. Verify style requirements before publication.

## 9. Export

Use **Export JSON** for the richest portable export. It includes sources, claims, and snapshots.

Use **Export CSV** for a source-level tabular export.

Keep exports protected if your research topics, notes, or source history are sensitive.

## 10. Private-source override

`GORECLOUD_RESEARCH_ALLOW_PRIVATE_FETCH=true` allows private/local resolved addresses. This is a Development override for trusted environments and weakens the default SSRF defense. Do not enable it on a deployment reachable by untrusted users.

## 11. Current limitations

The MVP does not execute webpage JavaScript, sign into sites, bypass paywalls, crawl entire sites, perform OCR, or automatically summarize/verify content with AI. Those capabilities require separate implementation and safety review.
