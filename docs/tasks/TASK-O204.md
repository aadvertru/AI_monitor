# TASK-O204 — Translate Core App Shell, Navigation, Auth, and Common UI

## Goal

Translate core frontend UI surfaces using the i18n framework.

---

## Scope

Translate:

```text
app shell
navigation
common buttons
common status labels
auth pages
protected route messages
loading/error/empty state primitives
```

Do not translate audit results/raw answers in this task.

---

## Rules

- Use translation keys.
- No inline hardcoded user-facing strings in touched components.
- Backend codes translated frontend-side.
- Support future locales by adding keys, not code branches.

---

## Tests

Frontend tests:

```text
navigation labels render in en/ru
auth labels render in en/ru
common buttons render in en/ru
loading/error labels translated
missing translation fallback safe
```

---

## Acceptance criteria

- Core app shell translated.
- Auth/common UI translated.
- Translation keys organized by namespace.
- No raw AI/user content translated.
- Task-scoped frontend tests pass.
- TypeScript passes.

---

## Non-goals

- Do not translate every audit/results screen yet.
- Do not change backend.
- Do not implement profile page.
