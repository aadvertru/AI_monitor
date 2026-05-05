# TASK-V210 — Add Web5 Summary Verification Checklist

## Goal

Create a manual QA checklist for the Web5-style summary page.

This task is documentation-only. Do not change runtime code.

---

## File to create

```text
docs/WEB5_SUMMARY_VERIFICATION.md
```

---

## Required scenarios

Use standard scenario format with purpose, preconditions, steps, expected result, actual result, status, and issue ID.

Scenarios:

```text
V-S01 — Completed audit summary renders
V-S02 — Partial audit summary renders
V-S03 — Failed/no-data audit safe state
V-S04 — Mentionability L1/L2 cards
V-S05 — Accuracy cards with evaluation
V-S06 — Accuracy cards without evaluation
V-S07 — Tone/sentiment card
V-S08 — Model summary table
V-S09 — OpenRouter experimental L2 marker
V-S10 — Rerun fact-checking action
V-S11 — DOCX/Excel/Repeat placeholders
V-S12 — i18n labels
V-S13 — Mobile layout
V-S14 — No raw provider data exposed
```

---

## Result table

Include standard result table with `Not run | Pass | Fail | Blocked | Partial`.

---

## Captured issues section

Use standard issue template.

---

## Acceptance criteria

- `docs/WEB5_SUMMARY_VERIFICATION.md` exists.
- Scenarios V-S01 through V-S14 included.
- Result table included.
- Captured issue template included.
- Checklist verifies Web5 UI, actions, i18n, mobile, safety.
- No runtime code changed.

---

## Non-goals

- Do not run checklist.
- Do not fix bugs.
- Do not implement UI.
