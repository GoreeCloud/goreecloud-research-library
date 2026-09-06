# Research and Evidence Model

GoreeCloud Research Library is designed to preserve the difference between **a source existing**, **a researcher recording a relationship**, and **a proposition being established as true**.

## Source record

Every captured source should answer:

- What URL was fetched?
- What source URL/canonical URL did the page identify?
- Who authored or published it, if known?
- When was it published or updated, if known?
- When did GoreeCloud access it?
- What content type/source type was observed?
- What extracted text was retained?
- What was the SHA-256 identity of that extracted text?
- What source-origin classification applies?
- What limitations or research notes matter?

Metadata that was not actually observed should remain blank or unknown rather than being invented.

## Source-origin classifications

### GoreeCloud Authoritative

Use for current direct GoreeCloud evidence that controls GoreeCloud state, such as an authoritative source repository, approved canonical project document, validated deployment record, or other direct system-of-record evidence.

### External Primary

Use for first-party documentation, standards, vendor product documentation, official release notes, upstream source, or other direct external authority about the thing being described.

### Independent Technical

Use for technically relevant third-party analysis, testing, journalism, academic work, or other independent evidence.

### Community Evidence

Use for forums, issue discussions, Reddit, community troubleshooting, user reports, and similar experience evidence. Useful for patterns and discovery, but not automatically authoritative.

### Retail / Availability

Use for current price, stock, shipping, condition, marketplace listings, and similar time-sensitive commercial evidence.

### Unknown / Verification Required

Use when provenance or authority has not yet been established.

## Research statement classifications

- **Verified Fact** — supported by sufficient authoritative/direct evidence for the stated scope.
- **Source-Reported / Vendor Claim** — a statement made by a source that has not independently become a verified fact.
- **Direct Observation** — directly observed behavior or state.
- **Test Result** — outcome from a defined test.
- **Inference** — conclusion reasoned from evidence but not directly established by it.
- **Recommendation** — proposed course of action.
- **Decision** — an accepted choice or direction.
- **Planned Configuration** — intended future state, not current state.
- **Assumption** — premise being used without current verification.
- **Estimate** — approximate value or projection.
- **Historical** — past state that should not be treated as current.
- **Unknown / Verification Required** — unresolved state.

## Confidence

Confidence is separate from classification. A statement may be a high-confidence inference and still be an inference. A vendor claim may be accurately captured with high confidence while the underlying product claim remains unverified.

## Research projects

A research project groups existing source records around one bounded question, comparison, decision, or investigation. A project may carry its own question, description, tags, and project-specific notes for each source membership.

Project membership does not change the source's global provenance or classification. The same source can participate in more than one project without duplicating the captured evidence.

## Source relationships

A source relationship is explicit researcher-authored evidence metadata connecting two different source records. Current relationship types are:

- **Supports** — one source provides corroborating evidence for the other source or a proposition under review.
- **Contradicts** — material evidence conflicts.
- **Duplicates** — substantially redundant evidence.
- **Updates** — later evidence revises or supersedes relevant information.
- **References** — one source explicitly cites, links to, or depends on another.
- **Contextualizes** — one source adds scope, background, or interpretation without necessarily confirming the claim.

Each relationship can carry a strength and an evidence/limitation note. Relationship strength expresses the researcher's assessment of that relationship; it does not measure universal truth or authority.

Relationships are stored against global source identities. The project UI restricts relationship entry to sources currently included in that project so a relationship is recorded in a concrete research context. If project membership later changes, the relationship record is preserved as research metadata rather than silently discarded.

## Triangulation and conflicts

The project workspace summarizes explicit relationship counts and raises a visible warning when `contradicts` relationships exist. This is a navigation and review aid only.

When evidence conflicts:

1. preserve each material source independently;
2. classify source authority separately;
3. record the material conflict explicitly with a `contradicts` relationship and evidence note when appropriate;
4. preserve conflicting claims as separate research statements when the proposition itself matters;
5. do not silently collapse disagreement into one asserted fact;
6. use Unknown / Verification Required when evidence is insufficient to resolve the conflict;
7. record a resolution as a separate supported research conclusion rather than rewriting historical evidence.

A majority of supporting relationships does not automatically establish a Verified Fact. Source authority, scope, timeliness, methodology, independence, and direct evidence remain relevant.

## Time sensitivity

Availability, pricing, software versions, policies, release status, and other changing facts should carry access/as-of context. The source record always stores an access time; research statements and relationship notes should preserve time context when it materially affects correctness.

## Saved searches

A saved search preserves a reusable library query and optional source-classification filter. It is a discovery convenience, not a frozen evidence snapshot. Results may change as the library changes.

## Citation portability

Readable, BibTeX, CSL JSON, and RIS representations are metadata exports. They do not add authority to the underlying source or guarantee conformance with every publication-specific citation style.

## AI assistance boundary

The current Development application does not automatically summarize or verify research with AI. Future local GoreeCloud AI integration may assist with source-grounded summarization, comparison, entity extraction, question answering, and drafting research statements only when outputs remain linked to source evidence and visibly distinguished from verified fact. AI-generated output must not silently change source classifications or relationship truth status.

## Sensitive information

Do not place reusable credentials, private keys, tokens, recovery codes, or similar secrets in research records. Research topics, browsing history, project questions, annotations, saved searches, relationship notes, and source collections may themselves be sensitive; protect database files and exports accordingly.
