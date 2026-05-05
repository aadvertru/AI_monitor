# TASK-Y203 — Add Audit Run Estimate API

## Goal

Add an API endpoint or service for estimating the number of provider runs before an audit starts.

This helps users understand audit size before execution.

---

## Scope

Implement:

```text
run estimate service/API
query_count × target_count estimate
cap validation response
task-scoped backend/API tests
```

---

## Suggested endpoint

```http
POST /audits/estimate
```

Request may include draft audit payload:

```json
{
  "seed_query_items": [],
  "model_targets": []
}
```

Response:

```json
{
  "query_count": 20,
  "target_count": 6,
  "estimated_runs": 120,
  "over_cap": true,
  "cap": 100,
  "warnings": []
}
```

If project prefers no endpoint, expose estimate in create/update validation only. Document choice.

---

## Rules

- Backend is source of truth.
- Frontend estimate can be local, but backend validation must enforce caps.
- Legacy providers/scdl payloads should be estimable.
- No provider calls are made.

---

## Tests

Backend/API tests:

```text
estimate empty draft
estimate one query one target
estimate multiple queries/targets
over cap flagged
legacy payload estimate
invalid target payload safe
auth if endpoint requires login
no provider calls
```

---

## Acceptance criteria

- Run estimate service/API exists.
- Estimate uses query_count × target_count.
- Caps reflected.
- No provider calls performed.
- Task-scoped backend/API tests pass.
- Touched-file ruff passes.

---

## Non-goals

- Do not implement cost estimate.
- Do not implement frontend UI.
- Do not implement billing.
