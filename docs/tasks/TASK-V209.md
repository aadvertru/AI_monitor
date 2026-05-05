# TASK-V209 — Add Web5 Summary Fixtures and UI Tests

## Goal

Add fixtures and regression tests for the Web5 summary page.

---

## Scope

Implement:

```text
summary v2 UI fixtures
model summary fixtures
partial/failed fixtures
evaluation-missing fixtures
OpenRouter gateway fixtures
frontend UI tests
```

---

## Required fixtures

```text
completed audit with L1/L2
partial audit
failed audit
audit without evaluation
model with only L1
model with L1+L2
OpenRouter L2 experimental target
provider diagnostics
```

---

## Tests

Frontend tests:

```text
summary page renders completed fixture
summary page renders partial fixture
summary page renders no-evaluation fixture
cards display correct values
model summary rows display correct values
OpenRouter experimental marker visible
provider diagnostics safe
actions render
i18n labels render
raw content not translated
```

---

## Acceptance criteria

- Web5 fixtures exist.
- UI regression tests cover major states.
- No raw provider payloads/secrets in fixtures.
- Task-scoped frontend tests pass.
- TypeScript passes.

---

## Non-goals

- Do not implement new UI beyond test support.
- Do not change backend.
- Do not implement exports.
