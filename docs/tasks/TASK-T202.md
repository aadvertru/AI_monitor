# TASK-T202 — Add URL Normalization and Registrable Domain Extraction

## Goal

Add reusable backend utilities for URL normalization and registrable-domain extraction.

These utilities will be used by Source Intelligence v2 domain aggregation.

---

## Scope

Implement only:

```text
URL normalization utility
registrable domain extraction utility
safe invalid URL handling
unit tests
```

Do not implement source aggregation yet.

---

## Files to inspect

Codex should inspect actual project structure first.

Likely relevant areas:

```text
apps/api/
libs/
tests/
source/citation models
provider source normalization
```

Use existing utility/module conventions.

---

## Requirements

### URL normalization

Implement a function equivalent to:

```python
normalize_source_url(url: str) -> NormalizedUrl | None
```

It should:

```text
trim whitespace
parse URL safely
lowercase scheme and host
remove default ports
remove URL fragment
normalize trailing slash consistently
remove selected tracking parameters
reject unsupported schemes
return None or safe error for invalid URLs
```

Supported schemes:

```text
http
https
```

Unsupported schemes should be rejected:

```text
javascript:
data:
file:
ftp:
mailto:
```

### Tracking parameters

Remove common tracking params:

```text
utm_source
utm_medium
utm_campaign
utm_term
utm_content
fbclid
gclid
yclid
```

Keep meaningful non-tracking query params.

### Registrable domain

Implement:

```python
extract_registrable_domain(url_or_host: str) -> str | None
```

Use a Public Suffix List compatible library if already available or easy to add.

Examples:

```text
https://news.bbc.co.uk/article → bbc.co.uk
https://sub.example.com/path → example.com
https://www.wikipedia.org/wiki/X → wikipedia.org
```

If no library is used, document limitations and keep behavior safe.

### Safety

Utilities must not perform network calls.

---

## Tests

Add task-scoped unit tests.

Test:

```text
lowercase scheme/host
remove fragment
remove default ports
preserve path
remove tracking params
preserve meaningful query params
reject unsupported schemes
invalid URL returns None/safe value
bbc.co.uk registrable domain extracted correctly if PSL library used
subdomain grouped to registrable domain
localhost/private IP behavior safe according to source display policy
```

---

## Acceptance criteria

- URL normalization utility exists.
- Registrable domain extraction utility exists.
- Unsupported schemes rejected.
- Tracking params removed.
- No network calls performed.
- Unit tests cover core cases.
- Touched-file ruff passes.

---

## Non-goals

- Do not implement source aggregation service.
- Do not change source API endpoints.
- Do not implement frontend UI.
- Do not fetch URLs.
- Do not validate URL reachability.
- Do not fix unrelated legacy failures.
