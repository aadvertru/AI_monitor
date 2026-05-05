# TASK-Z207 — Add Frontend API Types for Comparison and Trends

## Goal

Add frontend API types and client methods for audit comparison and trend endpoints.

Do not implement final UI yet.

---

## Scope

Implement:

```text
comparison API types
trend API types
client methods/hooks
safe null handling
task-scoped frontend tests
```

---

## Client methods

Add methods equivalent to:

```ts
getComparisonCandidates(auditId)
compareAudits(auditId, previousAuditId)
getBrandAuditTrends(brandId)
```

---

## Types

Add types for:

```text
ComparisonCandidate
AuditComparison
MetricDelta
ModelDelta
SourceDomainChange
ConceptChange
CompetitorChange
AuditTrendPoint
```

---

## Tests

Frontend/API tests:

```text
client calls correct endpoints
candidate response parsed
comparison response parsed
trend response parsed
null accuracy safe
missing optional fields safe
warnings handled
```

---

## Acceptance criteria

- Frontend comparison/trend types exist.
- API client methods exist.
- Hooks exist if project convention uses hooks.
- Null/missing data safe.
- Task-scoped frontend tests pass.
- TypeScript passes.

---

## Non-goals

- Do not implement comparison UI.
- Do not implement trend charts.
- Do not change backend.
