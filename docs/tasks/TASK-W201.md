# TASK-W201 — Define Web6/Web7 Answer Matrix UI Contract

## Goal

Define the implementation contract for the Web6/Web7-style answer matrix UI.

This task is documentation/contract only. Do not change runtime code.

---

## Context

The target screen is a matrix:

```text
rows = questions / seed queries
columns = model/level targets
cells = answer excerpt + verdict badge + rationale + expand details
```

The matrix must use backend-provided Answer Matrix DTO. Frontend must not build scoring/evaluation logic.

---

## File to create

```text
docs/ANSWER_MATRIX_UI_CONTRACT.md
```

---

## Required decisions

### 1. Data source

Use:

```http
GET /audits/{id}/answer-matrix
```

### 2. Layout

Document:

```text
left sticky question column
horizontal scroll for model columns
columns grouped/labeled by model + level
cell content includes status, excerpt, evaluation verdict, rationale preview
expand action opens detailed view
```

### 3. Cell states

Support:

```text
completed
failed
partial
not_run
processing
missing
```

### 4. Verdict display

Map evaluation verdict codes:

```text
correct
partial
incorrect
unknown
not_applicable
```

Frontend translates labels. Do not hardcode Russian-only labels.

### 5. Filters

Document filters:

```text
level
AI family
model
verdict
query type
status
```

### 6. Raw content rule

Document:

```text
answer excerpt/full answer may be shown only from safe normalized fields
raw provider response is never displayed
raw prompts are never displayed
```

---

## Acceptance criteria

- Answer matrix UI contract exists.
- Data source documented.
- Layout documented.
- Cell state handling documented.
- Verdict label/i18n rules documented.
- Filters documented.
- Safety rules documented.
- No runtime code changed.

---

## Non-goals

- Do not implement matrix UI.
- Do not change backend.
- Do not implement evaluation.
