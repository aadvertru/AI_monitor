# TASK-O210 — Verify and Stabilize i18n

## Goal

Run the i18n verification checklist and fix only issues captured during verification.

This task closes Phase O.

---

## Required input

Read:

```text
docs/I18N_CONTRACT.md
docs/I18N_VERIFICATION.md
```

Use captured issues from verification.

---

## Scope

Allowed fixes:

```text
translation key bugs
language switcher bugs
locale persistence bugs
fallback bugs
hardcoded labels in scoped surfaces
formatting bugs
raw content accidental translation bugs
mobile switcher blockers
```

Not allowed:

```text
adding many new languages
backend localization redesign
raw answer translation
auth redesign
unrelated UI redesign
unrelated legacy fixes
```

---

## Verification expectations

Run scenarios:

```text
O-S01 through O-S12
```

Every non-pass scenario must have captured issue.

---

## Tests to add/update

Add task-scoped tests based on actual issues.

Likely tests:

```text
switch locale
persist locale
fallback locale
translated labels
raw content unchanged
date/number/percent formatting
```

---

## Acceptance criteria

- Verification document updated with final results.
- Blocker/major i18n issues fixed or deferred with rationale.
- en/ru UI works.
- Architecture remains future-locale-ready.
- Raw AI/user content not translated.
- Task-scoped frontend tests pass.
- TypeScript passes.

---

## Non-goals

- Do not add many new locales.
- Do not translate raw answers.
- Do not change backend contracts.
- Do not fix unrelated bugs.
