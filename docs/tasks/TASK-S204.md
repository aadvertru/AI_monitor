# TASK-S204 — Add Evaluation Service Interface and Mock Evaluator

## Goal

Add an evaluation service interface and deterministic/mock evaluator for tests and development.

This prepares the evaluation pipeline without requiring real LLM-as-judge calls.

---

## Scope

Implement:

```text
AnswerEvaluator interface
MockAnswerEvaluator
evaluation input/output DTOs
safe evaluation service wrapper
task-scoped backend tests
```

Do not add real evaluator provider calls yet.

---

## Evaluation input

Suggested input:

```python
AnswerEvaluationInput(
    audit_id: int,
    run_id: int,
    query_text: str,
    answer_text: str,
    brand_facts: list[BrandFact],
    level: str,
    model_id: str,
)
```

Do not include raw provider response.

---

## Evaluation output

```python
AnswerEvaluationResult(
    verdict: AnswerEvaluationVerdict,
    rationale: str | None,
    confidence: float | None,
    evaluation_version: str,
)
```

---

## Mock evaluator behavior

Create deterministic rules for tests, for example:

```text
answer contains marker "[CORRECT]" → correct
answer contains marker "[PARTIAL]" → partial
answer contains marker "[INCORRECT]" → incorrect
empty answer → unknown or not_applicable
```

Use whatever is least invasive and predictable.

---

## Safety

- Do not log full answer text by default.
- Do not log brand description.
- Do not expose raw prompts/responses.
- No real LLM calls in CI.

---

## Tests

Backend tests:

```text
mock evaluator returns correct verdict
mock evaluator returns partial verdict
mock evaluator returns incorrect verdict
mock evaluator handles empty answer
evaluation output is JSON-safe
evaluation_version present
no raw provider response required
```

---

## Acceptance criteria

- Evaluation interface exists.
- Mock evaluator exists.
- Mock evaluator deterministic.
- No real evaluator calls in CI.
- Service input uses normalized answer text, not raw provider response.
- Task-scoped backend tests pass.
- Touched-file ruff passes.

---

## Non-goals

- Do not implement real LLM evaluator.
- Do not add rerun endpoint.
- Do not update summary/matrix endpoints yet.
- Do not change parser/scoring.
