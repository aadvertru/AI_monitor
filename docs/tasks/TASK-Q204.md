# TASK-Q204 — Add People Also Ask Provider Abstraction and Config

## Goal

Add a backend abstraction for People Also Ask (PAA) query providers.

This prepares the project for SerpApi-based PAA enrichment while keeping provider choice replaceable.

Do not implement SerpApi runtime calls in this task unless unavoidable.

---

## Scope

Implement:

```text
PAA provider interface
PAA request/response DTOs
PAA config keys
mock PAA provider for tests
safe diagnostics
task-scoped backend tests
```

---

## Provider abstraction

Define an interface equivalent to:

```python
class PeopleAlsoAskProvider:
    async def get_questions(
        self,
        query: str,
        language: str | None,
        country: str | None,
        limit: int,
    ) -> PeopleAlsoAskResult:
        ...
```

Response shape:

```python
PeopleAlsoAskResult(
    questions=[
        PeopleAlsoAskQuestion(
            text="...",
            source="paa",
            provider="serpapi",
            metadata={}
        )
    ],
    warnings=[]
)
```

---

## Config keys

Add config keys:

```text
PAA_ENABLED
PAA_PROVIDER
PAA_MAX_RESULTS
PAA_REQUEST_TIMEOUT_SECONDS
SERPAPI_API_KEY
SERPAPI_DEFAULT_COUNTRY
SERPAPI_DEFAULT_LANGUAGE
```

Defaults:

```text
PAA_ENABLED=false
PAA_PROVIDER=mock
PAA_MAX_RESULTS=10
PAA_REQUEST_TIMEOUT_SECONDS=15
```

Do not add real keys.

---

## Safety

- Frontend must never call SerpApi directly.
- Do not expose SerpApi API key.
- Do not log raw SerpApi payloads.
- No real PAA calls in CI.

---

## Tests

Backend tests:

```text
PAA config loads
PAA disabled returns safe diagnostic or empty result according to convention
mock provider returns deterministic questions
limit respected
language/country passed through DTO
missing provider handled safely
no API keys in serialized output/loggable errors
```

---

## Acceptance criteria

- PAA provider interface exists.
- PAA DTOs exist.
- PAA config exists.
- Mock PAA provider exists for tests.
- PAA provider can be injected/mocked.
- No real SerpApi calls in CI.
- No frontend changes.
- Task-scoped backend tests pass.
- Touched-file ruff passes.

---

## Non-goals

- Do not implement SerpApi adapter yet unless trivial and explicitly separated.
- Do not extend seed query generation yet.
- Do not implement frontend PAA controls.
- Do not call Google directly.
- Do not fix unrelated legacy failures.
