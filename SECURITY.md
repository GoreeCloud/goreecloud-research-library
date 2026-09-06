# Security Policy

GoreeCloud Research Library is currently a **Development** application and is not approved for direct Internet-facing deployment.

## Security-sensitive areas

Remote-source ingestion is the highest-risk current capability. The application fetches and parses content controlled by arbitrary public web servers. Current mitigations include:

- HTTP(S)-only URL policy;
- embedded-credential rejection;
- public-address validation with private/loopback/link-local/reserved destinations blocked by default;
- validation of each redirect destination;
- fetch timeout, redirect, size, and media-type limits;
- robots.txt checks by default;
- no fetched JavaScript execution;
- extracted-text storage rather than raw executable page HTML;
- bounded PDF page processing;
- loopback-first deployment guidance.

These controls reduce risk but do not make the MVP production-safe. DNS rebinding, parser vulnerabilities, decompression/parser resource abuse, hostile documents, egress control, authentication, authorization, rate limiting, audit policy, and platform-system acceptance still require additional hardening.

## Deployment requirements

Until GoreeCloud Identity and the required platform security/privacy controls are integrated and accepted:

- bind the application only to loopback or place it behind an approved authenticated private boundary;
- do not expose `/api/v1/capture` to untrusted users;
- keep `GORECLOUD_RESEARCH_ALLOW_PRIVATE_FETCH=false` unless a controlled private-source workflow explicitly requires otherwise;
- apply network-level egress restrictions in higher-risk deployments;
- protect the SQLite database and exports because research context can be sensitive;
- do not store reusable credentials in source URLs, notes, repository files, or ordinary exports.

## Reporting vulnerabilities

Do not publish credentials, private research content, exploit payloads containing sensitive information, or other protected evidence in a public issue. Use GitHub private vulnerability reporting/security advisories for this repository when available, or an established private GoreeCloud security channel.

Public non-sensitive hardening ideas may be filed as ordinary issues.
