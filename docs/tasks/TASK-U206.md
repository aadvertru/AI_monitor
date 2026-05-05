# TASK-U206 — Add Concepts and Competitors API Fields

## Goal

Expose concepts and competitor candidates through backend result/detail/summary APIs.

This task provides data to frontend but does not implement final UI sections yet.

---

## Scope

Implement:

```text
concepts API serialization
competitor_candidates API serialization
evidence summaries
backward-compatible legacy fields
task-scoped backend/API tests
```

---

## API surfaces

Add fields where appropriate:

```text
GET /audits/{id}/summary-v2
GET /audits/{id}/answer-matrix
GET /audits/{id}/results
GET /audits/{id}/results/{run_id} if exists
```

Use project conventions.

---

## Response behavior

Concepts:

```json
"concepts": [
  {
    "text": "children's ballet classes",
    "category": "service",
    "count": 5,
    "evidence_count": 5
  }
]
```

Competitor candidates:

```json
"competitor_candidates": [
  {
    "name": "Another Ballet Studio",
    "domain": "example.com",
    "confidence": 0.82,
    "evidence_type": "comparison_context",
    "evidence_count": 3
  }
]
```

Evidence details may be included in detail endpoint or expandable API, not necessarily summary.

---

## Backward compatibility

Do not break current frontend.

If legacy `competitors` field exists:

```text
keep it temporarily
add concepts and competitor_candidates
document deprecation in code/docs if appropriate
```

---

## Tests

Backend/API tests:

```text
concepts returned
competitor_candidates returned
empty arrays safe
legacy competitors field still available if needed
evidence summaries safe
auth/ownership enforced
raw provider responses not exposed
generic phrases not returned as competitors
```

---

## Acceptance criteria

- APIs expose concepts and competitor_candidates.
- Empty states safe.
- Existing frontend not broken.
- Auth/ownership enforced.
- Raw provider data not exposed.
- Task-scoped backend/API tests pass.
- Touched-file ruff passes.

---

## Non-goals

- Do not implement frontend concepts/competitors UI.
- Do not remove legacy field yet.
- Do not change parser/scoring.
- Do not use LLM classifier.
