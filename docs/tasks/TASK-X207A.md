# TASK-X207A — Add Repeat Audit Backend Endpoint

## Status

Ready for implementation.

## Goal

Add a backend endpoint that duplicates an audit configuration without copying results.

This is the backend half of Repeat Audit. Frontend action belongs to TASK-X207B.

## Dependencies

Requires:

```text
audit ownership/auth
model_targets support if implemented
seed query storage
```

## Scope

Implement:

```text
POST /audits/{id}/duplicate
auth/ownership guard
config-only audit copy
task-scoped backend/API tests
```

## Endpoint

```http
POST /audits/{id}/duplicate
```

## Duplication rules

Copy:

```text
brand
domain
description
seed queries / seed_query_items
model_targets
user-provided competitors if applicable
audit settings
```

Do not copy:

```text
jobs/runs
raw responses
parsed results
scores
evaluations
source records
provider diagnostics
status terminal state
```

New audit status:

```text
created
```

New audit owner:

```text
current authenticated user
```

## Tests

Backend/API tests:

```text
unauthenticated rejected
non-owner rejected
owner can duplicate audit
new audit has copied config
new audit has copied model_targets
new audit has copied seed queries
new audit status created
new audit has no jobs/runs/results/raw responses/evaluations/sources
source audit unchanged
```

## Acceptance criteria

- Duplicate endpoint exists.
- Auth/ownership enforced.
- New audit copies configuration only.
- No results/raw data copied.
- Task-scoped backend/API tests pass.
- Touched-file ruff passes.

## Escalate if

- Current audit data model cannot distinguish config-owned vs result-owned data.
- Duplicate would require copying shared Brand in unsafe way.

## Commands

```bash
pytest <duplicate audit backend tests>
ruff check <touched backend files>
```

## Done means

Backend can create a clean new audit from an existing audit configuration without copying execution data.
