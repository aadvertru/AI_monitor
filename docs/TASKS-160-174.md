# TASKS.md

# Phase J — Seed Query Generation

This phase adds controlled AI-assisted seed query generation for SCDL audits.

Core product decision:

- Seed query generation is optional.
- Manual seed query input remains supported.
- The user must always be able to review, edit, remove, and manually add queries before running an audit.
- Generated seed queries are suggestions, not automatically persisted audit input.
- Backend remains the source of truth for validation, limits, ownership, scoring, aggregation, and safe response contracts.
- Frontend may provide UX validation and defensive soft deduplication, but backend must enforce final validation.
- Seed query generation must work from unsaved form state on the create audit page.

Global implementation constraints:

- Do not fix unrelated legacy failures inside feature tasks.
- Run task-scoped tests.
- Run ruff/typecheck only for touched files or according to the existing project convention.
- Do not modify unrelated parser/scoring behavior unless the task explicitly requires it.
- Do not expose raw AI prompts, raw provider responses, API keys, or secrets in frontend responses.
- Do not call `/dev/...` endpoints from normal frontend code.
- Do not make seed query generation part of the audit pipeline.
- Do not automatically run an audit after generating seed queries.
- Do not require an audit id for seed query suggestion generation.
- Do not persist generated suggestions before explicit user confirmation/save.

---

# Phase J1 — Generation MVP

J1 goal:

The user can generate 10 typed seed query suggestions from current form-state brand domain and/or brand description, review/edit/delete them, deduplicate them, keep the total query count within 20, and persist only the final confirmed query list.

Generation must support both:

- create audit page, where the audit may not exist yet
- edit audit page, where the audit may already exist

For this reason, generation uses a draft-safe suggestion endpoint that accepts current form values instead of reading only persisted audit data.

---

## TASK-J160 — Define Seed Query Generation Contract

### Goal

Document the backend/frontend contract for seed query generation before implementation.

The contract must define:

- generation input payload
- generation response shape
- fixed seed query types
- limits
- sync behavior
- persistence rules
- domain/description priority rules
- deduplication responsibilities
- provider/config behavior
- backward compatibility rules for manual/legacy queries
- non-goals

### Suggested documentation location

Add a new document:

```text
docs/SEED_QUERY_GENERATION.md
```

or update existing project documentation if that is the current convention:

```text
docs/PRODUCT_SPEC.md
docs/ARCHITECTURE.md
docs/TASKS.md
```

### Endpoint

Use a draft-safe endpoint:

```http
POST /audit-seed-query-suggestions
```

Do not use an audit-id-only endpoint for the MVP generation flow.

Rationale:

- On the create audit page, the audit may not exist yet.
- Brand domain and description may exist only in unsaved form state.
- The generation request must use the current visible form values, not stale persisted audit values.

### Request payload

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

### Response payload

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

### Fixed seed query types

```text
brand_direct
category_discovery
recommendation
comparison
alternative
problem_solution
```

### Limits

```text
default generated count: 10
max generated count per request: 10
max total seed queries per audit/form: 20
count > 10: reject with 422 Unprocessable Entity
```

### Deduplication responsibilities

Backend must:

- validate incoming `existing_queries`
- deduplicate generated suggestions internally
- deduplicate generated suggestions against `existing_queries`
- enforce available slots based on max total count of 20
- return skipped duplicate/limit counts and warnings
- filter invalid/empty/unknown-type provider suggestions

Frontend must:

- pass the current visible form query list as `existing_queries`
- defensively deduplicate returned suggestions before appending
- show returned warnings
- keep total visible query count at or below 20

### Required rules

- Generation is optional.
- Manual seed query input remains supported.
- Generation is synchronous for the MVP.
- Generated suggestions are not persisted automatically.
- Suggestions are persisted only after user confirmation/save.
- Description is the primary signal when available.
- Domain is a weak signal.
- If both domain and description are selected, description takes priority.
- Domain may be used for disambiguation, brand identity, and niche hints.
- Domain must not override clear brand description context.
- Backend and frontend must both protect against duplicate/invalid suggestions.

### Provider/config behavior

For MVP:

```text
Seed query generation uses OpenAI only when generation is enabled and OpenAI configuration is available.
SEED_QUERY_GENERATION_ENABLED=false returns 503 Service Unavailable.
Production/OpenAI mode with missing OpenAI config returns 503 Service Unavailable.
Deterministic mock suggestions are allowed only in explicit mock/dev/test mode.
```

Add or document config settings if they do not already exist:

```text
SEED_QUERY_GENERATION_ENABLED=true
SEED_QUERY_GENERATION_PROVIDER=openai
SEED_QUERY_GENERATION_MODEL=gpt-4.1-mini
SEED_QUERY_GENERATION_TIMEOUT_SECONDS=30
```

Use existing project configuration conventions if equivalent settings already exist.

### Backward compatibility

For final saved seed queries:

