# TASK-O207 — Add Locale-Aware Date, Number, and Percent Formatting

## Goal

Add locale-aware formatting helpers for dates, numbers, and percentages.

---

## Scope

Implement:

```text
date/time formatter
number formatter
percent formatter
shared formatting utilities/hooks
task-scoped frontend tests
```

Use browser `Intl` APIs or i18n library utilities.

---

## Formatting targets

Use helpers for:

```text
audit timestamps
checked_at dates
evaluated_at dates
percentages in summary cards
token counts
run counts
source counts
```

---

## Rules

- Use active locale.
- Fallback to en.
- Do not alter raw AI answer text.
- Keep numeric values intact; format only for display.

---

## Tests

Frontend tests:

```text
date formats differ for en/ru where expected
percent formatting works
large number formatting works
fallback locale safe
formatters handle null/undefined safely
```

---

## Acceptance criteria

- Shared locale-aware formatters exist.
- Core displays use formatters where touched.
- Null/undefined safe.
- Task-scoped frontend tests pass.
- TypeScript passes.

---

## Non-goals

- Do not translate content.
- Do not change backend date formats.
- Do not implement timezone settings unless already available.
