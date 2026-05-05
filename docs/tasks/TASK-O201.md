# TASK-O201 — Define i18n Architecture and Locale Policy

## Goal

Define the i18n architecture and locale policy for the frontend.

This task is documentation/contract only. Do not change runtime code.

The implementation must start with English and Russian but support future languages beyond two locales.

---

## File to create

```text
docs/I18N_CONTRACT.md
```

---

## Required decisions

### 1. Supported initial locales

```text
en
ru
```

### 2. Future locale support

Document:

```text
The architecture must support adding more locales without changing app logic.
Do not hardcode binary en/ru behavior.
Use locale codes and translation files/namespaces.
```

### 3. What is translated

Translate:

```text
navigation
buttons
labels
status labels
validation messages
provider diagnostic labels
empty states
summary card titles
table headers
profile labels
tooltips
```

Do not translate:

```text
raw AI answers
seed queries
brand descriptions
source titles/snippets
user-entered content
model ids
provider raw data
```

### 4. Backend/frontend responsibility

Document:

```text
backend returns stable codes and data
frontend translates labels
backend does not return localized UI strings unless explicitly designed later
```

### 5. Locale persistence

Choose one:

```text
localStorage for MVP
user preference later
```

Recommended:

```text
localStorage now, optional profile preference later
```

### 6. Formatting

Document locale-aware formatting for:

```text
dates
times
numbers
percentages
```

Use browser Intl APIs or i18n library utilities.

---

## Acceptance criteria

- i18n contract doc exists.
- Initial locales en/ru documented.
- Future language support documented.
- Translation scope documented.
- Non-translated content documented.
- Backend/frontend responsibility documented.
- Locale persistence policy documented.
- Formatting policy documented.
- No runtime code changed.

---

## Non-goals

- Do not implement i18n framework.
- Do not translate UI.
- Do not change backend.