```text
seed_query_items:
- new canonical typed field for final saved seed queries
- each item carries text/type/source

seed_queries:
- legacy plain-text list kept for backward compatibility
- derived from seed_query_items in detail responses
- accepted in create/update requests for legacy clients

If both seed_queries and seed_query_items are provided in the same create/update request:
- return 422 Unprocessable Entity
- do not guess which field is authoritative

source:
- optional in incoming save payload
- defaults to "user" if omitted

type:
- required when source = "ai"
- optional/nullable when source = "user"
```

Legacy/manual seed queries must not break.

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

### Acceptance criteria

- The generation contract is documented.
- The draft-safe endpoint is documented.
- Request payload includes current brand form data and `existing_queries`.
- Response payload includes suggestions and warning metadata.
- Allowed query types are documented.
- Sync generation behavior is explicit.
- Persistence rule is explicit: generated suggestions are not saved before user confirmation.
- Limits are explicit.
- `count > 10` returns 422.
- Domain/description priority is explicit.
- Backend/frontend deduplication responsibilities are explicit.
- Provider/config behavior is explicit.
- Backward compatibility rules are explicit.
- `seed_query_items` is documented as the canonical save/detail field.
- Sending both `seed_queries` and `seed_query_items` in one save request is documented as 422.

### Non-goals

- No async job system.
- No query generation history.
- No automatic audit run after generation.
- No scoring changes in this task.
- No audit-id-only generation endpoint for MVP.

---

## TASK-J161 — Add Seed Query Type and Source Model Support

### Goal

Add fixed seed query typing and minimal provenance support without breaking manual or legacy seed query flows.

### Required enums

Add a fixed seed query type enum:

```python
class SeedQueryType(str, Enum):
    brand_direct = "brand_direct"
    category_discovery = "category_discovery"
    recommendation = "recommendation"
    comparison = "comparison"
    alternative = "alternative"
    problem_solution = "problem_solution"
```

Add a seed query source enum:

```python
class SeedQuerySource(str, Enum):
    user = "user"
    ai = "ai"
```

### Required behavior

- Manual queries get `source = "user"` when source is omitted.
- AI-generated suggestions get `source = "ai"` after the user confirms/saves them.
- `type` must be valid if provided.
- Generated/AI queries must always have a valid `type`.
- Manual queries must remain supported even when they do not have a type.
- If the current legacy model stores seed queries as strings, extend the schema carefully without breaking existing audit creation/editing flows.

### Storage and migration

Add an Alembic migration in this task.

If seed queries are stored as individual rows, add:

```text
queries.query_type nullable
queries.source not null default "user"
```

If the project stores seed queries as JSON/list in another table, migrate toward a structure that can store:

```json
{
  "text": "What is Seopaja?",
  "type": "brand_direct",
  "source": "ai"
}
```

without breaking existing `list[str]` create/edit flows.

Existing persisted queries become:

```text
source = "user"
query_type = null
```

Do not require a cleanup/backfill migration that invents query types for legacy rows.

### Backward compatibility rules

For incoming final saved seed query payloads:

```text
seed_query_items is the canonical typed field
seed_queries remains accepted as a legacy plain-text list
if both seed_queries and seed_query_items are provided -> 422
```

```text
source omitted → default to "user"
source = "user" → type may be valid enum or null/omitted
source = "ai" → type is required and must be valid enum
```

For legacy persisted data:

```text
missing source → treat as "user"
missing type → allowed for user/manual/legacy query
```

### Migration nuance

If existing audits have untyped seed queries, do not break them.

Acceptable options:

- allow nullable `type` for legacy/manual rows
- default source to `user` when omitted
- avoid backfilling type unless the project has a clear migration rule

Generated AI queries must not be nullable by contract.

### Important nuance

If the user edits an AI-generated suggestion before saving, `source` remains `ai`.

`source` represents provenance, not legal ownership of the final text.

### Acceptance criteria

- Fixed query type enum exists.
- Source enum exists.
- Generated queries can carry `type` and `source`.
- Alembic migration adds storage support for query type/source.
- Source defaults to `user` when omitted in final save payloads.
- Type is required only for `source = "ai"`.
- Manual queries remain supported with nullable/omitted type.
- Existing audit creation flow does not break.
- `seed_query_items` is accepted as canonical input.
- Legacy `seed_queries: list[str]` input still works.
- Sending both `seed_queries` and `seed_query_items` returns 422.
- Existing persisted queries are treated as `source="user"` and `query_type=null`.

### Tests

- Known seed query types are accepted.
- Unknown seed query type is rejected.
- Unknown source is rejected.
- AI-generated query without type is rejected.
- Manual query with omitted source defaults to `user`.
- Manual query with omitted type is accepted.
- Legacy-style query payload still works according to current product behavior.
- Canonical `seed_query_items` payload saves text/type/source.
- Sending both legacy and canonical seed query fields is rejected.
- Migration test verifies query type/source columns and defaults.

### Non-goals

- No scoring logic.
- No UI diagnostics.
- No cleanup migration for old query data unless required by the schema change.

---

## TASK-J162 — Add Backend Validation for Seed Query Limits

