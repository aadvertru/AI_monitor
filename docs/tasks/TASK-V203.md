# TASK-V203 — Implement Web5 Header and Tested Scope Section

## Goal

Implement the top section of the Web5-style summary page.

This includes audit metadata, action placeholders, and the collapsible “What was tested” section.

---

## Scope

Implement:

```text
audit header
audit metadata summary
action button area placeholders
"What was tested" collapsible section
task-scoped frontend tests
```

Do not implement metric cards or model summary yet.

---

## Header content

Display available data such as:

```text
audit name/title
created or completed date/time
audit status
query count
target/model count
levels tested
```

Use locale-aware date/number formatting if i18n formatting utilities exist.

---

## Actions area

Show action buttons according to availability:

```text
Rerun fact-checking
DOCX
Excel
Repeat audit
```

In this task, buttons may be disabled/placeholders unless the action is already implemented.

Button states:

```text
enabled
disabled
loading if action already wired
tooltip/copy for unavailable exports
```

---

## Tested scope collapsible

Show:

```text
number of questions/queries
number of models/targets
levels included
model/AI families included
OpenRouter L2 experimental indicator if present
```

The section should be collapsible.

---

## i18n

All static labels must use translation keys.

Do not translate model ids, audit title, or query text.

---

## Tests

Frontend tests:

```text
header renders audit title/status
date/number formatting used where applicable
query/target/level counts render
tested scope expands/collapses
action placeholders render
disabled export buttons state works
OpenRouter L2 experimental marker renders when present
i18n labels render
```

---

## Acceptance criteria

- Header section implemented.
- Tested scope collapsible implemented.
- Action placeholders render safely.
- Counts and metadata render from backend data.
- i18n/static labels handled.
- Responsive layout acceptable.
- Task-scoped frontend tests pass.
- TypeScript passes.

---

## Non-goals

- Do not implement actual export generation.
- Do not implement metric cards.
- Do not implement model summary table.
- Do not change backend.
- Do not calculate backend metrics in frontend.
