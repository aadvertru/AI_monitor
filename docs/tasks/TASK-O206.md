# TASK-O206 — Translate Results UI Labels and Profile Labels When Present

## Status

Ready for implementation.

## Goal

Translate remaining static labels for results-related screens and profile/account shell where those screens already exist.

Do not implement profile UI in this task.

## Dependencies

Requires:

```text
TASK-O202
TASK-O203
```

Profile label translation depends on Phase P components existing. If Profile components do not exist yet, add translation namespace keys only and do not touch non-existing UI.

## Scope

Translate labels for existing components only:

```text
summary cards
results table/matrix labels if present
sources tab labels
concepts/competitors labels if present
profile/account labels if Profile screen already exists
notification labels if Profile screen already exists
plan/usage labels if Profile screen already exists
export button labels if present
```

## Rules

Do not translate:

```text
raw AI answers
query text
brand description
source titles/snippets
model ids
provider ids
email/name values
```

Evaluation verdict labels should be translated from codes if evaluation exists:

```text
correct → Correct / Верно
partial → Partial / Частично
incorrect → Error / Ошибка
unknown → Unknown / Неизвестно
```

Support future locales through translation files.

## Tests

Frontend tests:

```text
summary labels translated if summary exists
sources labels translated if sources UI exists
profile labels translated only if profile UI exists
verdict labels translated if present
raw answer text unchanged
source title/snippet unchanged
model id unchanged
```

## Acceptance criteria

- Existing results/profile static labels translated.
- If Profile UI does not exist, profile namespace keys may be added but no runtime UI change is made.
- Verdict labels translation-ready.
- Raw content not translated.
- Task-scoped frontend tests pass.
- TypeScript passes.

## Escalate if

- Profile screen does not exist but product expects this task to implement it.
- Results UI components are being replaced by Web5/Web6 tasks and translating them now would be wasted.

## Commands

```bash
cd apps/web
npm run typecheck
npm test -- <i18n label tests>
```

## Done means

Existing results/profile labels are translation-backed without creating new Profile UI or translating raw content.
