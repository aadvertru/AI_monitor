# TASK-M207 — Update Frontend API Types and Wire Mapping for Model Targets

## Status

Ready for implementation after TASK-M203.

## Goal

Update frontend API types and client payload mapping to support canonical backend `model_targets`.

This task prepares frontend for the model target selector but does not implement the selector UI yet.

---

## Dependencies

Requires:

```text
TASK-M203
```

Recommended:

```text
TASK-M206 if frontend estimate API types are also touched
```

---

## Scope

Implement:

```text
AuditTarget TypeScript domain types
snake_case backend wire types
camelCase frontend internal types
API mapping functions
audit create/update payload support
audit detail response parsing
legacy compatibility typing
task-scoped frontend tests
```

---

## Critical wire-shape rule

Backend wire field is:

```text
model_targets
```

Frontend internal/domain type may be:

```text
modelTargets
```

The API client must explicitly map:

```text
modelTargets → model_targets
model_targets → modelTargets
```

Do not send camelCase `modelTargets` directly to backend unless the backend explicitly accepts camelCase.

---

## Types

Add frontend internal type equivalent to:

```ts
type ScdlLevel = "L1" | "L2"

type AuditTarget = {
  id?: string | number
  aiFamily: string
  executionProvider: string
  modelProvider: string
  modelId: string
  displayName: string
  level: ScdlLevel
  gateway?: boolean
  gatewayL2Experimental?: boolean
}
```

Add backend wire type equivalent to:

```ts
type AuditTargetWire = {
  id?: string | number
  ai_family: string
  execution_provider: string
  model_provider: string
  model_id: string
  display_name: string
  level: "L1" | "L2"
  gateway?: boolean
  gateway_l2_experimental?: boolean
}
```

Use project naming conventions.

---

## API client behavior

- create audit can send internal `modelTargets`, mapped to wire `model_targets`
- update audit can send internal `modelTargets`, mapped to wire `model_targets`
- detail/list can parse wire `model_targets` into internal `modelTargets`
- legacy fields still typed if used by existing UI

Do not break current create audit flow.

---

## Tests

Frontend/API tests:

```text
create payload with modelTargets maps to request body model_targets
actual request body does not contain modelTargets unless backend supports it
update payload maps to model_targets
detail response model_targets parses to modelTargets
legacy audit response still parses
L1/L2 values typed
gateway_l2_experimental maps to gatewayL2Experimental
gatewayL2Experimental maps to gateway_l2_experimental
missing model_targets safe if legacy fields exist
mixed legacy/canonical payload not produced by client
```

Use mocked fetch/API client assertions to inspect the actual outgoing JSON body.

---

## Acceptance criteria

- Frontend internal types support model targets.
- Backend wire types support snake_case model_targets.
- API client maps camelCase internal fields to snake_case wire fields.
- API client parses snake_case response into internal types.
- Existing create audit UI not broken.
- Legacy audit detail still safe.
- Task-scoped frontend tests pass.
- TypeScript passes.

---

## Escalate if

- Existing API client has no mapping layer and would require broad refactor.
- Backend accepts only camelCase despite documented snake_case.
- Existing create audit form depends directly on wire types and cannot be safely separated in one task.

## Commands

Use task-scoped commands. Adjust exact paths to the repository layout.

Suggested frontend checks:

```bash
cd apps/web
npm run typecheck
npm test -- <task-specific tests>
```

If the project uses a different test runner, use the project convention.

Do not fix unrelated frontend failures inside this task.


## Done means

Frontend tests prove actual backend request JSON uses `model_targets`, response parsing supports `model_targets`, and internal UI code can use `modelTargets`.

---

## Non-goals

- Do not implement target selector UI.
- Do not implement model catalog.
- Do not change backend.
- Do not redesign create audit page.