### Goal

Make the backend the source of truth for final saved seed query limits and validity.

### Validation rules

For final saved audit seed queries:

```text
seed_query_items is the canonical typed save field
seed_queries remains accepted as a legacy plain-text list
if both seed_queries and seed_query_items are provided -> 422
max total seed queries per audit: 20
query text is required
query text cannot be whitespace-only
query type must be valid if provided
generated/ai query type is required
query source must be user or ai if provided
query source defaults to user if omitted
```

### Recommended text limits

Add reasonable limits if no project-wide limits exist yet:

```text
min query length: 3 characters after trim
max query length: 300 characters
```

Rationale:

300 characters is enough for a realistic AI/search prompt and prevents users from pasting whole paragraphs into seed queries.

### Normalization

Before saving:

```text
trim leading/trailing whitespace
collapse excessive internal whitespace if consistent with existing project style
```

Do not aggressively rewrite user input.

### Backend error behavior

If validation fails, use existing project conventions.

Recommended:

```http
422 Unprocessable Entity
```

### Acceptance criteria

- Backend rejects more than 20 seed queries.
- Backend rejects empty queries.
- Backend rejects whitespace-only queries.
- Backend validates query type enum.
- Backend validates source enum.
- Backend defaults omitted source to `user`.
- Backend requires type only when source is `ai`.
- Backend accepts `seed_query_items` as canonical input.
- Backend still accepts legacy `seed_queries: list[str]`.
- Backend rejects requests containing both `seed_queries` and `seed_query_items`.
- Existing manual seed query flow still works.

### Tests

- 20 queries are accepted.
- 21 queries are rejected.
- Empty query is rejected.
- Whitespace-only query is rejected.
- Unknown type is rejected.
- Unknown source is rejected.
- Omitted source defaults to `user`.
- Valid manual query without type is accepted.
- Valid AI-generated query with type is accepted.
- AI-generated query without type is rejected.
- Legacy `seed_queries: list[str]` is accepted and stored as user/null type.
- Canonical `seed_query_items` is accepted and stores text/type/source.
- Sending both seed query fields returns 422.

### Non-goals

- No AI generation.
- No frontend work.
- No scoring changes.

---

## TASK-J163 — Add AI Seed Query Generation Service

### Goal

Add a backend service that synchronously generates typed seed query suggestions from current form-state brand domain and/or brand description.

The service must not require an existing audit id.

### Suggested location

Use the existing service layout if one already exists.

Possible location:

```text
apps/api/services/seed_query_generation.py
```

### Service input

```python
GenerateSeedQueriesInput(
    brand_name: str | None,
    brand_domain: str | None,
    brand_description: str | None,
    use_domain: bool,
    use_description: bool,
    count: int = 10,
    existing_queries: list[SeedQueryDraft] = [],
)
```

### Service output

```python
GeneratedSeedQueriesResult(
    suggestions=[
        GeneratedSeedQuerySuggestion(
            text="Best SEO agencies in Finland",
            type="category_discovery",
            source="ai",
        )
    ],
    skipped_duplicates=1,
    skipped_limit=0,
    warnings=["1 duplicate query was skipped."],
)
```

### Input validation

- `count` defaults to 10.
- `count` max is 10.
- `count > 10` is rejected with 422 Unprocessable Entity.
- At least one of `use_domain` or `use_description` must be true.
- If `use_domain = true`, `brand_domain` must be present and valid.
- If `use_description = true`, `brand_description` must be present and non-empty.
- `existing_queries` must be normalized/validated enough to support deduplication and limit checks.
- If `existing_queries` already has 20 or more valid queries, return no suggestions and a soft warning.

### Domain/description priority rules

If `use_description = true`:

```text
Brand description is the primary semantic signal.
```

If both domain and description are selected:

```text
Use domain only for disambiguation, brand identity, and niche hints.
Do not overfit generated queries to the domain string.
Do not let domain override clear description context.
```

If only domain is selected:

```text
Generate conservative suggestions based only on the domain and brand name.
Do not infer unsupported product claims.
```

### Required AI output schema

The provider must be prompted to return JSON matching this shape:

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

Allowed `type` values:

```text
brand_direct
category_discovery
recommendation
comparison
alternative
problem_solution
```

### Provider output validation

After receiving provider output:

- parse JSON strictly
- reject/handle output if top-level object is invalid
- require top-level `queries` array
- reject item if `text` is missing, empty, or whitespace-only
- reject item if `type` is not in enum
- trim text
- normalize text for deduplication
- deduplicate generated suggestions internally
- deduplicate generated suggestions against `existing_queries`
- enforce available slots based on max total count of 20
- return fewer than `count` suggestions if validation/dedup/limit removes items
- return safe warnings when fewer suggestions are returned

### Prompt constraints

The prompt must require:

- JSON-only output
- exactly `count` items if possible
- fixed query types only
- no markdown
- no explanations
- no duplicate or near-duplicate queries
- realistic user prompts
- not only branded queries
- multiple intent coverage

