# TASK-Q205 — Implement SerpApi People Also Ask Adapter

## Goal

Implement a SerpApi-backed People Also Ask adapter behind the PAA provider abstraction.

Use mocked SerpApi responses in tests. No real SerpApi calls in CI.

---

## Scope

Implement:

```text
SerpApiPaaProvider
SerpApi config validation
PAA response parsing
safe error normalization
mocked tests
```

Do not extend seed query generation UI/runtime yet.

---

## Config

Use:

```text
SERPAPI_API_KEY
SERPAPI_DEFAULT_COUNTRY
SERPAPI_DEFAULT_LANGUAGE
PAA_REQUEST_TIMEOUT_SECONDS
PAA_MAX_RESULTS
```

Missing `SERPAPI_API_KEY` when SerpApi provider is selected should return safe diagnostic.

---

## Request behavior

SerpApi request should include:

```text
search query
language
country/location if supported
limit/max results if supported or applied after parsing
```

Do not expose SerpApi raw request/response to frontend.

---

## Response parsing

Extract People Also Ask questions from SerpApi response.

Return normalized questions:

```json
{
  "text": "What programs does Harmony Ballet Studio offer?",
  "source": "paa",
  "provider": "serpapi",
  "metadata": {
    "language": "en",
    "country": "us"
  }
}
```

Do not include raw response payload.

---

## Error mapping

Map:

```text
missing API key → NO_API_KEY or CONFIGURATION_ERROR according to provider diagnostics convention
timeout → TIMEOUT
rate limit / quota → RATE_LIMIT
invalid response shape → INVALID_RESPONSE
provider unavailable → PROVIDER_UNAVAILABLE
generic request failure → PROVIDER_REQUEST_FAILED
unknown exception → UNKNOWN_PROVIDER_ERROR
```

---

## Tests

Mock HTTP/client.

Test:

```text
successful PAA extraction
empty PAA result
limit respected
language/country passed
missing API key
timeout
rate limit/quota
invalid response shape
provider unavailable
generic failure
no raw payload/API key in output
```

---

## Acceptance criteria

- SerpApi PAA provider implemented.
- Provider returns normalized PAA questions.
- Errors normalized safely.
- Limit/language/country handled.
- No raw SerpApi response exposed.
- No real SerpApi calls in CI.
- Task-scoped backend tests pass.
- Touched-file ruff passes.

---

## Non-goals

- Do not update seed query generation endpoint yet.
- Do not implement frontend PAA controls.
- Do not implement DataForSEO.
- Do not change parser/scoring.
