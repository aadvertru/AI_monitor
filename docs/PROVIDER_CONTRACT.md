# Provider Contract

This document defines the provider adapter contract for AI Brand Visibility Monitor.
It is the standard for mock, OpenAI, and future real providers such as Anthropic.

The goal is to keep provider integrations interchangeable and prevent provider-specific
response shapes from leaking into parser, scoring, aggregation, API responses, or frontend code.

## Current Status

- `mock`: required for deterministic local/test execution.
- `openai`: first real provider.
- `anthropic`: future provider, not implemented yet.

## Core Rules

1. Frontend must never call provider APIs directly.
2. Parser, scoring, and aggregation must consume normalized provider output only.
3. Provider adapters must not calculate scores, classify competitors, or implement business logic.
4. Provider adapters must normalize every success and failure.
5. Provider adapters must not raise provider/network exceptions outward.
6. Raw provider responses, raw prompts, request headers, API keys, and secrets must not reach normal frontend endpoints.
7. CI must not call real providers.
8. L1 and L2 behavior must be explicit per provider. No silent fallback is allowed.

## Current Adapter Interface

The current code uses:

```python
class BaseProviderAdapter:
    async def query(self, query: str, **kwargs) -> ProviderResponse: ...
```

`ProviderResponse` is the current implementation DTO:

```python
ProviderStatus = Literal["success", "error", "timeout", "rate_limited"]

ProviderResponse(
    status: ProviderStatus,
    raw_answer: str | None,
    citations: list[dict] | None,
    response_time: float | None,
    error: dict | None,
    provider_metadata: dict | None,
)
```

Future typed DTOs may be introduced, but they must preserve this contract.

## ProviderRunInput

Provider adapters should accept a normalized input equivalent to:

```python
ProviderRunInput(
    provider: str,
    level: Literal["L1", "L2"],
    model: str,
    query: str,
    brand_name: str,
    brand_domain: str | None = None,
    brand_description: str | None = None,
    competitors: list[str] = [],
    locale: str | None = None,
    max_output_tokens: int | None = None,
    timeout_seconds: int | None = None,
    metadata: dict[str, Any] = {},
)
```

Field rules:

- `provider`: normalized provider id such as `mock`, `openai`, or `anthropic`.
- `level`: SCDL level, `L1` or `L2`.
- `model`: backend-configured model. Normal audit UI must not choose models.
- `query`: final seed query text, trimmed and non-empty.
- `brand_name`: audited brand/entity.
- `brand_domain`: optional validated domain.
- `brand_description`: optional description.
- `competitors`: optional names/domains.
- `locale`: optional language/country hint.
- `max_output_tokens` and `timeout_seconds`: backend-controlled caps.
- `metadata`: backend-only metadata. Must not contain secrets.

## ProviderRunOutput

A successful provider call should normalize to:

```python
ProviderRunOutput(
    provider: str,
    model: str,
    level: Literal["L1", "L2"],
    answer_text: str,
    raw_response_ref: str | None = None,
    sources: list[ProviderSource] = [],
    usage: ProviderUsage | None = None,
    metadata: dict[str, Any] = {},
)
```

Mapping to current implementation:

- `answer_text` maps to `ProviderResponse.raw_answer`.
- `sources` maps to `ProviderResponse.citations`.
- `metadata` maps to `ProviderResponse.provider_metadata`.
- `raw_response_ref` is internal only and must not expose raw response data.

Rules:

- Empty usable answer text must be returned as an `EMPTY_RESPONSE` error, not as success.
- Missing citations/sources are allowed.
- Missing usage is allowed and must not fail the run.
- Metadata must be JSON-serializable and secret-free.

## ProviderSource / Citation

Normalized source shape:

```python
ProviderSource(
    title: str | None = None,
    url: str | None = None,
    domain: str | None = None,
    snippet: str | None = None,
    source_type: Literal["web", "citation", "document", "unknown"] = "unknown",
    provider_source_id: str | None = None,
    metadata: dict[str, Any] = {},
)
```

Rules:

- URLs must be validated/sanitized before display.
- L1 normally returns no sources.
- L2 may return no sources if the provider does not provide them, but diagnostics should make this visible.
- Frontend displays normalized sources only.
- Frontend must not parse raw provider responses to extract citations.

