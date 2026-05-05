# TASK-X207B — Add Repeat Audit Frontend Action

## Status

Ready for implementation.

## Goal

Wire the Web5 Repeat Audit action to the duplicate audit backend endpoint.

## Dependencies

Requires:

```text
TASK-X207A — POST /audits/{id}/duplicate
Web5 summary action area
```

## Scope

Implement:

```text
frontend API client method
Repeat Audit button wiring
loading/error states
success navigation
task-scoped frontend tests
```

## Behavior

On click:

```text
call POST /audits/{id}/duplicate
show loading state
on success, navigate to new audit detail/create page according to product convention
show safe error on failure
```

Do not start the new audit automatically.

## Tests

Frontend tests:

```text
button calls duplicate endpoint
loading state works
success navigates to new audit
safe error state works
raw backend error not displayed
button disabled while request active
```

## Acceptance criteria

- Repeat Audit button calls backend duplicate endpoint.
- Success navigates to new audit.
- Loading/error states work.
- No raw API payload displayed.
- Task-scoped frontend tests pass.
- TypeScript passes.

## Escalate if

- Duplicate endpoint is missing.
- Routing target for new audit is undefined.
- Product wants repeat audit to auto-start.

## Commands

```bash
cd apps/web
npm run typecheck
npm test -- <repeat audit frontend tests>
```

## Done means

Repeat Audit works as a frontend action using the backend duplicate endpoint and does not auto-run the audit.