### Recommended distribution for 10 generated queries

```text
brand_direct: 1
category_discovery: 2
recommendation: 2
comparison: 2
alternative: 1
problem_solution: 2
```

This does not need to be mathematically rigid, but the prompt should request this coverage.

### Provider/API rules

- Use the existing provider/config infrastructure if available.
- If a separate generation provider does not exist yet, the MVP may use the existing OpenAI Responses API integration.
- Do not use Chat Completions unless the project has explicitly changed the provider decision.
- Do not expose raw prompts or raw provider responses to frontend responses.
- Do not log secrets.

### Provider/config behavior

For MVP:

```text
Seed query generation uses OpenAI only when generation is enabled and OpenAI configuration is available.
SEED_QUERY_GENERATION_ENABLED=false returns 503 Service Unavailable.
Production/OpenAI mode with missing OpenAI config returns 503 Service Unavailable.
Deterministic mock suggestions are allowed only in explicit mock/dev/test mode.
```

Add or document config settings if they do not already exist:

```text
SEED_QUERY_GENERATION_ENABLED=true
SEED_QUERY_GENERATION_PROVIDER=openai
SEED_QUERY_GENERATION_MODEL=gpt-4.1-mini
SEED_QUERY_GENERATION_TIMEOUT_SECONDS=30
```

Use existing project configuration conventions if equivalent settings already exist.

### Safe failure behavior

If provider output is invalid or unavailable, handle it safely.

Preferred service-level result:

```json
{
  "suggestions": [],
  "skipped_duplicates": 0,
  "skipped_limit": 0,
  "warnings": ["Seed query generation is currently unavailable."]
}
```

or raise a safe application error according to existing project conventions.

### Acceptance criteria

- Service accepts current form-state domain, description, or both.
- Service does not require an existing audit id.
- Service accepts `existing_queries`.
- Service returns typed suggestions.
- Service validates strict provider JSON output.
- Service filters invalid/empty/unknown-type items.
- Service deduplicates generated suggestions internally.
- Service deduplicates against `existing_queries`.
- Service enforces max total query count of 20.
- Service does not persist suggestions.
- Service handles invalid provider output safely.
- Service does not leak raw prompts, raw provider responses, or secrets.

### Tests

Use a mocked provider.

- Valid provider JSON returns structured suggestions.
- Invalid JSON is handled safely.
- Missing top-level `queries` is handled safely.
- Missing query text is filtered/rejected safely.
- Unknown query type is filtered/rejected safely.
- Duplicate provider suggestions are deduplicated.
- Duplicate suggestions against `existing_queries` are skipped.
- Existing query count near 20 limits returned suggestions.
- Provider timeout/error is handled safely.
- Generated suggestions are not persisted.

### Non-goals

- No frontend.
- No API endpoint.
- No async job.
- No scoring.

---

## TASK-J164 — Add Draft-Safe Seed Query Suggestion API Endpoint

### Goal

Add an authenticated draft-safe endpoint for synchronous seed query suggestion generation.

This endpoint must work before an audit exists.

### Endpoint

```http
POST /audit-seed-query-suggestions
```

### Request payload

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

### Response payload

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

### Validation

- User must be authenticated.
- `count` defaults to 10.
- `count` max is 10.
- `count > 10` returns 422 Unprocessable Entity.
- At least one of `use_domain` or `use_description` must be true.
- If `use_domain = true`, `brand_domain` must be present and valid.
- If `use_description = true`, `brand_description` must be present and non-empty.
- `existing_queries` must be accepted from current form state.
- If `existing_queries` already has 20 or more valid queries, return no suggestions and a soft warning.
- If brand domain validation exists elsewhere, reuse the same validation rules.

### Ownership/security nuance

This endpoint does not take `audit_id`, so audit ownership cannot be checked.

It still must:

- require authentication
- avoid exposing raw prompts/provider responses/secrets
- avoid persisting suggestions
- validate input strictly
- apply provider/cost guardrails

If the product later adds an audit-specific generation endpoint, that endpoint must enforce audit ownership.

### Provider/config behavior

```text
SEED_QUERY_GENERATION_ENABLED=false -> 503
PROVIDER_MODE=openai or SEED_QUERY_GENERATION_PROVIDER=openai without OpenAI config -> 503
PROVIDER_MODE=mock or SEED_QUERY_GENERATION_PROVIDER=mock -> deterministic mock suggestions allowed for dev/test
```

### Suggested HTTP behavior

Use existing project conventions if they differ.

For this phase, `count > 10` is explicitly a `422 Unprocessable Entity`.

Recommended:

```text
401 — unauthenticated
422 — invalid request
429 — generation limit/rate limit exceeded, if guardrails exist
503 — provider not configured or unavailable
```

### Persistence rule

This endpoint must return suggestions only.

It must not save generated suggestions as final audit seed queries.

### Acceptance criteria

