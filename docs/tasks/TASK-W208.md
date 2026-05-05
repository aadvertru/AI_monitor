# TASK-W208 — Add Matrix Responsive and Accessibility Polish

## Goal

Polish the matrix for usability on desktop and mobile/tablet, including accessibility basics.

---

## Scope

Implement:

```text
responsive horizontal scroll
sticky headers/columns if practical
mobile-safe controls
keyboard-accessible expand/filter controls
ARIA labels where needed
task-scoped frontend tests
```

---

## Requirements

- Matrix remains usable with many columns.
- Question column readable.
- No required hover-only controls.
- Expand buttons accessible by keyboard.
- Filter controls accessible by labels.
- Color is not the sole indicator for verdict/status.

---

## Tests

Frontend tests:

```text
expand buttons accessible by role/name
filter controls have labels
no hover-only required for expand
long content does not break layout
mobile viewport smoke if framework supports it
verdict text/icon present beyond color
```

---

## Acceptance criteria

- Matrix usable with many columns.
- Mobile/tablet behavior acceptable.
- Required controls are not hover-only.
- Basic accessibility covered.
- Task-scoped frontend tests pass.
- TypeScript passes.

---

## Non-goals

- Do not redesign entire app layout.
- Do not virtualize large tables unless required.
- Do not change backend.
