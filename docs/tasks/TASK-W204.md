# TASK-W204 — Implement Matrix Cell Rendering

## Goal

Implement answer matrix cell rendering with status, answer excerpt, evaluation verdict badge, rationale preview, and source count.

---

## Scope

Implement:

```text
cell status display
answer excerpt display
evaluation verdict badge
rationale preview
source count
failed/error cell state
task-scoped frontend tests
```

---

## Cell content

For completed cells:

```text
verdict badge if evaluation exists
answer excerpt
rationale preview if evaluation rationale exists
source count if available
expand button placeholder
```

For failed cells:

```text
failed status
safe provider error message if available
```

For missing/not_run cells:

```text
safe empty placeholder
```

---

## Verdict labels

Translate from codes:

```text
correct
partial
incorrect
unknown
not_applicable
```

Example labels:

```text
Correct / Верно
Partial / Частично
Error / Ошибка
Unknown / Неизвестно
```

Use i18n keys, not hardcoded language-specific text.

---

## Tests

Frontend tests:

```text
completed cell renders excerpt
correct verdict badge renders
partial verdict badge renders
incorrect verdict badge renders
unknown/null evaluation safe
rationale preview renders
source count renders
failed cell shows provider error
missing cell safe
i18n verdict labels render
unsafe raw fields not rendered
```

---

## Acceptance criteria

- Matrix cells render status/excerpt/verdict/rationale/source count.
- Failed/missing/null states safe.
- Verdict labels i18n-ready.
- No raw provider response shown.
- Task-scoped frontend tests pass.
- TypeScript passes.

---

## Non-goals

- Do not implement expand details yet.
- Do not implement filters.
- Do not change backend.
