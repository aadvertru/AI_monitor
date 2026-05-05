# Model Catalog and Audit Target Selector Contract

## Purpose

This document defines the backend/frontend contract for the OpenRouter model
catalog and audit target selector.

The goal is to let authenticated users select AI families, models, and SCDL
levels without typing executable model ids manually. The backend remains the
source of truth for allowed models and must validate all submitted
`model_targets`.

## Endpoint

Frontend reads the catalog through:

```http
GET /model-catalog
```

Authentication is required. Unauthenticated requests must return the project
standard unauthorized response.

The endpoint is part of the authenticated audit creation flow and is filtered
through product/account policy. It is not a public browsing endpoint.

## AI Family Mapping

The initial product mapping is:

```text
chatgpt     -> openai/*
gemini      -> google/*
claude      -> anthropic/*
grok        -> x-ai/*
perplexity  -> perplexity/*
```

Unknown model provider prefixes must not be assigned to a supported AI family.
Additional families may be added later through explicit backend configuration.

## OpenRouter Source

The normal service should use:

```text
/api/v1/models/user
```

This account-specific endpoint is preferred because it can reflect account
availability, privacy settings, and model preferences.

If `/api/v1/models/user` is unavailable or incompatible, escalate before falling
back to public `/api/v1/models`.

## Allowlist Semantics

Frontend-facing `/model-catalog` returns only allowed models.

The backend allowlist is controlled by:

```text
OPENROUTER_ALLOWED_MODELS
```

Rules:

```text
normal frontend DTOs must not include is_allowed
disallowed models are omitted, not returned as disabled
missing or empty allowlist returns a safe CONFIGURATION_ERROR-style diagnostic
audit create/update still validate submitted model_targets against backend policy
frontend cannot execute arbitrary model_id values
```

A future admin/debug endpoint may expose a full catalog including disallowed
models, but that is out of scope.

## Response Shape

Successful response:

```json
{
  "families": [
    {
      "id": "chatgpt",
      "label": "ChatGPT",
      "models": [
        {
          "model_id": "openai/gpt-4o-mini",
          "display_name": "GPT-4o mini",
          "model_provider": "openai",
          "execution_provider": "openrouter",
          "supports_l1": true,
          "supports_l2_gateway": true,
          "l2_experimental": true,
          "context_length": 128000
        }
      ]
    }
  ],
  "cached_at": "2026-01-01T00:00:00Z",
  "expires_at": "2026-01-02T00:00:00Z",
  "warnings": []
}
```

`context_length` is optional and may be omitted when unavailable.

Do not expose:

```text
is_allowed
raw OpenRouter model objects
raw OpenRouter catalog responses
account or billing data
headers
API keys
internal config dumps
```

## Normalized Model Fields

Each frontend-facing model contains:

```text
model_id
display_name
model_provider
execution_provider=openrouter
ai_family
supports_l1
supports_l2_gateway
l2_experimental
context_length, optional
```

L1 is normal OpenRouter chat completion without web access.

L2 through OpenRouter is experimental gateway web-search behavior and must be
marked with:

```text
supports_l2_gateway=true
l2_experimental=true
```

## Cache Policy

Catalog cache TTL:

```text
24 hours
```

Config:

```text
OPENROUTER_MODEL_CATALOG_CACHE_TTL_SECONDS=86400
OPENROUTER_CATALOG_ENABLED
OPENROUTER_API_KEY
OPENROUTER_ALLOWED_MODELS
```

Failure behavior:

```text
OPENROUTER_CATALOG_ENABLED=false -> safe disabled diagnostic, no OpenRouter call
missing OPENROUTER_API_KEY -> safe missing-key diagnostic, no OpenRouter call
missing/empty OPENROUTER_ALLOWED_MODELS -> safe configuration diagnostic
fetch failure with cache -> return stale cache with safe warning
fetch failure without cache -> return safe catalog diagnostic/error
```

Warnings must not include raw OpenRouter payloads, request headers, stack traces,
API keys, tokens, prompts, or raw response bodies.

## Selector UX Contract

The audit create/edit UI should use the catalog as follows:

```text
first AI family block visible by default, for example ChatGPT
each family block has model multiselect
each selected model has L1/L2 toggles
plus button adds another AI family block
user can remove family/model selections
unsupported L2 toggle is disabled
OpenRouter L2 is marked experimental
duplicate target selections are prevented
run estimate updates when queries or selected targets change
```

Selector output maps to canonical `model_targets`:

```json
{
  "model_targets": [
    {
      "ai_family": "chatgpt",
      "execution_provider": "openrouter",
      "model_provider": "openai",
      "model_id": "openai/gpt-4o-mini",
      "display_name": "GPT-4o mini",
      "level": "L1",
      "gateway": true,
      "gateway_l2_experimental": false
    }
  ]
}
```

The frontend may use camelCase internally, but API request bodies must use
snake_case `model_targets`.

## Backend Validation

`GET /model-catalog` is display-only. It does not authorize future execution by
itself.

Audit create/update must still validate:

```text
model_targets are allowed by backend catalog/policy
target model_id exists in backend allowlist
target execution_provider is supported
L2 gateway flags match level/capability policy
caps are enforced before save/run
mixed canonical model_targets and legacy providers/scdl_level payloads are rejected
```

## Test Requirements

Implementation tasks must test:

```text
authenticated /model-catalog access
unauthenticated request rejected
mocked OpenRouter catalog fetch
no real OpenRouter calls in CI
24h cache TTL
cache hit avoids repeated fetch
cache expiry refreshes
stale cache returned with warning on fetch failure
safe diagnostic when no cache exists
catalog disabled does not call OpenRouter
missing API key does not call OpenRouter
missing/empty allowlist returns configuration diagnostic
allowlist filtering returns only allowed models
is_allowed absent from frontend response
AI family mapping
unknown provider prefix excluded from supported families
L1/L2 capability flags
OpenRouter L2 experimental marker
selector output maps to canonical model_targets
frontend sends model_targets, not modelTargets
estimate uses POST /audits/estimate with model_targets
raw OpenRouter payloads and secrets are not exposed
```

## Non-Goals

This contract does not implement:

```text
runtime catalog service
frontend selector
OpenRouter network calls
model execution
admin/debug full catalog endpoint
public unauthenticated catalog browsing
billing or usage limits
```
