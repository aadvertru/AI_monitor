# TASK-Q207 — Add Frontend PAA Query Generation Controls

## Goal

Add frontend controls that allow users to include People Also Ask questions when generating seed query suggestions.

This must integrate with existing seed query generation UI and preserve manual editing/removal.

---

## Scope

Implement:

```text
Use PAA checkbox/toggle
language/country controls if required
API payload extension
PAA suggestion append/dedup behavior
warnings/errors display
task-scoped frontend tests
```

---

## UI behavior

In Generate Seed Queries UI, add:

```text
[ ] Include People Also Ask questions
Language selector or inherited setting
Country selector or inherited setting
```

If PAA is unavailable/disabled, show safe disabled state or warning.

Do not call SerpApi directly from frontend.

---

## Append behavior

PAA suggestions should enter the same visible seed query list as other suggestions.

Rules:

```text
append unique suggestions
source=paa preserved
type preserved
user can edit text
user can delete suggestion before save
not persisted until save
total seed query limit respected
warnings shown
```

If source badges exist, show `PAA` source badge or equivalent.

---

## Domain interaction

If domain is unavailable:

```text
domain-based generation may be disabled/warned
PAA may still be allowed if it does not depend on domain
manual input remains available
```

Product may decide whether PAA seed query is based on brand name/description/query. Reflect backend contract.

---

## Tests

Frontend tests:

```text
PAA toggle appears
payload includes usePaa/language/country
PAA suggestions append to list
source=paa preserved
duplicates skipped
max 20 limit respected
warnings displayed
user can edit PAA suggestion
user can delete PAA suggestion
removed PAA suggestion not saved
PAA disabled/error state displayed safely
```

Safety tests:

```text
raw SerpApi errors not displayed
unsafe mocked fields not rendered
```

---

## Acceptance criteria

- PAA controls added to generation UI.
- PAA payload sent to backend.
- PAA suggestions render in seed query editor.
- PAA suggestions can be edited/deleted before save.
- Source metadata preserved in save payload.
- Dedup/limit behavior works.
- Safe warnings/errors displayed.
- Task-scoped frontend tests pass.
- TypeScript passes for touched files.

---

## Non-goals

- Do not implement backend PAA provider.
- Do not call SerpApi from frontend.
- Do not persist suggestions automatically.
- Do not redesign seed query editor broadly.
