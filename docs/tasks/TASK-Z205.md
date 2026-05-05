# TASK-Z205 — Add Visibility and Accuracy Trend Endpoint

## Goal

Add backend endpoint for visibility and accuracy trends across audits for a brand.

---

## Endpoint

```http
GET /brands/{brand_id}/audit-trends
```

or project-equivalent route.

---

## Metrics

Return time series for:

```text
mentionability_l1
mentionability_l2
accuracy_l1
accuracy_l2
run_count
target_count
query_count
```

Accuracy may be null if evaluation unavailable.

---

## Rules

- Requires auth.
- User must own brand/audits.
- Include terminal audits only.
- Sort chronologically.
- Legacy audits handled safely.

---

## Response sketch

```json
{
  "brand_id": 1,
  "points": [
    {
      "audit_id": 7,
      "completed_at": "...",
      "mentionability_l1": 25,
      "mentionability_l2": 9,
      "accuracy_l1": null,
      "accuracy_l2": null
    }
  ]
}
```

---

## Tests

Backend/API tests:

```text
auth required
ownership enforced
only terminal audits included
chronological order
missing accuracy safe
legacy audits safe
no raw data exposed
```

---

## Acceptance criteria

- Trend endpoint exists.
- Visibility trend returned.
- Accuracy trend returned/null-safe.
- Auth/ownership enforced.
- Task-scoped backend tests pass.
- Touched-file ruff passes.

---

## Non-goals

- Do not implement frontend charts.
- Do not calculate new scoring methodology.
- Do not include non-terminal audits unless explicitly decided.