- Endpoint exists.
- Endpoint enforces auth.
- Endpoint works without an audit id.
- Endpoint accepts current form-state brand data.
- Endpoint accepts `existing_queries`.
- Endpoint validates inputs.
- Endpoint returns safe structured suggestions and warning metadata.
- Endpoint does not persist suggestions.
- Frontend receives no raw prompt or raw provider response.

### Tests

- Unauthenticated request is rejected.
- Authenticated request is accepted.
- No selected source is rejected.
- Missing selected description is rejected.
- Missing selected domain is rejected.
- Invalid domain is rejected when `use_domain=true`.
- Count above 10 is rejected with 422.
- Existing query count of 20 returns no suggestions and warning.
- Suggestions are deduplicated against existing queries.
- Suggestions are not persisted.
- Provider error returns a safe response.

### Non-goals

- No audit-id endpoint.
- No UI.
- No scoring.
- No automatic addition to audit.
- No audit ownership check because no audit id is used.

---

## TASK-J165 — Add Frontend API Client Method

### Goal

Add a typed frontend API client method for draft-safe seed query suggestion generation.

### Method

```ts
generateSeedQuerySuggestions(payload: {
  brandName?: string | null
  brandDomain?: string | null
  brandDescription?: string | null
  useDomain: boolean
  useDescription: boolean
  count?: number
  existingQueries: SeedQueryDraft[]
}): Promise<GenerateSeedQuerySuggestionsResponse>
```

### Types

```ts
type SeedQueryType =
  | "brand_direct"
  | "category_discovery"
  | "recommendation"
  | "comparison"
  | "alternative"
  | "problem_solution"

type SeedQuerySource = "user" | "ai"

type SeedQueryDraft = {
  text: string
  type?: SeedQueryType | null
  source?: SeedQuerySource
}

type GeneratedSeedQuerySuggestion = {
  text: string
  type: SeedQueryType
  source: "ai"
}

type GenerateSeedQuerySuggestionsResponse = {
  suggestions: GeneratedSeedQuerySuggestion[]
  skippedDuplicates?: number
  skippedLimit?: number
  warnings?: string[]
}
```

### Endpoint

```http
POST /audit-seed-query-suggestions
```

### Requirements

- Keep naming consistent with existing frontend API client conventions.
- Do not call `/dev/...`.
- Do not require audit id.
- Send current visible form values.
- Send current visible seed query list as `existingQueries`.
- Map frontend camelCase fields to the backend snake_case payload.
- Do not persist suggestions automatically.
- Do not trigger audit run.

### Acceptance criteria

- API client method exists.
- Method does not require an audit id.
- Method sends current brand form data.
- Method sends `existingQueries`.
- Types are exported or reused where needed.
- Errors are handled consistently with existing API client behavior.

### Tests

- API client sends the correct payload.
- API client calls `/audit-seed-query-suggestions`.
- API client parses suggestions and warning metadata.
- API client propagates errors safely.

### Non-goals

- No UI.
- No scoring.

---

## TASK-J166 — Add Controlled Generation UI

### Goal

Add UI for controlled seed query generation based on current form-state brand domain and/or brand description.

### Suggested placement

Place the control near the seed query section on the create/edit audit page.

Replace the old frontend-only mock `Query expansion · 15 tokens` control. There must be only one seed query generation UX.

The UI may be:

- dialog
- popover
- inline panel
- drawer

For the MVP, use a dialog or inline panel unless the existing design system suggests otherwise.

### UI elements

```text
Generate seed queries

[ ] Use brand domain
[ ] Use brand description

Generate 10 queries
```

Do not show fake token costs in this MVP. Use neutral UI text such as:

```text
Generate 10 queries
```

User-facing generation cost/usage limits can be added in a later dedicated task.

### Seed query editor

Replace the seed query textarea with a row-based seed query editor.

MVP row:

```text
[text input] [type badge/select] [remove button]
```

Generated suggestions are inserted as rows in the same list as manual queries, not as a separate persisted block.

Manual rows:

```text
source = user
type = optional/null unless the user selects a type
```

Generated rows:

```text
source = ai
type = required
source remains ai even if the user edits the generated text
```

A bulk paste helper can be added later, but it is not required for the MVP.

### Source values

Use current form state, not only persisted audit data:

```text
brand_name: current form value
brand_domain: current form value
brand_description: current form value
existing_queries: current visible form query list
```

### Default selections

- If both domain and description are available in current form state, select both by default.
- If only description is available, select description by default.
- If only domain is available, select domain by default.
- If neither is available, disable the Generate button.

### Loading state

During generation:

```text
Generate button disabled
loading spinner or "Generating..."
form remains stable
```

### Error state

Show a safe error:

```text
Could not generate seed queries. Please try again or enter queries manually.
```

Do not show raw provider output.

### UX rule

Manual input must remain available at all times.

### Acceptance criteria

- User can open controlled generation UI.
- User can select domain and/or description sources.
- Old mock Query expansion control is removed or replaced.
- Seed queries are edited as rows, not as a plain textarea.
- UI uses current unsaved form values.
- Generate calls the draft-safe backend endpoint.
- Loading state works.
- Error state works.
- Backend warnings are displayed.
- No generated query is saved automatically.
- Manual editing remains possible.

