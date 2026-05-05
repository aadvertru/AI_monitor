# TASK-O202 — Add i18n Framework and Locale Files

## Status

Ready for implementation.

## Goal

Add frontend i18n framework support with initial English and Russian locale files.

The implementation must be extensible to future locales.

## Dependencies

Requires:

```text
TASK-O201 — i18n architecture/locale policy
```

## Decision

Use:

```text
i18next
react-i18next
```

Do not implement a custom lightweight dictionary unless dependency installation is blocked.

## Scope

Implement:

```text
i18next/react-i18next dependencies
i18n config
locale files
translation namespaces
fallback locale
I18nextProvider/app integration
basic translation helper usage
task-scoped frontend tests
```

Do not translate the entire app in this task.

## Locales

Initial:

```text
en
ru
```

Fallback:

```text
en
```

Future locale readiness:

```text
locale list is config-based
no binary en/ru branching
```

## Namespace structure

Use namespaces such as:

```text
common
navigation
auth
audits
profile
results
providers
errors
```

Adjust to project conventions.

## Tests

Frontend tests:

```text
i18n provider initializes
fallback locale works
known key renders in en
known key renders in ru
missing key behavior safe
adding another locale would not require logic branch
```

## Acceptance criteria

- `i18next` and `react-i18next` installed/configured.
- en and ru locale files exist.
- fallback locale works.
- i18n provider integrated.
- No raw content auto-translation implemented.
- Task-scoped frontend tests pass.
- TypeScript passes.

## Escalate if

- Project dependency policy rejects new i18n dependencies.
- Existing frontend framework has an established i18n solution.
- Installing packages conflicts with lockfile/package manager.

## Commands

```bash
cd apps/web
npm install i18next react-i18next
npm run typecheck
npm test -- <i18n setup tests>
```

Use the project package manager if not npm.

## Done means

The app has working i18next/react-i18next setup with en/ru files and safe fallback.
