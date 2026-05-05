# TASK-W206 — Add Answer Matrix Filters

## Goal

Add filters to the answer matrix.

Filters should help users focus by level, AI family, model, verdict, query type, and status.

---

## Scope

Implement:

```text
level filter
AI family filter
model filter
verdict filter
query type filter
status filter
clear filters action
task-scoped frontend tests
```

---

## Filtering behavior

Filters are frontend view filters over backend matrix data.

Allowed because they do not calculate scores or classifications.

Filters should not mutate audit data.

---

## Filters

Recommended:

```text
Level: L1 / L2
AI family: ChatGPT / Gemini / Claude / ...
Model: model display name
Verdict: correct / partial / incorrect / unknown
Query type: seed query type
Status: completed / failed / missing / ...
```

---

## Tests

Frontend tests:

```text
level filter hides/shows columns/cells
AI family filter works
model filter works
verdict filter works
query type filter works
status filter works
clear filters resets
empty filtered state renders
filters preserve row/column alignment
```

---

## Acceptance criteria

- Matrix filters implemented.
- Filters do not mutate data.
- Empty filtered state works.
- Row/column alignment preserved.
- i18n labels used.
- Task-scoped frontend tests pass.
- TypeScript passes.

---

## Non-goals

- Do not implement backend filtering unless already designed.
- Do not change matrix endpoint.
- Do not calculate metrics.