### Tests

- Generation UI opens.
- Generate is disabled if no source is selected.
- Generate is disabled if selected source data is unavailable in current form state.
- Request uses current unsaved form values.
- Request includes current visible `existingQueries`.
- Loading state is shown during request.
- Error is displayed on failed request.
- Backend warnings are displayed on success.
- Success response is handed to append logic.
- Generated suggestions appear as editable seed query rows.

### Non-goals

- No scoring.
- No coverage UI.
- No async polling.

---

## TASK-J167 — Add Frontend Defensive Deduplication and Append Behavior

### Goal

After generation, add returned suggestions to the end of the current visible seed query list while defensively maintaining deduplication and total limit of 20.

Backend should already deduplicate suggestions, but frontend must still protect the visible form state.

The visible seed query list is the row-based editor introduced in TASK-J166, not the old textarea.

### Deduplication normalization

Compare returned suggestions against the current visible seed query list.

Minimum normalization:

```ts
query.trim().toLowerCase().replace(/\s+/g, " ")
```

Optional safe normalization:

```text
remove trailing punctuation if this does not create false positives
```

Do not use semantic/AI deduplication in this task.

### Behavior

- Exact normalized duplicate is skipped.
- Unique generated suggestion is appended to the end as a row with text/type/source.
- Existing manually entered queries remain unchanged.
- Existing generated queries remain unchanged.
- Generated rows keep `source = "ai"` even if the text is edited later.
- Total visible query count must not exceed 20.
- If returned suggestions exceed available slots, add only the available number.
- Show backend warnings.
- Show frontend defensive warnings if additional duplicates/limit truncation are detected.

### Soft warning examples

```text
3 duplicate queries were skipped.
Only 4 queries were added because the audit limit is 20 seed queries.
```

### Important nuance

Backend is responsible for primary validation/deduplication.

Frontend defensive deduplication is still required because visible form state can change between request start and response.

### Acceptance criteria

- Returned unique suggestions append to the end.
- Duplicates are skipped defensively.
- Total query count does not exceed 20.
- Backend warnings are displayed.
- Frontend warning appears when duplicates are skipped defensively.
- Frontend warning appears when max limit prevents adding all returned suggestions.
- Append behavior does not replace the existing list.

### Tests

- Adds unique suggestions.
- Skips duplicates.
- Respects max total count of 20.
- Appends rather than replaces.
- Existing manual queries remain unchanged.
- Displays backend warnings.
- Displays frontend warning for defensive duplicate skip.
- Displays frontend warning for defensive limit truncation.

### Non-goals

- No semantic deduplication.
- No scoring.

---

## TASK-J168 — Add Query Type Support in Seed Query UI

### Goal

Display and preserve query type for seed queries.

### UI behavior

For generated queries:

- show a small badge or select with the query type
- user can edit query text
- type remains attached when text is edited
- source remains `ai` when generated text is edited
- optional: user can change the type through a select

For MVP, a readonly badge is acceptable.

If the existing form structure makes it simple, prefer an editable select.

### User-facing labels

Map internal values to readable labels:

```text
brand_direct → Brand direct
category_discovery → Category discovery
recommendation → Recommendation
comparison → Comparison
alternative → Alternative
problem_solution → Problem-solution
```

Use enum values in payloads and storage, not labels.

### Manual queries

Preferred behavior:

- manual queries may optionally have a type
- if a default type is required, use `category_discovery`

Alternative acceptable behavior:

- manual queries may have nullable type if this is required for backward compatibility

### Acceptance criteria

- Generated queries show query type.
- Type is included when confirmed seed queries are saved.
- Type persists when query text is edited.
- Existing manual query UX remains usable.
- Invalid type cannot be selected from UI.
- Manual queries remain possible without forcing the user to understand query types.

### Tests

- Generated query displays correct type.
- Type persists through text edit.
- Source remains `ai` through text edit.
- Type is included in save payload.
- Manual query still works.
- Invalid type cannot be selected from UI.

### Non-goals

- No scoring.
- No diagnostics.
- No weighted score.

---

## TASK-J169 — Verify Generation Has No Persistence Side Effects

### Goal

Guarantee through tests and focused code review that AI-generated suggestions are persisted only after the user confirms/saves the final query list.

This is a verification/hardening task, not a new feature task.

### Correct flow

```text
Generate
→ backend returns suggestions
→ frontend deduplicates and appends suggestions to visible form state
→ user reviews/edits/deletes queries
→ user saves audit
→ backend persists the final visible list
```

### Explicitly forbidden behavior

- Do not save suggestions inside the suggestion endpoint.
- Do not create audit runs after generation.
- Do not change audit status after generation.
- Do not start the audit pipeline after generation.
- Do not write raw provider response as an audit result.
- Do not require an audit id for generation.

### Backend verification

Check that:

```http
POST /audit-seed-query-suggestions
```

does not write to audit execution/result tables, such as:

