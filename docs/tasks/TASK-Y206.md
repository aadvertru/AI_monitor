# TASK-Y206 — Add Audit Progress API

## Goal

Add an API endpoint that exposes audit execution progress for UI polling.

---

## Scope

Implement:

```text
progress DTO
GET /audits/{id}/progress endpoint
run/job aggregation
task-scoped backend tests
```

---

## Endpoint

```http
GET /audits/{id}/progress
```

Response:

```json
{
  "audit_id": 1,
  "status": "running",
  "total_runs": 120,
  "queued_runs": 10,
  "running_runs": 2,
  "completed_runs": 80,
  "failed_runs": 3,
  "skipped_runs": 0,
  "percent_complete": 69.2,
  "current_job_id": "job-123",
  "provider_diagnostics": []
}
```

---

## Rules

- Requires auth/ownership.
- Works for queued/running/completed/partial/failed audits.
- Handles legacy synchronous audits safely.
- Does not expose raw provider data.

---

## Tests

Backend/API tests:

```text
unauthenticated rejected
non-owner rejected
progress for created audit
progress for running audit
progress for completed audit
progress for partial/failed audit
percent calculation safe
zero total safe
provider diagnostics safe
```

---

## Acceptance criteria

- Progress endpoint exists.
- Auth/ownership enforced.
- Progress counts correct.
- Percent safe.
- Diagnostics safe.
- Task-scoped backend tests pass.
- Touched-file ruff passes.

---

## Non-goals

- Do not implement frontend progress UI.
- Do not implement cancel/retry.
- Do not change provider execution.
