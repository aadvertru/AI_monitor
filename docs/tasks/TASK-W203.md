# TASK-W203 — Implement Answer Matrix Layout

## Goal

Implement the core answer matrix layout: questions as rows and audit targets as columns.

---

## Scope

Implement:

```text
matrix table/grid layout
question rows
target columns
sticky/fixed question column if practical
horizontal scroll
basic cell placeholders
task-scoped frontend tests
```

Do not implement final cell content/filters yet.

---

## Layout rules

- Rows correspond to backend matrix rows.
- Columns correspond to backend matrix columns.
- Cells map by `target_id`.
- Frontend must not recalculate matrix shape.
- Long question text should wrap or truncate safely.
- Many columns should scroll horizontally.

---

## Tests

Frontend tests:

```text
columns render from matrix columns
rows render from matrix rows
cells align by target_id
missing cells render safe placeholder
horizontal scroll container exists
long question safe
OpenRouter gateway column metadata does not break layout
```

---

## Acceptance criteria

- Matrix rows/columns render.
- Cells align correctly.
- Missing cells safe.
- Horizontal scroll supported.
- No metric calculation in frontend.
- Task-scoped frontend tests pass.
- TypeScript passes.

---

## Non-goals

- Do not implement cell verdict UI yet.
- Do not implement filters.
- Do not implement expand details.
- Do not change backend.
