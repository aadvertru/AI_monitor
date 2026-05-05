# TASK-W209 — Add Answer Matrix Fixtures and Regression Tests

## Goal

Add fixtures and regression tests for the Web6/Web7 answer matrix UI.

---

## Scope

Implement:

```text
matrix fixtures
cell state fixtures
filter fixtures
OpenRouter gateway fixtures
frontend regression tests
```

---

## Required fixtures

```text
single model L1
same model L1+L2
multi-model audit
completed cells
failed cells
missing cells
correct/partial/incorrect/unknown verdicts
OpenRouter L2 experimental column
partial audit
no evaluation
sources count
provider diagnostics
```

---

## Tests

Frontend tests:

```text
matrix renders fixture
verdict badges render
failed/missing cells render
expand details works
filters work
OpenRouter experimental marker renders
provider diagnostics safe
i18n labels render
raw fields not rendered
```

---

## Acceptance criteria

- Matrix fixtures exist.
- Regression tests cover major states.
- No raw provider payloads/secrets in fixtures.
- Task-scoped frontend tests pass.
- TypeScript passes.

---

## Non-goals

- Do not implement new backend behavior.
- Do not change parser/scoring.
