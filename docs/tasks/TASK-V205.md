# TASK-V205 — Implement Web5 Model Summary Section

## Goal

Implement the Web5 “Summary by Models” section.

This section compares model-level metrics across L1 and L2.

---

## Scope

Implement:

```text
model summary table or cards
MR L1/MR L2 columns
delta MR
accuracy L1/accuracy L2
delta accuracy
tone L1/tone L2
task-scoped frontend tests
```

---

## Data source

Use `model_summaries` from summary v2.

Frontend must not aggregate model metrics itself.

---

## Table/card columns

Recommended:

```text
Model
MR L1
MR L2
Δ MR
Accuracy L1
Accuracy L2
Δ Accuracy
Tone L1
Tone L2
```

Use project labels. Keep responsive behavior in mind.

---

## Missing data

Handle:

```text
model has only L1
model has only L2
accuracy unavailable
tone unavailable
partial audit
failed target
```

Use `N/A`, dash, or project empty-state convention.

---

## Deltas

If backend provides deltas, display them.

If backend does not provide deltas, do not calculate unless contract explicitly allows simple display formatting.

Preferred: backend provides deltas.

---

## i18n

All labels use translation keys.

Model ids/display names are not translated.

---

## Tests

Frontend tests:

```text
model summary rows render
L1/L2 values render
missing L2 handled
missing accuracy handled
delta values render
tone values render
partial/failed model rows safe
i18n labels render
responsive horizontal scroll or card fallback works
```

---

## Acceptance criteria

- Model summary section implemented.
- Uses backend model_summaries.
- Missing/null values safe.
- No frontend metric aggregation.
- i18n labels used.
- Task-scoped frontend tests pass.
- TypeScript passes.

---

## Non-goals

- Do not implement matrix UI.
- Do not change backend metrics.
- Do not implement exports.
- Do not calculate scoring in frontend.
