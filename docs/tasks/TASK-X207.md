# TASK-X207 — Add Repeat Audit Action

## Goal

Add a Repeat Audit action that creates a new audit based on an existing audit configuration.

This supports the Web5 “Repeat audit” action.

---

## Scope

Implement:

```text
repeat/duplicate audit backend endpoint or existing action integration
frontend action button
safe copy of audit config
task-scoped tests
```

---

## Suggested endpoint

```http
POST /audits/{id}/duplicate
```

or use an existing duplicate endpoint if already implemented.

---

## Duplication rules

Copy:

```text
brand
domain
description
seed queries
model_targets
competitors if user-provided
settings
```

Do not copy:

```text
runs/results
raw responses
parsed results
scores
evaluations
source records
provider diagnostics
created/completed status
```

New audit should start in:

```text
created
```

---

## Auth/ownership

- Requires login.
- Enforces ownership of source audit.
- New audit owned by current user.

---

## Frontend behavior

- Repeat Audit button calls duplicate endpoint.
- On success, navigate to new audit detail/create page.
- Show loading/error states.

---

## Tests

Backend:

```text
owner can duplicate audit
non-owner rejected
new audit has copied config
new audit has no results/runs
model_targets copied
seed queries copied
status created
```

Frontend:

```text
button calls endpoint
success navigates
loading/error states
```

---

## Acceptance criteria

- Repeat audit action exists.
- Copies configuration only.
- Does not copy results/raw data.
- Auth/ownership enforced.
- Frontend action works.
- Task-scoped tests pass.
- Touched-file ruff/typecheck passes.

---

## Non-goals

- Do not start the new audit automatically.
- Do not copy raw responses/results/evaluations.
- Do not implement scheduled recurring audits.