## ProviderUsage

Normalized usage shape:

```python
ProviderUsage(
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    total_tokens: int | None = None,
    cached_tokens: int | None = None,
    reasoning_tokens: int | None = None,
    cost_estimate: float | None = None,
    currency: str | None = None,
)
```

Rules:

- Usage may be partially unavailable.
- Usage must be JSON-serializable before storing in `provider_metadata`.
- Cost estimates must not be shown to users until billing/usage reporting is a product feature.
- Provider-specific usage fields may be kept only in backend-safe metadata.

## ProviderError

Provider failures must normalize to:

```python
ProviderError(
    code: ProviderErrorCode,
    message: str,
    provider: str,
    model: str | None = None,
    level: Literal["L1", "L2"] | None = None,
    retryable: bool = False,
    details: dict[str, Any] = {},
)
```

Allowed error codes:

```text
PROVIDER_DISABLED
NO_API_KEY
INVALID_API_KEY
INVALID_MODEL
UNSUPPORTED_L2
TIMEOUT
RATE_LIMIT
EMPTY_RESPONSE
INVALID_RESPONSE
PROVIDER_UNAVAILABLE
PROVIDER_REQUEST_FAILED
CONFIGURATION_ERROR
UNKNOWN_PROVIDER_ERROR
```

Rules:

- Error messages must be safe for frontend display.
- Error details must not include raw response bodies, prompts, headers, stack traces, API keys, or secrets.
- Timeout, rate limit, and transient provider outage errors should be marked retryable when appropriate.
- Unknown provider exceptions must map to `UNKNOWN_PROVIDER_ERROR` or `PROVIDER_REQUEST_FAILED`.

Suggested HTTP mapping for API endpoints:

```text
PROVIDER_DISABLED        -> 503
NO_API_KEY               -> 503
INVALID_API_KEY          -> 503
INVALID_MODEL            -> 422 or 503
UNSUPPORTED_L2           -> 422
TIMEOUT                  -> 504
RATE_LIMIT               -> 429
EMPTY_RESPONSE           -> 502
INVALID_RESPONSE         -> 502
PROVIDER_UNAVAILABLE     -> 503
PROVIDER_REQUEST_FAILED  -> 502
CONFIGURATION_ERROR      -> 503
UNKNOWN_PROVIDER_ERROR   -> 502
```

Use existing project conventions where they are already stricter.

## SCDL L1/L2 Behavior

```text
L1 = AI answer without web access
L2 = AI answer with web access
```

L1 rules:

- Must not enable web search.
- Must not enable browsing tools.
- Must not perform external source enrichment.
- Sources are normally empty.

L2 rules:

- May enable web search only when the provider supports it.
- Must normalize citations/sources when available.
- May succeed without sources if the provider returns a usable answer but no source data.
- Must return `UNSUPPORTED_L2` when the provider cannot support L2.

No silent fallback:

- No `L2 -> L1` downgrade.
- No real-provider fallback to mock.
- No configured-model fallback to another model.
- Any fallback must be explicit and visible in diagnostics.

## Timeout, Retry, and Rate Limits

- Provider calls must use backend-configured timeouts.
- Timeout must normalize to `TIMEOUT`.
- Rate limit must normalize to `RATE_LIMIT`.
- Retry policy belongs in backend execution code, not frontend.
- If retries are added, retry count and final error must be visible in safe diagnostics.
- CI tests must simulate timeout/rate-limit behavior without real provider calls.

## Configuration

Recommended config keys:

```text
PROVIDER_MODE=mock|openai|anthropic
REAL_PROVIDER_ENABLED=false|true

OPENAI_API_KEY=...
OPENAI_L1_MODEL=...
OPENAI_L2_MODEL=...
OPENAI_REQUEST_TIMEOUT_SECONDS=30
OPENAI_MAX_OUTPUT_TOKENS=1200

ANTHROPIC_API_KEY=...
ANTHROPIC_L1_MODEL=...
ANTHROPIC_L2_MODEL=...
ANTHROPIC_REQUEST_TIMEOUT_SECONDS=30
ANTHROPIC_MAX_OUTPUT_TOKENS=1200

REAL_PROVIDER_MAX_PROVIDERS=1
REAL_PROVIDER_MAX_QUERIES=5
REAL_PROVIDER_MAX_RUNS_PER_QUERY=1
REAL_PROVIDER_MAX_TOTAL_RUNS=5
```

