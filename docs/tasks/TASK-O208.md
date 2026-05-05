# TASK-O208 — Add i18n Fixtures and Regression Tests

## Goal

Add i18n fixtures and regression tests to prevent accidental hardcoded labels and broken locale behavior.

---

## Scope

Implement:

```text
translation fixture tests
common page render tests in en/ru
missing key behavior tests
locale persistence tests
raw content non-translation tests
```

---

## Required test surfaces

At minimum cover:

```text
app shell
auth page
audit create page
audit list/detail
profile page if implemented
results summary/sources labels if implemented
```

---

## Tests

```text
renders main routes in en
renders main routes in ru
language switch persists
fallback works
status labels translated from codes
verdict labels translated from codes if present
raw AI answer remains unchanged
seed query text remains unchanged
brand description remains unchanged
```

---

## Acceptance criteria

- i18n regression tests exist.
- Main routes render in en/ru.
- Raw content is not translated.
- Missing/fallback behavior safe.
- Task-scoped frontend tests pass.
- TypeScript passes.

---

## Non-goals

- Do not implement new UI.
- Do not add more locales yet.
- Do not change backend.
