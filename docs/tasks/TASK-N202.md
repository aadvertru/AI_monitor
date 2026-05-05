# TASK-N202 — Add OpenRouter Model Catalog Service with Cache

## Status

Ready for implementation.

## Goal

Add a backend service that fetches OpenRouter model catalog data, filters it through product policy, and caches safe frontend-facing results.

No HTTP endpoint is implemented in this task. The endpoint belongs to TASK-N203.

## Why

The service must provide a stable, testable, backend-controlled list of allowed OpenRouter models grouped by AI family. The frontend must not receive arbitrary or disallowed models.

## Dependencies

Requires:

```text
TASK-N201 — Model catalog contract
OpenRouter config from gateway phase
```

## Scope

Implement:

```text
OpenRouter model catalog client/service
use /api/v1/models/user when available
24h cache
safe model normalization
AI family grouping
allowlist filtering
mock catalog provider for tests
task-scoped backend tests
```

## Out of scope

```text
HTTP /model-catalog endpoint
frontend model selector
audit create/update changes
real OpenRouter calls in CI
```

## OpenRouter source endpoint

Decision:

```text
Use OpenRouter /api/v1/models/user for the normal service when available.
```

Reason:

```text
The user/account-specific endpoint is safer because it can reflect account preferences, privacy settings, and model availability.
```

If `/api/v1/models/user` is not available in the installed/verified OpenRouter API version, escalate before falling back to public `/api/v1/models`.

## Frontend-facing allowlist behavior

Decision:

```text
Normal service output includes only allowed models.
```

If a lower-level internal helper tracks `is_allowed`, that field must not be included in frontend-facing DTOs.

## Config

Add or reuse:

```text
OPENROUTER_MODEL_CATALOG_CACHE_TTL_SECONDS=86400
OPENROUTER_ALLOWED_MODELS
OPENROUTER_CATALOG_ENABLED
OPENROUTER_API_KEY
```

Rules:

```text
OPENROUTER_CATALOG_ENABLED=false returns safe disabled diagnostic and does not call OpenRouter.
missing OPENROUTER_API_KEY returns NO_API_KEY or safe catalog diagnostic and does not call OpenRouter.
empty/missing OPENROUTER_ALLOWED_MODELS returns CONFIGURATION_ERROR.
```

## Normalized model fields

Frontend-facing normalized model:

```text
model_id
display_name
model_provider
execution_provider=openrouter
ai_family
supports_l1
supports_l2_gateway
l2_experimental
context_length if available and safe
```

Do not expose:

```text
is_allowed
raw OpenRouter model object
account/billing data
API keys
headers
```

## Cache behavior

Decision:

```text
Cache TTL = 24 hours.
```

Failure behavior:

```text
If fetch fails and cached catalog exists, return stale cache with safe warning.
If fetch fails and no cache exists, return safe diagnostic/error.
```

This behavior is mandatory and must be tested.

## AI family mapping

Use configured mapping:

```text
chatgpt     → openai/*
gemini      → google/*
claude      → anthropic/*
grok        → x-ai/*
perplexity  → perplexity/*
```

Unknown model provider prefixes:

```text
must not be assigned to supported family
exclude from normal family output unless explicitly mapped in config
```

## Tests

Backend tests:

```text
OPENROUTER_CATALOG_ENABLED=false does not call OpenRouter and returns safe diagnostic
missing OPENROUTER_API_KEY does not call OpenRouter and returns safe diagnostic
missing/empty OPENROUTER_ALLOWED_MODELS returns CONFIGURATION_ERROR
mock /api/v1/models/user fetch returns normalized models
no real network call is made; injected mock client required
models grouped by AI family
unknown model provider not assigned to supported family
allowlist filters out disallowed models
frontend-facing DTO does not include is_allowed
cache hit avoids second fetch
cache expires and refreshes
failed fetch with cache returns stale cache plus warning
failed fetch without cache returns safe diagnostic
raw OpenRouter response/API key/headers not exposed
```

## Acceptance criteria

- Model catalog service exists.
- Service uses `/api/v1/models/user` or escalates if unavailable.
- Frontend-facing output includes only allowed models.
- Cache TTL and stale-cache behavior implemented.
- Disabled/missing key/empty allowlist cases handled.
- Unknown provider prefixes are not assigned to supported families.
- No endpoint implemented in this task.
- No real OpenRouter calls in CI.
- Task-scoped backend tests pass.
- Touched-file ruff passes.

## Escalate if

- `/api/v1/models/user` cannot be used after checking current OpenRouter docs/API.
- Existing cache infrastructure cannot support stale-cache return.
- Product wants to expose disallowed models as disabled items.
- Implementing catalog service requires unrelated provider factory changes.

## Commands

```bash
pytest <model catalog service tests>
ruff check <touched backend files>
```

## Done means

Backend catalog service returns cached, allowed-only, AI-family grouped models using mocked OpenRouter client, with deterministic cache/failure behavior.
