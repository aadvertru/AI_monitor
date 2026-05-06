# i18n Contract

This document defines the frontend internationalization policy for AI Brand
Visibility Monitor.

## Initial Locales

The initial supported locales are:

- `en` - English
- `ru` - Russian

English is the fallback locale.

## Future Locale Support

The frontend architecture must support adding more locales without changing app
logic. Locale behavior must be driven by locale codes, configured locale lists,
translation files, and namespaces.

Do not hardcode binary `en`/`ru` behavior in components or business logic.
Adding a future locale should normally require:

- adding the locale to the supported locale config
- adding translation resources
- adding optional locale-specific tests

## Translation Scope

Translate user interface text:

- navigation
- buttons
- labels
- status labels
- validation messages
- provider diagnostic labels
- empty states
- summary card titles
- table headers
- profile/account labels
- tooltips

Do not translate user, provider, or raw content:

- raw AI answers
- seed query text
- brand descriptions
- source titles/snippets
- user-entered content
- model ids
- provider ids
- provider raw data

## Backend and Frontend Responsibilities

The backend returns stable data, codes, enum values, and safe diagnostics.

The frontend translates display labels from those stable codes. Backend response
fields should not become localized UI strings unless a future task explicitly
designs backend localization.

Examples:

- backend returns `status="completed"`; frontend displays a localized label
- backend returns `code="NO_API_KEY"`; frontend displays a localized diagnostic
- backend returns `model_id="openai/gpt-4o-mini"`; frontend displays the model id
  as raw data

## Locale Persistence

MVP locale persistence uses `localStorage`.

A profile/user preference may be added later. Until then, the browser-stored
locale is local-device preference only and must fall back safely to `en` when
missing or invalid.

## Formatting

Locale-aware formatting must use browser `Intl` APIs or the i18n library's
formatting utilities for:

- dates
- times
- numbers
- percentages

Backend date/time and numeric values remain stable machine-readable values. The
frontend formats values only for display and must handle `null`/`undefined`
safely.

## Safety

i18n must not cause raw provider data, prompts, headers, API keys, or stack
traces to become visible. Translation files must contain UI copy only, not
secrets or raw provider payloads.
