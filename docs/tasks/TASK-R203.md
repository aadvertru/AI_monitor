# TASK-R203 — Add Answer Matrix DTO and Endpoint

## Goal

Add a backend answer matrix endpoint that returns query × target cells for Web6/Web7-style results.

Frontend must receive matrix-ready data and must not assemble the matrix from raw results.

---

## Scope

Implement:

```text
answer matrix DTOs
matrix aggregation service
GET /audits/{id}/answer-matrix endpoint
task-scoped backend tests
```

Do not implement frontend matrix UI in this task.

---

## Endpoint

Preferred:

```http
GET /audits/{id}/answer-matrix
```

Use existing auth/ownership guards.

---

## Required response shape

Return:

```text
audit_id
columns
rows
provider_diagnostics
```

### Columns

One column per audit target.

Each column should include:

```text
target_id
label
ai_family
execution_provider
model_provider
model_id
level
gateway
gateway_l2_experimental
```

### Rows

One row per seed query.

Each row should include:

```text
query_id
query_text
query_type
cells
```

### Cells

One cell per query × target.

Each cell should include:

```text
target_id
run_id
status
answer_excerpt
brand_mentioned
score
evaluation
sources_count
provider_error
```

Evaluation may be null/unknown until Phase S.

---

## Cell state rules

Support these states safely:

```text
completed
failed
partial
not_run
processing
missing
```

Use current project status naming where possible.

### Completed cell

Should include answer excerpt and existing parser/scoring data.

### Failed cell

Should include safe provider_error if available.

### Missing/not_run cell

Should render as empty safe cell, not crash.

---

## Answer excerpt rules

- Excerpt should be backend-generated.
- Do not expose full raw response unless existing result detail endpoint already safely does so.
- Limit excerpt length consistently.
- Do not include raw provider payload.

Recommended:

```text
answer_excerpt_max_chars = 500
```

or project convention.

---

## Backward compatibility

- Legacy audits without audit targets should produce safe fallback columns.
- Old seed_queries list must work.
- New seed_query_items must work.
- Existing results endpoint remains backward compatible.

---

## Tests

Add task-scoped backend/API tests.

Test:

```text
requires auth
enforces ownership
columns match audit targets
rows match seed queries
cells map query × target
completed cell includes answer excerpt
failed cell includes safe provider_error
missing cell safe
partial audit safe
legacy audit safe
OpenRouter gateway metadata included
evaluation null/unknown before Phase S
no raw provider response exposed
```

---

## Acceptance criteria

- Answer matrix endpoint exists.
- Endpoint is authenticated and owner-scoped.
- Matrix columns are backend-generated from audit targets.
- Matrix rows are backend-generated from seed queries.
- Matrix cells map query × target correctly.
- Failed/partial/missing states are safe.
- Evaluation placeholder is present or safely null.
- Raw provider responses/prompts are not exposed.
- Task-scoped backend tests pass.
- Touched-file ruff passes.

---

## Non-goals

- Do not implement frontend matrix UI.
- Do not implement evaluation.
- Do not implement exports.
- Do not change parser/scoring methodology.
- Do not fix unrelated legacy failures.
