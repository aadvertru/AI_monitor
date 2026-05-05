# TASK-W211 — Verify and Stabilize Web6/Web7 Answer Matrix UI

## Goal

Run the Web6/Web7 matrix verification checklist and fix only issues captured during verification.

This task closes Phase W.

---

## Required input

Read:

```text
docs/ANSWER_MATRIX_UI_CONTRACT.md
docs/ANSWER_MATRIX_UI_VERIFICATION.md
```

Use captured issues from verification.

---

## Scope

Allowed fixes:

```text
matrix layout bugs
cell rendering bugs
expand details bugs
filter bugs
empty/partial/failed state bugs
responsive/accessibility bugs
provider diagnostics display bugs
OpenRouter experimental marker bugs
i18n label bugs
unsafe raw data rendering bugs
```

Not allowed:

```text
backend matrix redesign
evaluation backend changes
source aggregation changes
exports
parser/scoring changes
unrelated legacy fixes
```

---

## Verification expectations

Run scenarios:

```text
W-S01 through W-S16
```

Every non-pass scenario must have captured issue.

---

## Tests to add/update

Add task-scoped tests based on actual issues.

Likely tests:

```text
matrix alignment
cell states
verdict labels
expand details
filters
provider diagnostics
responsive/accessibility
no raw data
```

---

## Acceptance criteria

- Verification document updated with final results.
- Blocker/major matrix UI issues fixed or deferred with rationale.
- Matrix is usable for multi-model L1/L2 audits.
- Cells show verdict/excerpt/rationale/status safely.
- Expand details work.
- Filters work.
- Responsive/accessibility basics covered.
- No raw provider data exposed.
- Task-scoped frontend tests pass.
- TypeScript passes.

---

## Non-goals

- Do not change backend DTOs unless issue is explicitly captured and scoped.
- Do not implement exports.
- Do not change scoring/evaluation methodology.
- Do not fix unrelated bugs.
