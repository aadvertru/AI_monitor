# TASK-N203 — Add Authenticated Model Catalog API Endpoint

## Status

Ready for implementation.

## Goal

Expose the cached OpenRouter model catalog to the frontend through a safe authenticated backend endpoint.

## Dependencies

Requires:

```text
TASK-N201
TASK-N202
```

## Scope

Implement:

```text
GET /model-catalog endpoint
login requirement
safe DTO serialization
warnings/diagnostics forwarding from service
task-scoped backend/API tests
```

## Endpoint

```http
GET /model-catalog
```

Authentication is mandatory.

Unauthenticated requests return 401/unauthorized according to project convention.

## Response

Return:

```json
{
  "families": [],
  "cached_at": "...",
  "expires_at": "...",
  "warnings": []
}
```

Rules:

```text
only allowed models are returned
no is_allowed field in normal response
OpenRouter L2 marked experimental
cache metadata included
safe warnings included
```

## Failure behavior

```text
service returns stale cache with warning -> endpoint returns 200 with warnings
service has no cache and cannot fetch -> endpoint returns safe error/diagnostic according to project convention
catalog disabled -> safe diagnostic
missing API key -> safe diagnostic
```

Do not expose raw OpenRouter response.

## Tests

Backend/API tests:

```text
unauthenticated request rejected
authenticated request returns families
only allowed models returned
is_allowed not present
cache metadata returned
warnings returned for stale cache
safe error when no cache/fetch failure
catalog disabled safe
missing key safe
OpenRouter API key not exposed
raw OpenRouter response not exposed
```

## Acceptance criteria

- `GET /model-catalog` exists.
- Endpoint requires login.
- Endpoint returns allowed-only catalog data.
- Stale-cache warning behavior works.
- Safe no-cache failure behavior works.
- No raw provider data/secrets exposed.
- Task-scoped backend/API tests pass.
- Touched-file ruff passes.

## Escalate if

- Product requires public unauthenticated model catalog.
- Existing auth middleware cannot be applied without route refactor.
- Service failure shape conflicts with existing API error conventions.

## Commands

```bash
pytest <model catalog endpoint tests>
ruff check <touched backend files>
```

## Done means

Authenticated users can fetch a safe allowed-only model catalog; unauthenticated users cannot.
