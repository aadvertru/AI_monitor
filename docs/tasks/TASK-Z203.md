# TASK-Z203 — Add Comparison Candidates Endpoint

## Goal

Add an endpoint that lists previous audits suitable for comparison with the current audit.

---

## Endpoint

```http
GET /audits/{id}/comparison-candidates
```

---

## Rules

Candidates should match:

```text
same owner
same brand or normalized domain
terminal status
has usable results/snapshot
not the current audit
```

Sort by most recent first.

---

## Response

```json
{
  "audit_id": 10,
  "candidates": [
    {
      "audit_id": 7,
      "created_at": "...",
      "completed_at": "...",
      "status": "completed",
      "query_count": 20,
      "target_count": 6,
      "summary": {
        "mentionability_l1": 25,
        "mentionability_l2": 9
      }
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
same brand candidates returned
different owner excluded
current audit excluded
non-terminal audits excluded
no-usable-data audits excluded if policy says so
sorted newest first
legacy audits safe
```

---

## Acceptance criteria

- Comparison candidates endpoint exists.
- Auth/ownership enforced.
- Candidate filtering works.
- Response safe.
- Task-scoped backend tests pass.
- Touched-file ruff passes.

---

## Non-goals

- Do not implement comparison diff endpoint.
- Do not implement UI.
- Do not create snapshots if handled elsewhere.
