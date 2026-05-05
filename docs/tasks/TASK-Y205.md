# TASK-Y205 — Move Audit Pipeline Run to Background Execution

## Goal

Move user-triggered audit pipeline execution from synchronous request handling to background execution.

The Start Audit action should enqueue a job and return quickly.

---

## Scope

Implement:

```text
run-pipeline endpoint enqueues background job
background worker executes existing pipeline
safe status updates
task-scoped backend tests
```

Do not redesign pipeline internals.

---

## Endpoint behavior

Current:

```text
POST /audits/{id}/run-pipeline runs synchronously
```

Target:

```text
POST /audits/{id}/run-pipeline enqueues job and returns job/audit status
```

Response example:

```json
{
  "audit_id": 1,
  "job_id": "job-123",
  "status": "running"
}
```

Use existing conventions.

---

## Rules

- Requires auth/ownership.
- Prevent duplicate active jobs for same audit.
- Existing pipeline service reused.
- Provider calls still follow caps/guardrails.
- No raw provider data exposed.

---

## Tests

Backend/API tests:

```text
run-pipeline enqueues job
non-owner rejected
duplicate start prevented
background job executes mocked pipeline
audit status becomes running
terminal status set after job complete
provider errors safe
```

---

## Acceptance criteria

- Start audit returns quickly with job/status.
- Pipeline executes in background path.
- Duplicate starts prevented.
- Existing pipeline logic reused.
- Task-scoped backend tests pass.
- Touched-file ruff passes.

---

## Non-goals

- Do not implement advanced queue infra if not needed.
- Do not implement cancel/retry yet.
- Do not change parser/scoring.
- Do not redesign frontend beyond API contract if separate task handles UI.
