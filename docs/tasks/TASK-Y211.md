# TASK-Y211 — Add Execution/Usage Verification Checklist

## Goal

Create a manual QA checklist for usage accounting, background execution, progress, cancel, and retry.

This task is documentation-only. Do not change runtime code.

---

## File to create

```text
docs/EXECUTION_USAGE_VERIFICATION.md
```

---

## Required scenarios

Use standard scenario format.

Scenarios:

```text
Y-S01 — Run estimate for small audit
Y-S02 — Over-cap audit rejected
Y-S03 — Start audit enqueues background job
Y-S04 — Progress endpoint updates during run
Y-S05 — UI progress polling works
Y-S06 — Completed audit reaches terminal state
Y-S07 — Cancel running audit
Y-S08 — Retry failed runs
Y-S09 — Successful runs not duplicated on retry
Y-S10 — Usage aggregation shown
Y-S11 — Provider diagnostics safe
Y-S12 — No raw provider data exposed
```

---

## Result table

Include standard result table.

---

## Captured issues section

Use standard issue template.

---

## Acceptance criteria

- `docs/EXECUTION_USAGE_VERIFICATION.md` exists.
- Scenarios Y-S01 through Y-S12 included.
- Result table included.
- Captured issue template included.
- Checklist verifies estimate, background execution, progress, cancel, retry, usage, safety.
- No runtime code changed.

---

## Non-goals

- Do not run checklist.
- Do not fix bugs.
