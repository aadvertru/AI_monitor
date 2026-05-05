# TASK-Y208 — Add Retry Failed Runs Backend

## Goal

Add backend support for retrying failed/skipped audit runs without duplicating successful runs.

---

## Scope

Implement:

```text
retry failed endpoint
failed/skipped run selection
new retry job creation
result supersede/history policy
task-scoped backend tests
```

---

## Endpoint

```http
POST /audits/{id}/retry-failed
```

Response:

```json
{
  "audit_id": 1,
  "retry_run_count": 3,
  "job_id": "job-456",
  "status": "running"
}
```

---

## Rules

- Requires auth/ownership.
- Only failed/skipped/cancelled runs are retried.
- Successful runs are not duplicated.
- Retried runs should preserve target/query identity.
- Previous failed diagnostics may remain as history or be superseded according to project convention.
- No raw provider data exposed.

---

## Tests

Backend/API tests:

```text
owner can retry failed runs
non-owner rejected
completed successful runs not retried
failed runs retried
skipped/cancelled runs retried if policy allows
new job created
target/query identity preserved
no duplicate successful results
provider diagnostics safe
```

---

## Acceptance criteria

- Retry failed endpoint exists.
- Auth/ownership enforced.
- Only failed/skipped runs retried.
- Successful runs not duplicated.
- Retry job created.
- Task-scoped backend tests pass.
- Touched-file ruff passes.

---

## Non-goals

- Do not implement frontend retry button.
- Do not implement retry all successful runs.
- Do not change scoring/parser.
- Do not fix unrelated bugs.
