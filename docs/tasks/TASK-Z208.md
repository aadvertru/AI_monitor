# TASK-Z208 — Add Audit Comparison and Trends UI

## Goal

Add a first UI for comparing audits and viewing trends over time.

---

## Scope

Implement:

```text
comparison candidate selector
overall delta display
model delta display
trend chart/table
source/concept/competitor change summaries
loading/error/empty states
task-scoped frontend tests
```

---

## UI behavior

### Comparison

User can select a previous audit to compare with current audit.

Show:

```text
overall metric changes
model-level changes
source domain changes
concept changes
competitor changes
warnings for missing data
```

### Trends

Show simple chart/table of historical points:

```text
mentionability L1/L2 over time
accuracy L1/L2 over time if available
```

Use existing chart library if available.

---

## Tests

Frontend tests:

```text
candidate selector renders
selecting candidate loads comparison
overall deltas render
missing data warnings render
trend points render
empty state for no previous audits
source/concept/competitor changes render
i18n labels
```

---

## Acceptance criteria

- Comparison UI exists.
- Trends UI exists.
- Empty/missing-data states safe.
- No frontend metric recomputation beyond display formatting.
- Task-scoped frontend tests pass.
- TypeScript passes.

---

## Non-goals

- Do not implement backend endpoints.
- Do not add advanced analytics.
- Do not redesign dashboard.
