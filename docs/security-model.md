# Security Model

## Current trust boundary

The Development MVP assumes one trusted operator and a loopback/private deployment. It does not yet contain user authentication or authorization. The primary untrusted input is remote content retrieved from user-supplied URLs.

## Threats considered in the MVP

### Server-side request forgery

Controls:

- only HTTP(S) schemes;
- no embedded URL credentials;
- DNS resolution before fetch;
- non-global IPv4/IPv6 destinations rejected by default;
- every redirect destination revalidated;
- explicit Development-only private-fetch override.

Residual risk: a DNS name can theoretically change resolution between policy validation and the network connection. Production deployments should add restrictive network egress policy and current Wardveil controls rather than relying on application checks alone.

### Unbounded downloads and slow endpoints

Controls:

- request timeout;
- redirect ceiling;
- `Content-Length` pre-check when present;
- streaming byte limit when reading the body;
- supported media-type allowlist.

### Active webpage content

Controls:

- no browser engine in the current fetch path;
- fetched JavaScript is never executed;
- script/style/template/form/canvas/SVG content is removed from HTML extraction;
- raw active HTML is not persisted by the MVP.

### Hostile PDFs/parsers

Controls:

- download size ceiling;
- PDF page extraction capped at 200 pages;
- extracted text capped by the configured character limit.

Residual risk: parsing untrusted files can expose parser-library vulnerabilities or CPU/memory abuse. Production acceptance requires dependency review, security testing, runtime containment, and Wardveil integration.

### Sensitive research disclosure

Controls:

- no analytics/tracking dependency;
- no external AI processing;
- exports occur only on direct user request;
- source bodies are not intentionally logged.

Residual risk: the unauthenticated MVP database/UI reveals research to anyone who can reach the service. Keep it behind a trusted boundary until Identity integration is accepted.

### Cross-site scripting

Jinja autoescaping is used for HTML templates. Fetched page content is rendered as escaped text inside a `<pre>` element rather than inserted as trusted HTML. User notes/statements are also rendered through normal autoescaping.

## Production hardening gates

At minimum, Internet-facing or Stable consideration requires:

- GoreeCloud Identity authentication and authorization;
- Wardveil Security integration and accepted ingestion/runtime controls;
- Privacy Shield integration for research-context privacy and safe logging/export behavior;
- Everkeep backup/restore evidence;
- rate limits and abuse controls for capture endpoints;
- network egress restrictions that prevent private/metadata/control-plane access;
- dependency and container vulnerability review;
- parser fuzz/adversarial test coverage appropriate to supported formats;
- CSRF/session controls once authenticated write sessions exist;
- structured security audit events without captured-body leakage;
- validated reverse-proxy/TLS deployment;
- Glaze UI accessibility/rendered acceptance;
- restore testing and incident-response documentation.
