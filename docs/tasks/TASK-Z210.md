# TASK-Z210 — Add Longitudinal Analytics Verification Checklist

## Goal

Create a manual QA checklist for audit comparison and longitudinal analytics.

This task is documentation-only. Do not change runtime code.

---

## File to create

```text
docs/LONGITUDINAL_ANALYTICS_VERIFICATION.md
```

---

## Required scenarios

Use standard scenario format.

Scenarios:

```text
Z-S01 — Comparison candidates list
Z-S02 — Compare two completed audits
Z-S03 — Compare audits with missing evaluation
Z-S04 — Compare audits with changed model set
Z-S05 — Visibility trend chart/table
Z-S06 — Accuracy trend null-safe
Z-S07 — Source domain changes
Z-S08 — Concept changes
Z-S09 — Competitor changes
Z-S10 — No previous audits empty state
Z-S11 — Legacy audit comparison
Z-S12 — No raw provider data exposed
```

---

## Result table

Include standard result table with `Not run | Pass | Fail | Blocked | Partial`.

---

## Captured issues section

Use standard issue template.

---

## Acceptance criteria

- `docs/LONGITUDINAL_ANALYTICS_VERIFICATION.md` exists.
- Scenarios Z-S01 through Z-S12 included.
- Result table included.
- Captured issue template included.
- Checklist verifies comparison, trends, missing data, legacy, safety.
- No runtime code changed.

---

## Non-goals

- Do not run checklist.
- Do not fix issues.
- Do not implement analytics.
