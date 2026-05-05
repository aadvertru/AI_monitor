# TASK-V208 — Add Web5 Summary Responsive and State Polish

## Goal

Polish the Web5 summary page for responsive layout, partial/failed audit states, and accessibility.

---

## Scope

Implement:

```text
responsive layout
mobile/tablet behavior
partial/failed audit messages
provider diagnostics display
accessibility basics
task-scoped frontend tests
```

---

## States to handle

```text
completed audit
partial audit
failed audit
audit with no results
audit without evaluation
audit with provider diagnostics
audit with only L1
audit with only L2
audit with OpenRouter experimental L2
```

---

## Responsive behavior

Ensure:

```text
summary cards wrap cleanly
model summary table scrolls or converts to cards
action buttons remain accessible
collapsible tested-scope section usable on mobile
no hover-only controls
```

---

## Accessibility

At minimum:

```text
buttons have accessible names
collapsible section has accessible state
tables have headings
color is not sole indicator for deltas/status
keyboard navigation works for buttons/collapse
```

---

## Tests

Frontend tests:

```text
partial audit message renders
failed audit message renders
no evaluation state renders
provider diagnostics render
mobile layout smoke if testing framework supports viewport
buttons accessible by role/name
collapsible state accessible
```

---

## Acceptance criteria

- Web5 summary handles completed/partial/failed/no-data states.
- Layout works on mobile/tablet/desktop.
- Required actions accessible without hover.
- Provider diagnostics displayed safely.
- Accessibility basics covered.
- Task-scoped frontend tests pass.
- TypeScript passes.

---

## Non-goals

- Do not implement new backend endpoints.
- Do not implement exports.
- Do not implement matrix UI.
- Do not redesign entire app shell.
