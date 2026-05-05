# TASK-S205 — Add Evaluation Runner and Rerun Endpoint

## Goal

Add a backend service and endpoint to run or rerun answer evaluation for an audit.

This powers the “rerun fact-checking” action shown in the target summary UI.

---

## Scope

Implement:

```text
evaluation runner service
POST /audits/{id}/rerun-evaluation endpoint
ownership/auth guard
evaluation record creation/update
task-scoped backend tests
```

Use the mock/deterministic evaluator from `TASK-S204` unless a real evaluator is already explicitly configured.

---

## Endpoint

```http
POST /audits/{id}/rerun-evaluation
```

Response:

```json
{
  "audit_id": 1,
  "evaluated_runs": 20,
  "skipped_runs": 2,
  "status": "completed",
  "warnings": []
}
```

Adapt to project conventions.

---

## Rules

- Requires auth.
- Enforces audit ownership.
- Does not rerun provider calls.
- Does not mutate raw answers.
- Does not mutate ParsedResult.
- Does not rerun parser/scoring.
- Updates evaluation records only.
- Skips runs without usable answer text.
- Handles partial/failed audits safely.

---

## Evaluation target selection

Evaluate runs/cells that have:

```text
usable answer text
terminal successful provider result
no fatal parsing issue preventing answer access
```

Skip:

```text
failed provider runs with no answer
missing raw/normalized answer
not_run cells
```

---

## Tests

Backend/API tests:

```text
unauthenticated rejected
non-owner rejected
owner can rerun evaluation
successful runs evaluated
failed/no-answer runs skipped
evaluation records created
existing evaluations updated/replaced
raw answers unchanged
parsed results unchanged
scores unchanged
summary status not corrupted
safe response shape
```

Safety tests:

```text
no raw prompts/responses/secrets in response
```

---

## Acceptance criteria

- Rerun evaluation endpoint exists.
- Auth/ownership enforced.
- Evaluation runner creates/updates evaluations.
- Provider calls are not rerun.
- Parser/scoring are not rerun.
- Failed/no-answer runs skipped safely.
- Task-scoped backend tests pass.
- Touched-file ruff passes.

---

## Non-goals

- Do not implement real LLM evaluator.
- Do not implement frontend button.
- Do not change visibility scoring.
- Do not reprocess provider responses.
- Do not fix unrelated legacy failures.
