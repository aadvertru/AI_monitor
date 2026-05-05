# TASK-V206 — Wire Rerun Fact-Checking Action in Summary UI

## Status

Ready for implementation.

## Goal

Wire the “Rerun fact-checking” action on the Web5 summary page.

This action must call the evaluation rerun endpoint and refresh summary/matrix data.

## Dependencies

Requires:

```text
TASK-S205 — POST /audits/{id}/rerun-evaluation
TASK-S208 — frontend rerun evaluation client/hook
Web5 summary page shell
```

## Scope

Implement:

```text
rerun fact-checking button
mutation wiring
loading state
success/warning display
safe error state
query invalidation/refetch
task-scoped frontend tests
```

## Backend availability rule

The backend endpoint is required.

If `POST /audits/{id}/rerun-evaluation` is unavailable, this is a blocker/escalation condition, not an acceptable disabled implementation.

Do not silently ship a permanently disabled rerun fact-checking button for this task.

## Behavior

On click:

```text
disable button while request is running
show loading state
call rerun evaluation endpoint
on success, invalidate/refetch:
  - summary v2
  - answer matrix
  - audit status/detail if relevant
show warnings if returned
```

Do not rerun provider calls.

## Error handling

Show safe error message only.

Do not show:

```text
raw API response
raw evaluator/provider payload
stack trace
secrets
```

## Tests

Frontend tests:

```text
button renders enabled when endpoint/client available
click calls rerun endpoint
loading state works
success invalidates summary/matrix queries
warnings render
safe error renders
raw API body not displayed
```

## Acceptance criteria

- Rerun fact-checking action is wired to backend endpoint.
- Backend unavailable is treated as blocker/escalation.
- Loading/success/error states work.
- Summary/matrix refetch after success.
- No raw data/secrets displayed.
- Task-scoped frontend tests pass.
- TypeScript passes.

## Escalate if

- Backend rerun endpoint is missing.
- Existing query cache keys for summary/matrix are not available.
- Product wants the button disabled despite missing backend.

## Commands

```bash
cd apps/web
npm run typecheck
npm test -- <rerun fact-checking UI tests>
```

## Done means

The Web5 rerun fact-checking button performs the real rerun-evaluation mutation and refetches affected result data.
