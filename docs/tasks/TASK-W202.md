# TASK-W202 — Add Answer Matrix Data Hook and Page Shell

## Goal

Add frontend data hook and page shell for the Web6/Web7-style answer matrix.

This task should wire to the matrix endpoint but not implement full matrix layout yet.

---

## Scope

Implement:

```text
answer matrix query hook
page/container shell
loading/error/empty states
provider diagnostics placeholder
task-scoped frontend tests
```

---

## Data source

Use:

```text
GET /audits/{id}/answer-matrix
```

Use existing API client and TanStack Query conventions.

---

## Page shell

Include placeholders for:

```text
filters area
matrix area
cell detail area/modal
diagnostics area
```

---

## Tests

Frontend tests:

```text
matrix hook calls endpoint
loading state renders
error state renders safely
empty matrix state renders
page shell renders with mock data
provider diagnostics placeholder safe
```

---

## Acceptance criteria

- Matrix data hook exists.
- Matrix page shell exists.
- Loading/error/empty states work.
- No raw API/provider payload displayed.
- Task-scoped frontend tests pass.
- TypeScript passes.

---

## Non-goals

- Do not implement full matrix grid.
- Do not implement filters.
- Do not implement cell expand.
- Do not change backend.
