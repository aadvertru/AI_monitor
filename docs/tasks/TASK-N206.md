# TASK-N206 — Integrate Model Target Selector with Audit Create/Edit

## Status

Ready for implementation.

## Goal

Wire the audit target selector into audit create/edit forms and persist selected canonical model targets.

## Dependencies

Requires:

```text
TASK-M207 — frontend wire mapping for model_targets
TASK-N205 — selector component
TASK-M203 — backend model_targets DTO
```

## Critical wire-shape rule

Frontend internal state may use:

```text
modelTargets
```

Backend wire payload must use:

```text
model_targets
```

The API client must map internal camelCase to backend snake_case. Tests must inspect actual outgoing request JSON.

## Scope

Implement:

```text
create audit payload uses wire model_targets
edit audit loads wire model_targets into internal modelTargets
edit audit saves changed targets as wire model_targets
legacy fallback if old audit has providers/scdl_level
validation messages
task-scoped frontend tests
```

## Rules

- Submit `model_targets` to backend.
- Do not submit both `model_targets` and legacy `providers/scdl_level`.
- Legacy audits should load into selector if conversion is possible.
- If conversion is not possible, show safe fallback state.
- Empty target selection blocks save.

## Tests

Frontend tests:

```text
create audit with internal modelTargets sends request body model_targets
actual request body does not contain modelTargets
same model L1+L2 sends two wire targets
edit audit loads backend model_targets into selector
edit audit saves updated model_targets
legacy audit fields convert/load safely
empty target selection validation
backend validation error shown safely
mixed legacy/canonical payload not produced by client
```

## Acceptance criteria

- Create audit sends `model_targets`.
- Edit audit supports `model_targets`.
- Legacy audits remain usable.
- Validation works.
- Existing non-target fields unaffected.
- Task-scoped frontend tests pass.
- TypeScript passes.

## Escalate if

- Existing API client cannot map internal/wire shapes without broad refactor.
- Backend currently expects camelCase despite contract.
- Legacy audit conversion cannot be represented in selector.

## Commands

```bash
cd apps/web
npm run typecheck
npm test -- <audit create/edit model target tests>
```

## Done means

Create/edit forms use canonical targets and outgoing request bodies are proven to contain backend `model_targets`.
