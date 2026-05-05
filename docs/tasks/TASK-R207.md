# TASK-R207 — Add Results v2 Fixtures and Contract Tests

## Goal

Add fixtures and contract tests for results v2 APIs to stabilize future Web5/Web6/Web7 UI work.

---

## Scope

Implement:

```text
mock multi-target audit fixtures
summary v2 fixture
answer matrix fixture
source-domain fixture
contract tests
legacy compatibility fixture
```

Do not implement UI.

---

## Required fixture cases

Create fixtures for:

```text
empty audit with no runs
single model L1 audit
single model L1+L2 audit
multi-model audit
partial audit with failed cells
OpenRouter gateway L1/L2 audit
legacy audit without audit_targets
evaluation-null audit
```

Use existing fixture structure.

---

## Contract tests

Backend/API tests:

```text
summary v2 schema stable
answer matrix schema stable
source domains schema stable
concepts/competitors placeholders stable
legacy compatibility stable
no raw provider payloads exposed
provider diagnostics safe
```

Frontend if applicable:

```text
types parse fixtures
empty/partial fixtures do not crash hooks
```

---

## Acceptance criteria

- Results v2 fixtures exist.
- Contract tests cover empty, completed, partial, gateway, and legacy cases.
- No raw provider responses/prompts in fixtures.
- Future UI can import/reuse fixtures if current test pattern allows it.
- Task-scoped tests pass.
- Touched-file ruff/typecheck passes.

---

## Non-goals

- Do not implement new UI.
- Do not implement evaluation.
- Do not change parser/scoring.
- Do not run real providers.
