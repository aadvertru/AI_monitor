# TASK-N201 — Define OpenRouter Model Catalog and Selector Contract

## Status

Ready. Documentation-only task.

## Goal

Define the backend/frontend contract for OpenRouter model catalog and audit target selector.

This task is documentation/contract only. Do not change runtime code.

## Why

The product needs model selection by AI family/model/level without allowing arbitrary frontend-provided model IDs. The contract must be decision-complete before implementing catalog service and selector UI.

## Dependencies

Requires Phase M target contract to exist or be accepted conceptually:

```text
AuditTarget / model_targets contract
```

## Scope

Document:

```text
OpenRouter model catalog endpoint
AI family mapping
allowlist semantics
auth requirement
cache/failure behavior
selector UX
test requirements for later implementation tasks
```

## Out of scope

```text
runtime catalog service
frontend selector
OpenRouter network calls
audit create/update changes
```

## Required decisions

### 1. AI family mapping

Document:

```text
chatgpt     → openai/*
gemini      → google/*
claude      → anthropic/*
grok        → x-ai/*
perplexity  → perplexity/*
```

Additional families may be added through config later.

### 2. Catalog endpoint

Define:

```http
GET /model-catalog
```

### 3. Authentication

Decision:

```text
GET /model-catalog requires login.
```

Reason:

```text
The catalog is part of authenticated audit creation and is filtered through product/account policy.
```

Unauthenticated requests must return the project-standard 401/unauthorized response.

### 4. Allowlist semantics

Decision:

```text
Frontend-facing /model-catalog returns only allowed models.
```

Do not expose disallowed models with `is_allowed=false` in the MVP endpoint.

If the implementation internally tracks allowed/disallowed models, `is_allowed` must not be exposed in the normal frontend DTO. A future admin/debug endpoint may expose full catalog, but that is out of scope.

### 5. Response shape

Use:

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
          "l2_experimental": true
        }
      ]
    }
  ],
  "cached_at": "2026-01-01T00:00:00Z",
  "expires_at": "2026-01-02T00:00:00Z",
  "warnings": []
}
```

No `is_allowed` field in frontend-facing response.

### 6. Cache policy

Decision:

```text
Catalog cache TTL = 24 hours.
```

Failure behavior:

```text
If OpenRouter catalog fetch fails and a cache exists, return stale cached catalog with a safe warning.
If OpenRouter catalog fetch fails and no cache exists, return safe provider/catalog diagnostic.
```

Warnings must not expose raw OpenRouter payloads, request headers, or API keys.

### 7. Selector UX

Document:

```text
first AI family block visible by default, e.g. ChatGPT
each family block has model multiselect
each selected model has L1/L2 toggles
plus button adds another AI family block
user can remove family/model selections
L2 via OpenRouter is marked experimental
run count estimate updates as selections change
```

### 8. Backend validation

Document:

```text
/model-catalog is display-only.
Audit create/update must still validate model_targets against backend allowlist/caps.
Frontend cannot execute arbitrary model_id values.
```

## Test requirements

No automated tests are required for this documentation-only task.

Later implementation tasks must test:

```text
authenticated /model-catalog access
unauthenticated request rejected
mocked OpenRouter catalog fetch
no real OpenRouter calls in CI
24h cache TTL
stale cache returned with warning on fetch failure
safe diagnostic when no cache exists
allowlist filtering returns only allowed models
AI family mapping
L1/L2 capability flags
OpenRouter L2 experimental marker
selector output maps to canonical model_targets
```

## Acceptance criteria

- Contract file is created or updated.
- Auth requirement is explicit.
- Allowlist semantics are explicit: frontend receives only allowed models.
- Cache TTL and failure behavior are explicit.
- Response DTO is defined without `is_allowed`.
- Selector UX documented.
- Test requirements documented.
- No runtime code changed.

## Escalate if

- Product wants to show disabled/disallowed models to normal users.
- OpenRouter account-specific model endpoint is unavailable or incompatible.
- The app must support public unauthenticated model catalog browsing.

## Commands

Documentation-only task.

Optional:

```bash
markdownlint docs/MODEL_CATALOG_CONTRACT.md
```

## Done means

The model catalog/selector contract is decision-complete enough for N202/N203/N205 implementation without choosing auth, allowlist, or cache semantics again.
