# TASK-Y207 — Add Cancel Audit Run Backend

## Goal

Add backend support for cancelling an active audit run/job.

---

## Scope

Implement:

```text
cancel endpoint
cancel_requested state
pending job/run cancellation
safe terminal status
task-scoped backend tests
```

---

## Endpoint

```http
POST /audits/{id}/cancel
```

Response:

```json
{
  "audit_id": 1,
  "status": "cancel_requested"
}
```

Use existing conventions.

---

## Rules

- Requires auth/ownership.
- Only active/running audits can be cancelled.
- Completed runs remain preserved.
- Pending runs are skipped/cancelled.
- Running provider call may not be interruptible; mark cancellation once safe.
- No raw provider data exposed.
- Final status policy must follow contract:
  - `cancelled` if status exists
  - or `partial` with cancellation reason if not

---

## Tests

Backend/API tests:

```text
owner can cancel running audit
non-owner rejected
cannot cancel completed audit
pending runs skipped/cancelled
completed results preserved
running job observes cancel request if possible
final status correct
no raw data exposed
```

---

## Acceptance criteria

- Cancel endpoint exists.
- Auth/ownership enforced.
- Active audit can be cancelled.
- Completed results preserved.
- Pending work stopped/skipped where possible.
- Status updated safely.
- Task-scoped backend tests pass.
- Touched-file ruff passes.

---

## Non-goals

- Do not implement frontend cancel button.
- Do not guarantee immediate interruption of in-flight HTTP call.
- Do not redesign provider adapters.
- Do not change parser/scoring.