Seed query generation is a separate provider-facing feature:

```text
SEED_QUERY_GENERATION_ENABLED=true
SEED_QUERY_GENERATION_PROVIDER=openai|mock
SEED_QUERY_GENERATION_MODEL=...
SEED_QUERY_GENERATION_TIMEOUT_SECONDS=30
```

Rules:

- Missing required API key must produce `NO_API_KEY`.
- Disabled provider must produce `PROVIDER_DISABLED`.
- Invalid model/config must produce `INVALID_MODEL` or `CONFIGURATION_ERROR`.
- Backend must enforce caps before provider execution.
- Frontend must never receive provider secrets or raw config.

## Raw Response Handling

Raw provider responses may be stored internally for debugging and post-processing.

Rules:

- Normal frontend endpoints must not return raw responses.
- CLI tools must not print raw responses by default.
- Stored raw responses must be serializable and secret-free.
- Admin/dev inspection endpoints must redact sensitive metadata.
- Parser and scoring should consume normalized answer text, not provider raw objects.
- Normal result DTOs should expose only internal raw response references when needed.

## Logging and Diagnostics

Provider execution should produce safe structured diagnostics:

```text
provider
model
level
audit_id
query_id or run_id
status
duration_ms
error_code
retryable
usage.input_tokens
usage.output_tokens
usage.total_tokens
source_count
```

Rules:

- Do not log API keys.
- Do not log full raw prompts by default.
- Do not log full raw responses by default.
- Query text may be logged only if current project logging policy allows it.
- Diagnostics should explain failures without exposing sensitive internals.

Frontend-safe diagnostics may look like:

```json
{
  "provider_error": {
    "code": "NO_API_KEY",
    "message": "OpenAI API key is not configured.",
    "provider": "openai",
    "retryable": false
  }
}
```

## Mock and CI Rules

- Mock provider must be deterministic.
- Unit tests must not require OpenAI, Anthropic, or other real provider keys.
- CI must not call real provider APIs.
- Provider adapter tests must mock SDK/client calls.
- Snapshot fixtures must not include secrets or raw provider payloads.

Required test coverage for each real provider:

- successful L1
- successful L2 when supported
- unsupported L2 when not supported
- timeout
- rate limit
- missing API key
- invalid model/config
- empty response
- invalid response
- usage normalization
- source normalization
- no secret leakage in errors, metadata, logs, or frontend-safe DTOs

## Manual Verification Checklist

Minimum real-provider manual checks:

```text
provider disabled error
missing API key error
one-query L1 audit
one-query L2 audit if supported
unsupported L2 if not supported
timeout or forced provider failure if feasible
typed seed query audit execution
summary/results/sources render after execution
raw response is stored but not exposed to normal frontend endpoints
```

## Provider Parity Checklist

Each real provider must complete this checklist before being marked supported:

```text
Provider name:
Adapter implemented:
L1 supported:
L2 supported:
Unsupported L2 normalized:
Raw response internally storable:
Normalized answer_text:
Normalized sources:
Normalized usage:
Timeout normalized:
Rate limit normalized:
Missing key normalized:
Invalid model normalized:
No secret leakage:
Mock tests only in CI:
Manual verification completed:
```

## Adding a New Provider

Before implementing a new real provider:

1. Confirm supported SCDL levels.
2. Add backend config and `.env.example` placeholders.
3. Implement adapter behind this contract.
4. Normalize success output to provider output fields.
5. Normalize errors to `ProviderError`.
6. Add mock/client tests.
7. Add provider parity checklist entry.
8. Run manual real-provider verification.
9. Do not change parser/scoring for provider-specific response shapes.
10. Do not expose provider-specific raw responses to frontend.

## Recommendation Before Anthropic/Claude

Before adding Anthropic/Claude:

1. Stabilize OpenAI one-click UI audit flow.
2. Normalize provider errors and frontend-safe diagnostics.
3. Complete OpenAI provider parity checklist.
4. Add Anthropic L1 adapter first.
5. Treat Anthropic L2 as unsupported until explicitly implemented and verified.
