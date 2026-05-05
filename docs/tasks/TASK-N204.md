# TASK-N204 — Add Frontend Model Catalog API Types and Hook

## Goal

Add frontend API types and query hook/client method for `GET /model-catalog`.

Do not implement the audit target selector UI yet.

---

## Scope

Implement:

```text
TypeScript model catalog types
API client method
TanStack Query hook if project convention uses hooks
loading/error handling primitives
task-scoped frontend tests
```

---

## Types

Add types equivalent to:

```ts
type ModelCatalogModel = {
  modelId: string
  displayName: string
  modelProvider: string
  executionProvider: "openrouter" | string
  aiFamily: string
  supportsL1: boolean
  supportsL2Gateway: boolean
  l2Experimental: boolean
  isAllowed: boolean
}

type ModelCatalogFamily = {
  id: string
  label: string
  models: ModelCatalogModel[]
}

type ModelCatalogResponse = {
  families: ModelCatalogFamily[]
  cachedAt?: string | null
  expiresAt?: string | null
  warnings?: string[]
}
```

Use project naming conventions.

---

## Tests

Frontend/API tests:

```text
client calls /model-catalog
parses families/models
handles empty catalog
handles warnings
handles missing optional fields
loading/error states exposed by hook
```

---

## Acceptance criteria

- Frontend API client supports model catalog.
- Types exist.
- Hook/client handles empty/warning states.
- No selector UI implemented yet.
- Task-scoped frontend tests pass.
- TypeScript passes.

---

## Non-goals

- Do not implement target selector UI.
- Do not change audit create page.
- Do not change backend endpoint.