```text
seed_queries
audit_queries
audit_runs
raw_responses
parsed_results
scores
```

or their project-specific equivalents.

### Frontend behavior

Generated suggestions live only in form state before save.

If the user closes the page without saving, generated suggestions are lost.

This is acceptable for the MVP.

If the user edits a generated suggestion before saving, `source` remains `ai`; source is provenance, not a claim that the final text was never edited.

### Acceptance criteria

- Suggestion endpoint is generate-only.
- Generated suggestions are not persisted before save.
- Save persists only the final edited visible list.
- Removed generated suggestions are not persisted.
- Edited generated suggestions are persisted with `source = "ai"` and their valid query type.
- Audit status is unchanged by generation.
- No audit runs are created by generation.

### Tests

Backend:

- Before generation: N seed queries or no audit exists.
- After suggestion endpoint call: no seed queries are persisted.
- After user save: final visible list is persisted through the existing save flow.
- Audit status is unchanged by suggestion generation.
- Audit runs are not created by suggestion generation.

Frontend:

- Generate without save does not call the save endpoint.
- User can remove generated suggestion before save.
- Removed suggestion is not included in final save payload.

### Non-goals

- No draft autosave.
- No generation history.
- No async recovery after page refresh.

---

## TASK-J170 — Add Backend Tests for Generation Flow

### Goal

Add task-scoped backend tests for the seed query generation flow.

### Required test groups

#### Auth

- unauthenticated user is rejected
- authenticated user is accepted

#### Payload validation

- `use_domain=false` and `use_description=false` is rejected
- missing domain is rejected when `use_domain=true`
- invalid domain is rejected when `use_domain=true`
- missing description is rejected when `use_description=true`
- `count=10` is accepted
- `count>10` is rejected with 422
- `existing_queries` with 20 valid items returns no suggestions and warning

#### Provider behavior

- valid provider JSON returns suggestions
- invalid JSON is handled safely
- missing top-level `queries` is handled safely
- unknown query type is filtered or rejected safely
- empty query text is filtered or rejected safely
- duplicate provider suggestions are deduplicated
- duplicate suggestions against `existing_queries` are skipped
- provider error returns a safe error
- disabled generation returns 503
- OpenAI mode without required OpenAI config returns 503
- deterministic mock suggestions work only in explicit mock/dev/test mode

#### Persistence

- generation does not persist suggestions
- generation does not create runs
- generation does not change audit status
- generation works without audit id

#### Safety

- response does not include raw prompt
- response does not include raw provider response
- response does not include secrets

### Acceptance criteria

- Task-scoped backend tests pass.
- No unrelated legacy failures are fixed inside this task.
- Touched-file ruff passes.

### Non-goals

- No full test suite cleanup.
- No frontend tests.

---

## TASK-J171 — Add Frontend Tests for Generation Flow

### Goal

Add frontend tests for the seed query generation UI flow.

### Required tests

- Generate control appears near the seed query section.
- User can select domain/description.
- Generate is disabled when no source is selected.
- Generate is disabled when selected source data is unavailable in current form state.
- Generate sends current unsaved brand form values.
- Generate sends current visible `existingQueries`.
- Generate shows loading state.
- Successful generation appends suggestions.
- Duplicate suggestions are skipped defensively.
- Max total count of 20 is respected.
- Backend warnings are displayed.
- Frontend soft warning appears for defensive duplicates.
- Frontend soft warning appears for max-limit truncation.
- User can edit generated query text before saving.
- Edited generated query keeps `source = "ai"`.
- User can remove generated query before saving.
- Save sends the final edited query list.

### Mocking

Mock the frontend API client method:

```ts
generateSeedQuerySuggestions()
```

Do not call a real provider from frontend tests.

### Acceptance criteria

- Frontend task-scoped tests pass.
- TypeScript passes for touched files.
- Existing happy-path audit creation flow still works.

### Non-goals

- No E2E real provider test.
- No scoring UI.
- No coverage diagnostics.

---

# Phase J2 — Evaluation by Query Type

J2 goal:

Audit summaries can show visibility by query intent and calculate a weighted visibility score based on query type.

Important gate:

Do not implement J2 until J1 is merged, verified through UI, and at least one typed-query audit has been run successfully through the normal audit pipeline.

J2 depends on real stored query type data from confirmed seed queries.

---

## TASK-J172 — Add Query-Type Coverage Metrics

### Goal

Add backend aggregation by query type so the summary can show brand visibility across different query intents.

### Metrics

For each query type, return data similar to:

```json
{
  "type": "recommendation",
  "total_queries": 2,
  "processed_runs": 2,
  "failed_runs": 0,
  "brand_found_count": 1,
  "brand_found_rate": 0.5,
  "average_score": 0.42
}
```

Adapt exact field names to the current scoring/summary model.

### Data sources

Use backend data only:

- confirmed seed query type
- parsed result
- score
- run status

Frontend must not calculate these metrics.

### Terminal statuses

Use only terminal/accounted-for runs.

Recommended handling:

