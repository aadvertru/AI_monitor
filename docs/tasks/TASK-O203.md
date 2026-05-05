# TASK-O203 — Add Language Switcher and Locale Persistence

## Goal

Add a user-facing language switcher and persist selected locale.

---

## Scope

Implement:

```text
language switcher component
locale persistence
app shell integration
task-scoped frontend tests
```

---

## Persistence

Recommended MVP:

```text
localStorage
```

If profile preferences already support locale, use them only if easy and stable.

Rules:

```text
do not hardcode only en/ru in logic
use configured locales list
fallback to en for invalid/missing locale
```

---

## UI

Language switcher may be in:

```text
app shell
profile page
user menu
```

Use existing design system.

Display labels:

```text
English
Русский
```

or localized labels.

---

## Tests

Frontend tests:

```text
language switcher renders
switching to ru changes translated label
switching to en changes translated label
selection persists after reload
invalid stored locale falls back safely
future locale list can be extended
```

---

## Acceptance criteria

- Language switcher exists.
- Locale persists.
- Invalid locale fallback works.
- Logic is not hardcoded to exactly two languages.
- Task-scoped frontend tests pass.
- TypeScript passes.

---

## Non-goals

- Do not translate full app yet.
- Do not change backend locale.
- Do not translate raw AI answers/user content.
