# TASK-R206 — Add Frontend API Types for Results v2

## Goal

Add frontend API types and client methods for summary v2, answer matrix, source-domain, and concepts/competitor placeholder contracts.

This task does not implement Web5/Web6/Web7 UI yet.

---

## Scope

Implement:

```text
frontend TypeScript types
API client methods/hooks
safe parsing/null handling
task-scoped frontend tests
```

Do not implement new result UI screens in this task.

---

## Client methods

Add methods equivalent to:

```ts
getAuditSummaryV2(auditId)
getAuditAnswerMatrix(auditId)
getAuditSourceDomains(auditId)
```

Use existing API client conventions.

---

## Types

Add types for:

```text
SummaryV2
ModelSummary
AnswerMatrix
AnswerMatrixColumn
AnswerMatrixRow
AnswerMatrixCell
CellEvaluationPlaceholder
SourceDomainGroup
Concept
CompetitorCandidate
```

Evaluation may be null/unknown until Phase S.

---

## Null/legacy handling

Types and parsing should tolerate:

```text
evaluation = null
accuracy = null
source domains empty
concepts empty
competitor_candidates empty
legacy missing fields if endpoint not yet available
```

Do not crash when data is partial.

---

## Tests

Frontend/API tests:

```text
client calls correct endpoints
summary v2 response parsed
answer matrix response parsed
source domains response parsed
null evaluation handled
missing optional fields handled
OpenRouter gateway metadata typed
provider_error typed
```

---

## Acceptance criteria

- Frontend API client supports results v2 endpoints.
- TypeScript types exist.
- Null/empty states are type-safe.
- Existing results UI is not broken.
- No Web5/Web6/Web7 UI implemented yet.
- Task-scoped frontend tests pass.
- TypeScript passes for touched files.

---

## Non-goals

- Do not implement summary UI.
- Do not implement matrix UI.
- Do not implement source-domain UI.
- Do not implement evaluation.
- Do not change backend contracts.
