# TASK-N208 — Add Model Catalog and Selector Fixtures/Tests

## Goal

Add fixtures and contract tests for model catalog and audit target selector.

---

## Scope

Implement:

```text
model catalog fixtures
selector fixtures
frontend tests
backend catalog contract tests if applicable
```

---

## Fixture cases

```text
empty catalog
ChatGPT family with multiple models
Gemini family
Claude family
model supports L1 only
model supports L1+experimental L2
disallowed model filtered/disabled
catalog warning/error
legacy audit converted to targets
```

---

## Tests

Frontend:

```text
selector renders fixture families
multiselect works
L2 disabled state works
experimental L2 marker works
plus family flow works
target output correct
legacy target fixture loads
```

Backend if applicable:

```text
catalog response schema stable
allowlist applied
cache metadata present
```

---

## Acceptance criteria

- Model catalog fixtures exist.
- Selector tests cover key flows.
- Contract tests cover catalog shape if backend endpoint exists.
- No real OpenRouter calls.
- Task-scoped tests pass.
- TypeScript/ruff passes for touched files.

---

## Non-goals

- Do not implement new UI beyond test coverage.
- Do not call real OpenRouter.
- Do not change audit pipeline.
