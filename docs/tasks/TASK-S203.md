# TASK-S203 — Add AnswerEvaluation Model and Migration

## Goal

Add persistent storage for answer evaluations.

Each evaluated run/cell should be able to store a verdict, rationale, confidence, version, and timestamp.

---

## Scope

Implement:

```text
AnswerEvaluation DB model/migration
Pydantic/DTO schemas
repository/service helpers
task-scoped backend tests
```

Do not implement evaluator logic in this task.

---

## Suggested fields

```text
id
audit_id
run_id
query_id
target_id
verdict
rationale
confidence
evaluation_version
evaluated_at
created_at
updated_at
```

Optional fields:

```text
evaluator_provider
evaluator_model
facts_version
```

---

## Verdict enum

Use:

```text
correct
partial
incorrect
unknown
not_applicable
```

---

## Rules

- One current evaluation per run/cell unless project supports history.
- If history is needed, mark previous evaluations as superseded.
- Rerun evaluation should update/replace current evaluation later.
- Rationale must be safe text.
- Do not store raw evaluator prompts/responses in normal evaluation fields.

---

## Tests

Backend tests:

```text
migration creates table/fields
valid verdicts accepted
invalid verdict rejected
evaluation can link to run/query/target
confidence bounds enforced if applicable
evaluation_version required
rationale optional or required according to contract
legacy runs without evaluation still work
```

Safety tests:

```text
raw prompt/response fields not part of frontend DTO
API keys/secrets not serializable in evaluation DTO
```

---

## Acceptance criteria

- AnswerEvaluation model exists.
- Migration exists if project uses migrations.
- Verdict enum exists.
- Evaluation can link to audit run/cell.
- Legacy runs without evaluations remain valid.
- Task-scoped backend tests pass.
- Touched-file ruff passes.

---

## Non-goals

- Do not implement evaluator service.
- Do not implement rerun endpoint.
- Do not update UI.
- Do not change parser/scoring.
- Do not store raw evaluator prompts/responses.
