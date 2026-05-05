# TASK-Q202 — Add Authenticated Backend Brand Domain Availability Check

## Status

Ready for implementation.

## Goal

Add authenticated backend domain availability checking for brand domains.

This service helps query generation determine whether domain-based analysis is reliable, but it must not block manual audit creation.

## Dependencies

Requires:

```text
TASK-Q201
auth middleware
```

## Scope

Implement:

```text
POST /brand-domain/check
auth requirement
domain normalization
domain validation
SSRF-safe DNS/HTTP availability check
24h cache
task-scoped backend tests
```

## Endpoint

```http
POST /brand-domain/check
```

Requires login. Unauthenticated requests return 401/unauthorized.

## Response

```json
{
  "input": "https://example.com/path",
  "normalized_domain": "example.com",
  "status": "reachable",
  "http_status": 200,
  "checked_at": "2026-01-01T00:00:00Z",
  "query_generation_allowed": true,
  "reason": null,
  "cache_ttl_seconds": 86400
}
```

## Status values

```text
reachable
dns_failed
http_failed
timeout
invalid_domain
blocked_private_network
unknown
```

## Cache policy

Decision:

```text
TTL = 24 hours
cache key = normalized_domain
```

## Query generation policy

Decision:

```text
query_generation_allowed=true only when status=reachable
all other statuses => query_generation_allowed=false
```

No uncertain-status allowance in this task.

## SSRF safety

Reject/block:

```text
localhost
127.0.0.0/8
10.0.0.0/8
172.16.0.0/12
192.168.0.0/16
169.254.0.0/16
::1
fc00::/7
fe80::/10
direct IP literals unless explicitly allowed
redirects to private networks
```

Use short DNS/HTTP timeouts, limit redirects, and do not read large bodies.

## Tests

Backend tests:

```text
unauthenticated rejected
valid reachable domain
invalid domain
protocol/path normalization
DNS failure
HTTP failure
timeout
private IP blocked
localhost blocked
redirect to private IP blocked if redirects supported
cache hit avoids repeated network call
TTL returned as 86400
query_generation_allowed true only for reachable
query_generation_allowed false for all other statuses
response does not include raw HTML/body
no request headers/secrets logged or returned
```

## Acceptance criteria

- Authenticated domain check endpoint exists.
- SSRF protections implemented.
- TTL fixed at 24h.
- query_generation_allowed true only for reachable.
- Cache works.
- No raw response body returned.
- Tests mock DNS/HTTP only.
- Task-scoped backend tests pass.
- Touched-file ruff passes.

## Escalate if

- Auth middleware cannot be applied to this endpoint.
- DNS/HTTP checks cannot be safely mocked in CI.
- SSRF protections require a broader networking utility.

## Commands

```bash
pytest <domain check tests>
ruff check <touched backend files>
```

## Done means

Authenticated domain checks are safe, cached for 24h, and allow query generation only for reachable domains.
