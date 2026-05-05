# TASK-U202 — Add Concept and CompetitorCandidate Models/DTOs

## Goal

Add backend models/DTOs for concepts and competitor candidates.

This task creates storage/API structures but does not implement extraction logic yet.

---

## Scope

Implement:

```text
Concept model/table or equivalent
CompetitorCandidate model/table or equivalent
Evidence DTO/model if needed
Pydantic schemas
migration if applicable
task-scoped backend tests
```

---

## Concept fields

Suggested:

```text
id
audit_id
run_id optional
query_id optional
target_id optional
text
category
count
evidence_count
created_at
updated_at
```

### CompetitorCandidate fields

Suggested:

```text
id
audit_id
name
domain nullable
confidence
evidence_type
evidence_count
created_at
updated_at
```

Evidence may be stored as separate table or JSON depending on project conventions.

Evidence should include:

```text
query_id
run_id
target_id
answer_excerpt
level
model_id
execution_provider
```

---

## Rules

- Concepts and competitor candidates must be audit-owned data.
- Deleting audit should delete these records.
- Do not delete shared Brand.
- Empty concepts/competitors arrays are valid.
- Confidence must be bounded if numeric, e.g. 0..1.

---

## Tests

Backend tests:

```text
migration creates models
concept can be created
competitor candidate can be created
evidence can be stored
confidence validation
audit ownership relation
audit delete removes owned records if delete behavior exists
empty arrays safe
```

---

## Acceptance criteria

- Concept storage/DTO exists.
- CompetitorCandidate storage/DTO exists.
- Evidence can be represented.
- Audit ownership relation exists.
- Empty states safe.
- Migration exists if project uses migrations.
- Task-scoped backend tests pass.
- Touched-file ruff passes.

---

## Non-goals

- Do not implement extraction.
- Do not update UI.
- Do not change parser/scoring.
- Do not run LLM classification.
