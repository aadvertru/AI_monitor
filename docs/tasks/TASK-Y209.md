# TASK-Y209 — Add Frontend Progress, Cancel, and Retry UI

## Goal

Add frontend UI for audit progress, cancel, and retry failed runs.

---

## Scope

Implement:

```text
progress polling hook
progress display
cancel button
retry failed button
loading/error states
task-scoped frontend tests
```

---

## Data/actions

Use:

```http
GET /audits/{id}/progress
POST /audits/{id}/cancel
POST /audits/{id}/retry-failed
```

---

## UI behavior

Progress display:

```text
total runs
completed
failed
running/queued
percent complete
status
```

Cancel:

```text
visible for running/queued audits
confirmation recommended
loading state
safe error
```

Retry failed:

```text
visible for partial/failed audits with failed/skipped runs
loading state
safe error
starts/polls new job
```

---

## Tests

Frontend tests:

```text
progress renders
polling updates progress
cancel button visible when running
cancel confirmation/action works
retry button visible when failed runs exist
retry action works
loading/error states
provider diagnostics safe
no raw errors displayed
```

---

## Acceptance criteria

- Progress UI renders.
- Polling works.
- Cancel action works.
- Retry failed action works.
- States are safe and accessible.
- Task-scoped frontend tests pass.
- TypeScript passes.

---

## Non-goals

- Do not implement backend endpoints.
- Do not redesign results UI.
- Do not implement billing.
