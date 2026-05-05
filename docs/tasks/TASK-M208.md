# TASK-M208 — Add Multi-Target Audit Fixtures and Contract Tests

## Status

Ready for implementation after TASK-M204, M205, M206, and M207.

## Goal

Add fixtures and contract tests for canonical audit targets and multi-target scheduling.

This task includes both backend and frontend fixtures/tests.

---

## Dependencies

Requires:

```text
TASK-M203
TASK-M204
TASK-M205
TASK-M206
TASK-M207
```

---

## Scope

Implement:

```text
backend fixtures for multi-target audits
API contract tests
scheduler tests
frontend parsing fixtures
frontend API mapping tests using fixtures
```

Frontend fixtures are in scope. Do not mark them optional.

---

## Required backend fixture cases

```text
legacy single provider L1
single model L1
single model L1+L2
two models same level L1
two families mixed levels
OpenRouter L1 target
OpenRouter L2 experimental target
two OpenRouter same-level targets with different model_id values
audit over caps
legacy audit without targets
```

---

## Required frontend fixture cases

```text
audit detail with model_targets wire field
audit detail legacy providers/scdl_level only
create payload with internal modelTargets
create payload mapped to wire model_targets
OpenRouter L2 target gateway_l2_experimental=true
missing model_targets legacy-safe response
```

---

## Backend/API tests

```text
model_targets schema stable
legacy conversion stable
scheduling query × targets stable
target_id preserved
caps stable
gateway metadata safe
two same-level OpenRouter targets with different model_id values do not collapse
provider request payload uses each target.model_id
no raw provider responses/secrets in fixtures
```

---

## Frontend tests

```text
AuditTarget internal type parses snake_case fixture
legacy detail parses fixture
create payload fixture maps modelTargets to model_targets
actual request body does not contain modelTargets
gateway_l2_experimental maps correctly
```

---

## Acceptance criteria

- Multi-target backend fixtures exist.
- Frontend model target fixtures exist.
- Contract tests cover legacy and new payloads.
- Scheduling tests cover query × target expansion.
- Provider model payload tests cover two same-level different model_id targets.
- Gateway metadata covered.
- No raw provider responses/secrets in fixtures.
- Task-scoped backend/frontend tests pass.
- Touched-file ruff/typecheck passes.

---

## Escalate if

- Frontend and backend fixture formats cannot be shared or aligned.
- Provider request model payload cannot be asserted without broad test infrastructure changes.
- Adding these fixtures requires updating unrelated legacy fixtures extensively.

## Commands

Use task-scoped commands.

Suggested backend checks:

```bash
pytest <backend fixture/contract/scheduler tests>
ruff check <touched backend files>
```

Suggested frontend checks:

```bash
cd apps/web
npm run typecheck
npm test -- <frontend fixture/API mapping tests>
```

Do not fix unrelated full-suite failures.

---

## Done means

Backend and frontend fixtures cover canonical/legacy target behavior, scheduling, caps, wire mapping, and target.model_id provider request behavior.

---

## Non-goals

- Do not implement selector UI.
- Do not implement model catalog.
- Do not run real providers.
- Do not add a partial scheduling fixture in this task; if needed, cover it in a later scheduling-specific task.
- Do not fix unrelated legacy failures.
