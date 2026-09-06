# Research and Evidence Model

GoreeCloud Research Library is designed to preserve the difference between **a source existing** and **a proposition being established as true**.

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

## Time sensitivity

Availability, pricing, software versions, policies, release status, and other changing facts should carry access/as-of context. The source record always stores an access time; research statements should preserve time context in their wording or evidence note when it materially affects correctness.

## Conflicts

The MVP lets the researcher record limitation/conflict notes but does not yet provide a dedicated contradiction graph. Until that feature exists:

1. preserve each material source independently;
2. classify source authority separately;
3. record conflicting statements as separate research statements;
4. do not silently merge disagreement into one asserted fact;
5. use Unknown / Verification Required when evidence is insufficient to resolve the conflict.

## Sensitive information

Do not place reusable credentials, private keys, tokens, recovery codes, or similar secrets in research records. Research topics, browsing history, annotations, and source collections may themselves be sensitive; protect database files and exports accordingly.
