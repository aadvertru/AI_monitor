# TASK-W210 — Add Web6/Web7 Matrix Verification Checklist

## Goal

Create a manual QA checklist for the Web6/Web7 answer matrix UI.

This task is documentation-only. Do not change runtime code.

---

## File to create

```text
docs/ANSWER_MATRIX_UI_VERIFICATION.md
```

---

## Required scenarios

Use standard scenario format with purpose, preconditions, steps, expected result, actual result, status, and issue ID.

Scenarios:

```text
W-S01 — Matrix renders completed audit
W-S02 — Matrix renders multi-model L1/L2 audit
W-S03 — Correct/partial/incorrect verdict badges
W-S04 — Cell rationale preview
W-S05 — Cell expand details
W-S06 — Failed cell diagnostics
W-S07 — Missing/not-run cell state
W-S08 — Level filter
W-S09 — Model/AI family filter
W-S10 — Verdict filter
W-S11 — Query type filter
W-S12 — OpenRouter L2 experimental marker
W-S13 — Horizontal scroll/many columns
W-S14 — Mobile matrix smoke test
W-S15 — No raw provider data exposed
W-S16 — i18n labels
```

---

## Result table

Include standard result table with `Not run | Pass | Fail | Blocked | Partial`.

---

## Captured issues section

Use standard issue template.

---

## Acceptance criteria

- `docs/ANSWER_MATRIX_UI_VERIFICATION.md` exists.
- Scenarios W-S01 through W-S16 included.
- Result table included.
- Captured issue template included.
- Checklist verifies matrix rendering, filters, expand, states, responsive behavior, i18n, safety.
- No runtime code changed.

---

## Non-goals

- Do not run checklist.
- Do not fix issues.
- Do not implement UI.
