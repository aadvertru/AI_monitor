# TASK-Z204 — Add Audit Comparison Backend Endpoint

## Goal

Add backend endpoint for comparing two audits.

---

## Endpoint

```http
GET /audits/{id}/compare?previous_audit_id=...
```

---

## Comparison sections

Return:

```text
overall metric deltas
model summary deltas
query/target coverage differences
source domain changes
competitor candidate changes
concept changes
diagnostics/missing-data notes
```

For this task, source/concept/competitor changes may be basic if full endpoints exist.

---

## Rules

- Requires auth.
- User must own both audits.
- Audits should belong to same brand/domain or return safe warning/error.
- Missing models/queries handled.
- Do not expose raw provider responses.

---

## Response sketch

```json
{
  "current_audit_id": 10,
  "previous_audit_id": 7,
  "overall_delta": {
    "mentionability_l1_delta": 5,
    "mentionability_l2_delta": -2,
    "accuracy_l1_delta": null
  },
  "model_deltas": [],
  "source_domain_changes": [],
  "competitor_changes": [],
  "concept_changes": [],
  "warnings": []
}
```

---

## Tests

Backend/API tests:

```text
auth required
ownership for both audits
different brand warning/rejection
overall deltas calculated
missing model handled
missing evaluation handled
legacy audit handled
no raw provider data exposed
```

---

## Acceptance criteria

- Audit comparison endpoint exists.
- Auth/ownership enforced.
- Overall deltas calculated.
- Missing data safe.
- Response safe.
- Task-scoped backend/API tests pass.
- Touched-file ruff passes.

---

## Non-goals

- Do not implement frontend comparison UI.
- Do not implement trend charts.
- Do not redesign metrics.
