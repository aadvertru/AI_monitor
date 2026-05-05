# TASK-S208 — Add Rerun Fact-Checking Frontend Action Stub

## Goal

Add frontend API client support and a minimal action hook for rerunning evaluation/fact-checking.

This prepares the Web5 button but does not require final Web5 UI implementation.

---

## Scope

Implement:

```text
frontend API client method for POST /audits/{id}/rerun-evaluation
mutation hook
safe loading/error handling
cache invalidation for summary/matrix
task-scoped frontend tests
```

If Web5 UI does not exist yet, expose hook/client only.

---

## Client method

Add:

```ts
rerunAuditEvaluation(auditId): Promise<RerunEvaluationResponse>
```

Response type equivalent to:

```ts
type RerunEvaluationResponse = {
  auditId: string | number
  evaluatedRuns: number
  skippedRuns: number
  status: string
  warnings?: string[]
}
```

---

## Cache invalidation

After success, invalidate/refetch:

```text
summary v2
answer matrix
audit detail/status if relevant
```

Use existing TanStack Query conventions.

---

## Safety

Do not display raw backend error body.

Do not expose raw evaluator/provider data.

---

## Tests

Frontend tests:

```text
client calls correct endpoint
mutation loading state works
success invalidates summary/matrix queries
warnings handled
safe error handled
```

---

## Acceptance criteria

- Rerun evaluation API client method exists.
- Mutation/hook exists.
- Success invalidates relevant result queries.
- Safe error handling works.
- No final Web5 UI required.
- Task-scoped frontend tests pass.
- TypeScript passes for touched files.

---

## Non-goals

- Do not implement final Web5 summary UI.
- Do not implement backend endpoint.
- Do not implement real evaluator.
- Do not change parser/scoring.
