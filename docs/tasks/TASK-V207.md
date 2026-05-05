# TASK-V207 — Add Web5 Export and Repeat Audit Action Placeholders

## Goal

Add safe action placeholders for DOCX export, Excel export, and Repeat Audit on the Web5 summary page.

This task does not implement actual export generation unless export endpoints already exist.

---

## Scope

Implement:

```text
DOCX button placeholder
Excel button placeholder
Repeat audit button placeholder or existing action wiring
disabled/loading states
tooltips/help text
task-scoped frontend tests
```

---

## Behavior

### DOCX / Excel

If export endpoints do not exist:

```text
buttons visible but disabled
show tooltip/copy: Export will be available later
```

If endpoints already exist and are stable:

```text
wire download action according to existing API
```

Do not create export backend in this task.

### Repeat audit

If duplicate/rerun audit action exists:

```text
wire to existing action
```

Otherwise:

```text
show disabled placeholder
```

---

## i18n

Translate labels and tooltips.

---

## Tests

Frontend tests:

```text
DOCX button renders
Excel button renders
Repeat audit button renders
disabled placeholder state works
tooltip/help copy present
existing action wiring works if enabled
no raw errors displayed
```

---

## Acceptance criteria

- Action buttons render.
- Unavailable actions are safely disabled.
- Existing actions wired only if already implemented.
- No backend export implementation added.
- i18n labels used.
- Task-scoped frontend tests pass.
- TypeScript passes.

---

## Non-goals

- Do not implement DOCX/Excel generation.
- Do not implement duplicate audit backend.
- Do not change audit pipeline.
- Do not redesign summary layout.
