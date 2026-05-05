# TASK-N205 — Add Audit Target Selector UI

## Goal

Add the Create/Edit Audit UI control for selecting AI families, models, and L1/L2 levels.

This UI should use the backend model catalog and produce canonical `modelTargets`.

---

## Scope

Implement:

```text
audit target selector component
default first AI family block
plus button to add AI family block
model multiselect per family
L1/L2 toggles per selected model
remove family/model actions
basic validation
task-scoped frontend tests
```

Do not change backend validation in this task.

---

## UX behavior

### Initial state

When user opens create audit:

```text
show one AI family block by default, e.g. ChatGPT
show model multiselect for that family
```

### Add family

User clicks plus button:

```text
another AI family selector block appears
user selects family, e.g. Gemini
then selects one or more models
then chooses L1/L2 toggles per model
```

### L1/L2 toggles

Rules:

```text
L1 available for supported text models
L2 shown only if backend catalog says supported/allowed
OpenRouter L2 marked experimental
disabled toggles have reason/tooltip if possible
```

### Output

Selector outputs canonical model targets:

```text
one selected model with L1+L2 => two modelTargets
```

---

## Tests

Frontend tests:

```text
default family block renders
model catalog loading state
model catalog error state
model multiselect works
plus button adds another family block
remove family works
L1/L2 toggles create correct targets
OpenRouter L2 experimental marker shown
disabled unsupported L2 cannot be selected
duplicate target prevented
empty selection validation
```

---

## Acceptance criteria

- Target selector component exists.
- Uses model catalog data.
- Plus-button family flow works.
- Model multiselect works.
- L1/L2 toggles work.
- Selector outputs canonical modelTargets.
- Experimental L2 is visibly marked.
- Task-scoped frontend tests pass.
- TypeScript passes.

---

## Non-goals

- Do not implement backend catalog endpoint.
- Do not change audit save integration yet if separated.
- Do not implement cost estimate beyond local run count if not available.
- Do not redesign entire create page.