- processed successful runs contribute to score/rate denominator
- failed/skipped runs are reported separately as `failed_runs` or equivalent
- do not silently hide failed/skipped runs if they affect interpretation

### Legacy behavior

Old audits without query type must not break summary.

Acceptable handling:

- group them under `unknown`
- or assign neutral behavior with `type = null`

Choose the option that best matches the existing API style.

### Acceptance criteria

- Summary endpoint returns query-type coverage data.
- Existing summary fields remain backward-compatible.
- Missing query type is handled safely.
- Old audits without query types do not break summary.
- Frontend still does not calculate these metrics.

### Tests

- Aggregates by query type correctly.
- Handles brand found.
- Handles brand not found.
- Handles failed runs.
- Handles unknown/null legacy type.
- Existing summary tests still pass.

### Non-goals

- No frontend UI.
- No weighted scoring.
- No diagnostic prose generation.

---

## TASK-J173 — Add Query-Type Diagnostics to Summary UI

### Goal

Add a UI block that displays brand visibility by query type.

### MVP UI

A table or cards are both acceptable.

Example table:

| Query type | Queries | Brand found | Visibility |
|---|---:|---:|---:|
| Brand direct | 1 | 1 | 100% |
| Recommendation | 2 | 0 | 0% |
| Comparison | 2 | 1 | 50% |

### Optional rule-based diagnostic text

If simple and safe, add rule-based text such as:

```text
Brand is visible in direct queries, but weak in recommendations.
Brand appears in comparison queries, but not in category discovery.
```

For MVP, the table/cards are sufficient.

### Important rule

Frontend displays backend-provided summary data.

Frontend must not recalculate score.

### Empty state

If data is missing:

```text
Query-type diagnostics will appear after the audit has processed typed seed queries.
```

### Acceptance criteria

- Summary UI displays query-type metrics.
- UI handles missing data safely.
- UI handles partial audits.
- Existing summary page does not break.
- No frontend-side scoring is added.

### Tests

- Renders metrics when present.
- Renders empty state when absent.
- Handles partial/failed type data.
- Does not crash on legacy audits without query types.

### Non-goals

- No weighted scoring.
- No AI-generated diagnostic prose.
- No chart requirement unless Recharts is already convenient.

---

## TASK-J174 — Add Weighted Scoring by Query Type

### Goal

Add a weighted visibility score based on query type without breaking the existing general score.

### Initial weights

```text
brand_direct: 1.0
category_discovery: 1.2
recommendation: 1.5
comparison: 1.3
alternative: 1.2
problem_solution: 1.4
```

### Architecture rule

Do not replace the existing score unless the product explicitly decides to do so later.

Add a new field instead, for example:

```json
{
  "visibility_score": 0.48,
  "weighted_visibility_score": 0.56
}
```

Use project naming conventions if they differ.

### Formula

Recommended formula:

```text
weighted_score =
sum(query_score * query_type_weight) / sum(query_type_weight)
```

Only processed runs should contribute to the denominator.

Failed/skipped runs must be handled explicitly and must not silently corrupt the denominator.

### Legacy behavior

If query type is missing:

```text
weight = 1.0
```

### Calculation location

Backend scoring/aggregation layer only.

Frontend only displays the returned value.

### Acceptance criteria

- Weighted score is calculated on backend.
- Existing score remains available.
- Missing type defaults to weight `1.0`.
- Failed/skipped runs are handled explicitly.
- Summary endpoint exposes weighted score safely.

### Tests

- Weighted calculation is correct.
- Missing type uses weight `1.0`.
- Different query types produce expected weighted result.
- Failed runs do not silently corrupt denominator.
- Existing score tests remain valid.

### Non-goals

- No reprocessing of all historical audits unless required.
- No UI redesign.
- No user-editable weights in the MVP.

---

# Recommended Implementation Order

## J1 — Generation MVP

Implement first:

```text
TASK-J160
TASK-J161
TASK-J162
TASK-J163
TASK-J164
TASK-J165
TASK-J166
TASK-J167
TASK-J168
TASK-J169
TASK-J170
TASK-J171
```

Expected outcome:

```text
User can generate 10 typed seed queries from current form-state domain and/or description, review/edit/delete them, deduplicate them, keep max total count of 20, and save only confirmed queries.
```

## J2 — Evaluation by Query Type

Implement only after J1 is merged and live-verified:

```text
TASK-J172
TASK-J173
TASK-J174
```

Expected outcome:

```text
Audit summary can show visibility by query intent and calculate weighted score.
```

---

# Codex Execution Rules for This Phase

For every task:

```text
Implement only the requested task scope.
Do not fix unrelated legacy failures.
Run task-scoped tests.
Run touched-file ruff/typecheck or follow the existing project convention.
Do not expose raw AI prompts, raw provider responses, API keys, or secrets in frontend responses.
Do not modify unrelated parser/scoring behavior unless the task explicitly requires it.
Do not call /dev endpoints from normal frontend code.
Do not require audit id for seed query suggestion generation.
Do not persist generated suggestions before explicit user confirmation/save.
```
