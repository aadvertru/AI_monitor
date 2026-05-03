# Seed Query Generation Contract

This document defines the MVP contract for controlled AI-assisted seed query generation in SCDL audits.

Seed query generation is optional. Manual query entry remains supported. Generated suggestions are draft-only until the user explicitly saves the audit setup.

## Endpoint

```http
POST /audit-seed-query-suggestions
```

This is a draft-safe endpoint. It does not require an audit id because it must work from unsaved create/edit form state.

Do not use an audit-id-only generation endpoint for the MVP flow.

## Request

```json
{
  "brand_name": "Seopaja",
  "brand_domain": "seopaja.fi",
  "brand_description": "SEO services for small businesses in Finland",
  "use_domain": true,
  "use_description": true,
  "count": 10,
  "existing_queries": [
    {
      "text": "What is Seopaja?",
      "type": "brand_direct",
      "source": "user"
    }
  ]
}
```

Rules:

- `brand_name`, `brand_domain`, and `brand_description` come from current visible form state.
- `existing_queries` is the current visible seed query list.
- `count` defaults to `10`.
- `count > 10` returns `422 Unprocessable Entity`.
- At least one of `use_domain` or `use_description` must be true.
- If `use_domain = true`, `brand_domain` must be present and valid.
- If `use_description = true`, `brand_description` must be present and non-empty.

## Response

```json
{
  "suggestions": [
    {
      "text": "Best SEO agencies for small businesses in Finland",
      "type": "category_discovery",
      "source": "ai"
    }
  ],
  "skipped_duplicates": 1,
  "skipped_limit": 0,
  "warnings": [
    "1 duplicate query was skipped."
  ]
}
```

Responses must not include raw prompts, raw provider responses, API keys, provider secrets, auth tokens, or internal tracebacks.

## Query Types

Allowed seed query types:

```text
brand_direct
category_discovery
recommendation
comparison
alternative
problem_solution
```

Generated suggestions always have:

```text
source = "ai"
type = one of the allowed query types
```

Manual queries default to:

```text
source = "user"
type = null
```

If the user edits an AI-generated suggestion before saving, `source` remains `ai`; source is provenance.

## Limits

```text
default generated count: 10
max generated count per request: 10
max total seed queries per audit/form: 20
min saved query length: 3 characters after trim
max saved query length: 300 characters
```

The backend is the source of truth for saved query validation.

## Deduplication

Backend must:

- validate incoming `existing_queries`
- deduplicate generated suggestions internally
- deduplicate generated suggestions against `existing_queries`
- enforce the 20-query total limit
- return skipped duplicate/limit counts and warnings
- filter invalid, empty, or unknown-type provider suggestions

Frontend must:

- pass the current visible query list as `existing_queries`
- defensively deduplicate returned suggestions before appending
- keep total visible query count at or below 20
- display backend warnings

Minimum deduplication normalization:

```text
query.trim().toLowerCase().replace(/\s+/g, " ")
```

## Domain and Description Priority

Description is the primary semantic signal when available.

Domain is a weak signal. If both domain and description are selected, the domain may be used for disambiguation, brand identity, and niche hints, but it must not override clear brand description context.

If only domain is selected, generation must stay conservative and avoid unsupported product claims.

## Persistence

Generation is synchronous and draft-only.

Forbidden behavior:

- Do not save suggestions inside `POST /audit-seed-query-suggestions`.
- Do not create audit runs after generation.
- Do not change audit status after generation.
- Do not start the audit pipeline after generation.
- Do not write raw provider responses as audit results.

Generated suggestions are persisted only when the user saves the final visible seed query list through the create/update audit flow.

## Save and Detail Compatibility

`seed_query_items` is the canonical typed field:

```json
{
  "seed_query_items": [
    {
      "text": "What is Seopaja?",
      "type": "brand_direct",
      "source": "ai"
    }
  ]
}
```

`seed_queries` remains a backward-compatible plain-text field:

```json
{
  "seed_queries": ["What is Seopaja?"]
}
```

Create/update request rules:

- Accept legacy `seed_queries: list[str]`.
- Accept canonical `seed_query_items`.
- If both are provided in the same request, return `422 Unprocessable Entity`.
- Legacy `seed_queries` are stored as `source = "user"` and `query_type = null`.

Detail/list responses may temporarily expose both:

```json
{
  "seed_queries": ["What is Seopaja?"],
  "seed_query_items": [
    {
      "text": "What is Seopaja?",
      "type": "brand_direct",
      "source": "ai"
    }
  ]
}
```

`seed_query_items` is canonical. `seed_queries` is compatibility output.

## Provider and Config

MVP provider behavior:

```text
SEED_QUERY_GENERATION_ENABLED=false -> 503 Service Unavailable
SEED_QUERY_GENERATION_PROVIDER=openai -> use OpenAI when configured
PROVIDER_MODE=openai or SEED_QUERY_GENERATION_PROVIDER=openai without OpenAI config -> 503 Service Unavailable
PROVIDER_MODE=mock or SEED_QUERY_GENERATION_PROVIDER=mock -> deterministic mock suggestions allowed for dev/test
```

Expected config keys:

```text
SEED_QUERY_GENERATION_ENABLED=true
SEED_QUERY_GENERATION_PROVIDER=openai
SEED_QUERY_GENERATION_MODEL=gpt-4.1-mini
SEED_QUERY_GENERATION_TIMEOUT_SECONDS=30
```

Use existing project configuration conventions where equivalent settings already exist.

## Provider Output

The provider must be prompted to return JSON only:

```json
{
  "queries": [
    {
      "text": "string",
      "type": "brand_direct"
    }
  ]
}
```

Post-processing must:

- parse JSON strictly
- require a top-level `queries` array
- reject or filter items with missing/empty text
- reject or filter unknown query types
- trim text
- deduplicate suggestions
- enforce the 20-query total limit
- return safe warnings when fewer suggestions are returned

Recommended coverage for 10 suggestions:

```text
brand_direct: 1
category_discovery: 2
recommendation: 2
comparison: 2
alternative: 1
problem_solution: 2
```

## Frontend UX

The old frontend-only mock `Query expansion · 15 tokens` control is replaced by the new generation UX. Do not keep both.

Do not show fake token costs in the MVP. Use neutral text such as:

```text
Generate 10 queries
```

Seed queries are edited through a row-based editor:

```text
[text input] [type badge/select] [remove button]
```

Generated suggestions are inserted as rows in the same list as manual queries.

## Non-Goals

- No async generation job system.
- No generation history.
- No automatic audit run after generation.
- No scoring changes.
- No audit-id-only generation endpoint for MVP.
- No fake token-cost UI.
- No DNS or domain availability checks.
