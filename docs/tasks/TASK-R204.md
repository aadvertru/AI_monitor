# TASK-R204 — Add Strict Source Domains Placeholder Endpoint

## Status

Ready for implementation.

## Goal

Add a strict placeholder endpoint/DTO for future Source Intelligence v2.

This task must not implement grouping. Real grouping belongs to Phase T.

## Dependencies

Requires:

```text
TASK-R201
auth/ownership audit guard
```

## Scope

Implement:

```text
SourceDomainsResponse DTO
GET /audits/{id}/source-domains endpoint
auth/ownership guard
strict empty placeholder response
task-scoped backend/API tests
```

## Endpoint

```http
GET /audits/{id}/source-domains
```

## Response

Always return placeholder:

```json
{
  "audit_id": 1,
  "domains": [],
  "warnings": []
}
```

Do not implement hostname grouping or any “if easy” grouping in this task.

## Rules

- Requires auth.
- Enforces ownership.
- No source aggregation in this task.
- Existing source endpoints unchanged.
- Frontend can safely consume empty shape.

## Tests

Backend/API tests:

```text
unauthenticated rejected
non-owner rejected
owner receives domains=[]
response includes audit_id
response includes warnings=[]
response stable for L1 audit
response stable for L2 audit with sources
response stable for legacy audit
no raw provider/source payload exposed
```

## Acceptance criteria

- Placeholder endpoint exists.
- Auth/ownership enforced.
- Endpoint always returns stable empty `domains`.
- No grouping implemented.
- Task-scoped backend tests pass.
- Touched-file ruff passes.

## Escalate if

- Existing code already implemented source-domain grouping and removing it would be worse.
- Frontend already depends on non-empty source-domain response.

## Commands

```bash
pytest <source domains placeholder tests>
ruff check <touched backend files>
```

## Done means

A strict, safe, empty source-domains endpoint exists as a stable contract for later Phase T implementation.
