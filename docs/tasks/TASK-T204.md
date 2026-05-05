# TASK-T204 — Add Source Domains API Endpoint

## Status

Ready for implementation.

## Goal

Expose Source Intelligence v2 domain aggregation through a backend API endpoint.

## Dependencies

Requires:

```text
TASK-T203 — Source domain aggregation service
```

## Scope

Implement:

```text
GET /audits/{id}/source-domains
auth/ownership guard
source domain DTO serialization
warnings if applicable
task-scoped backend/API tests
```

## Endpoint

```http
GET /audits/{id}/source-domains
```

## Filters

Decision:

```text
No query parameters/filters in this task.
```

Do not implement:

```text
?level=
?model_id=
?provider=
```

Filters are a future separate task.

## Response shape

Return domain groups from aggregation service.

## Tests

Backend/API tests:

```text
unauthenticated rejected
non-owner rejected
owner can access source domains
empty audit returns domains=[]
L2 sources grouped
partial audit sources grouped
invalid URLs do not crash endpoint
OpenRouter gateway metadata included where available
raw provider response not exposed
no filter parameters documented/required
```

## Acceptance criteria

- Source domains endpoint exists.
- Auth/ownership enforced.
- No filters implemented.
- Endpoint returns domain groups using aggregation service.
- Empty/no-source state works.
- No raw provider/source payload exposed.
- Task-scoped backend/API tests pass.
- Touched-file ruff passes.

## Escalate if

- Frontend already requires level/model filters.
- Existing API route already has filter behavior that must be preserved.

## Commands

```bash
pytest <source domain endpoint tests>
ruff check <touched backend files>
```

## Done means

Source-domain endpoint works without optional filters, with clear future extension point.
