# TASK-T205 — Add Frontend Source Domains API Types and Client

## Goal

Add frontend API types and client method for Source Intelligence v2 domain groups.

This task does not implement the final source-domain UI yet.

---

## Scope

Implement:

```text
TypeScript types
API client method
TanStack Query hook if project convention uses hooks
safe null/empty handling
task-scoped frontend tests
```

---

## Client method

Add:

```ts
getAuditSourceDomains(auditId): Promise<SourceDomainsResponse>
```

Use existing API client conventions.

---

## Types

Add types equivalent to:

```ts
type SourceDomainUrl = {
  url: string
  normalizedUrl?: string | null
  title?: string | null
  snippet?: string | null
  queryId?: string | number | null
  targetId?: string | number | null
  modelId?: string | null
  executionProvider?: string | null
  level?: "L1" | "L2" | string
  sourceType?: string | null
}

type SourceDomainGroup = {
  domain: string
  sourceCount: number
  uniqueUrlCount: number
  queryCount?: number
  targetCount?: number
  levels?: string[]
  models?: string[]
  providers?: string[]
  urls: SourceDomainUrl[]
}

type SourceDomainsResponse = {
  auditId: string | number
  domains: SourceDomainGroup[]
  warnings?: string[]
}
```

Use project naming conventions.

---

## Tests

Frontend/API tests:

```text
client calls correct endpoint
parses empty domains
parses domain group
parses URL evidence
handles missing optional fields
handles warnings
does not render/keep unsafe raw fields if mapper strips them
```

---

## Acceptance criteria

- Frontend source-domain types exist.
- API client method exists.
- Empty/warning states type-safe.
- Existing sources UI not changed yet.
- Task-scoped frontend tests pass.
- TypeScript passes for touched files.

---

## Non-goals

- Do not implement source-domain UI.
- Do not change backend endpoint.
- Do not implement filtering UI.
- Do not redesign sources tab.
