# TASK-O209 — Add i18n Verification Checklist

## Goal

Create a manual QA checklist for i18n.

This task is documentation-only. Do not change runtime code.

---

## File to create

```text
docs/I18N_VERIFICATION.md
```

---

## Required scenarios

Use standard format with purpose, preconditions, steps, expected result, actual result, status, and issue ID.

Scenarios:

```text
O-S01 — Default locale loads
O-S02 — Switch to Russian
O-S03 — Switch back to English
O-S04 — Locale persists after reload
O-S05 — Invalid stored locale falls back safely
O-S06 — App shell/auth translated
O-S07 — Audit create/list/detail translated
O-S08 — Results/profile labels translated
O-S09 — Status/error/verdict labels translated
O-S10 — Raw answers/user content not translated
O-S11 — Date/number/percent formatting changes by locale
O-S12 — Mobile language switcher smoke test
```

---

## Result table

Include standard result table with:

```text
Not run
Pass
Fail
Blocked
Partial
```

---

## Captured issues section

Use standard issue template.

---

## Acceptance criteria

- `docs/I18N_VERIFICATION.md` exists.
- Scenarios O-S01 through O-S12 included.
- Result table included.
- Captured issue template included.
- Checklist verifies future-language-ready behavior.
- Checklist verifies raw content is not translated.
- No runtime code changed.

---

## Non-goals

- Do not run checklist.
- Do not fix i18n bugs.
