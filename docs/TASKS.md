# TASKS_PHASE_K.md

# Phase K — OpenAI Stabilization + Provider Diagnostics

Phase goal:

Stabilize the OpenAI real-provider path before adding Anthropic/Claude.

This phase should make OpenAI the baseline real provider for the SCDL audit pipeline:

```text
create audit
→ generate or manually enter typed seed queries
→ save audit
→ click Start audit
→ backend runs full pipeline
→ UI polls status
→ terminal status appears
→ summary/results/sources render
```

No CLI post-processing should be required after the user clicks Start audit.

Claude/Anthropic must not be implemented in Phase K.

---

## Phase K Task Order

```text
TASK-K175 — Document provider contract
TASK-K176 — Add OpenAI one-click verification checklist
TASK-K177 — Run checklist and capture actual issues
TASK-K178 — Normalize provider error model
TASK-K179 — Add provider diagnostics to API
TASK-K180 — Add provider diagnostics UI
TASK-K181 — Add provider parity checklist
TASK-K182 — Stabilize OpenAI one-click happy path based on captured issues
TASK-K183 — Finalize OpenAI provider baseline and Claude readiness decision
```

---

# Global Rules for Phase K

- Do not add Claude/Anthropic.
- Do not change parser/scoring unless explicitly required by a task.
- Do not fix unrelated legacy failures.
- Do not expose raw provider responses, raw prompts, stack traces, request headers, API keys, or secrets.
- No real provider calls in CI.
- Use mock providers for automated tests.
- Real OpenAI verification must be manual/dev-only.
- Frontend must never call provider APIs directly.
- Backend remains the source of truth for provider execution, normalization, diagnostics, parser input, scoring input, and safety.
- Normal frontend code must not call `/dev/...` endpoints.
- Keep changes task-scoped.

---

# TASK-K175 — Document Provider Contract

## Goal

Add or confirm a compact, practical provider contract document that defines the normalized interface for real and mock AI providers used by the SCDL audit pipeline.

This task is documentation-only. Do not change runtime code.

If `docs/PROVIDER_CONTRACT.md` already exists and matches the requirements below, treat this task as completed after a short review/alignment pass.

## File

```text
docs/PROVIDER_CONTRACT.md
```

## Requirements

The document must define:

1. Core provider principles
2. SCDL level behavior:
   - `L1 = AI answer without web access`
   - `L2 = AI answer with web access`
3. Normalized provider input shape
4. Normalized provider output shape
5. Normalized source/citation shape
6. Normalized usage metadata shape
7. Normalized provider error model
8. L1/L2 behavior rules
9. Provider configuration rules
10. Raw response handling rules
11. Logging and diagnostics rules
12. API/frontend diagnostics rules
13. Testing rules
14. Provider parity checklist
15. Rules for adding a new provider

## Acceptance criteria

- `docs/PROVIDER_CONTRACT.md` exists.
- Document is compact and practical.
- It defines normalized provider input/output/error/usage/source shapes.
- It defines L1/L2 behavior.
- It defines safe frontend diagnostics rules.
- It defines raw response safety rules.
- It defines CI/testing rules.
- It includes provider parity checklist.
- It explicitly says Anthropic/Claude is future work, not part of this task.
- No runtime code is changed.

## Non-goals

- Do not implement provider error model yet.
- Do not change OpenAI adapter.
- Do not change mock provider.
- Do not add Claude/Anthropic.
- Do not change frontend.
- Do not change audit pipeline.
- Do not change parser/scoring.

---

# TASK-K176 — Add OpenAI One-Click Verification Checklist

## Goal

Create a practical manual QA checklist for verifying that the OpenAI audit flow works end-to-end from UI without CLI/manual post-processing.

This task is documentation-only. Do not change runtime code.

## File to create

```text
docs/OPENAI_ONE_CLICK_VERIFICATION.md
```

## What “one-click” means

The user should be able to complete this flow from UI:

```text
login/register
→ create audit
→ fill brand fields
→ generate or manually enter typed seed queries
→ save audit
→ click Start audit
→ backend runs full pipeline
→ UI polls status
→ terminal status appears
→ summary/results/sources are visible
```

No CLI commands should be required after clicking Start audit.

No manual post-processing should be required.

## Required checklist structure

Each scenario should use this format:

```markdown
## K176-S01 — Scenario title

### Purpose
What this scenario verifies.

### Preconditions
- Backend state/config required.
- Frontend state required.
- User/account requirements.
- Provider/env requirements.

### Steps
1. Step one.
2. Step two.
3. Step three.

### Expected result
- Expected UI result.
- Expected backend/API behavior if observable.
- Expected audit status.
- Expected safety/security behavior.

### Failure notes
- What to record if the scenario fails.
```

## Required scenarios

### K176-S01 — Mock L1 one-click audit

Verify complete UI-to-pipeline flow without real provider dependency.

Must cover:

```text
create audit
manual seed query or generated query
SCDL L1
provider mock
Start audit from UI
polling
terminal status
summary/results visible
```

Expected:

```text
audit reaches completed or known valid terminal status
no CLI required
summary/results render
no raw provider response exposed
```

### K176-S02 — OpenAI L1 one-click audit

Verify real OpenAI L1 provider path.

Expected:

```text
OpenAI answer is saved
post-processing runs automatically
parsed/scored result appears
audit reaches completed/partial according to current status semantics
no web citations expected for L1
no raw provider response exposed to normal UI
```

### K176-S03 — OpenAI L2 one-click audit

Verify OpenAI L2 web-enabled path.

Expected:

```text
web-enabled provider path is used
audit reaches completed/partial according to current status semantics
summary/results render
sources/citations render if provider returns them
safe empty state if no sources returned
no raw provider response exposed
```

### K176-S04 — Typed seed queries survive save/reload/run

Verify that typed seed query data is preserved and used by pipeline.

Expected:

```text
query text persists
query type persists for generated typed queries
source persists as ai for generated queries even after text edit
manual query persists with source user
pipeline uses final visible query list
removed queries are not run
```

### K176-S05 — Legacy seed_queries compatibility

Verify that old audits or old API payloads using `seed_queries: list[str]` still work.

Expected:

```text
legacy queries load
legacy queries are treated as source user
missing type does not crash UI
save/reload does not corrupt queries
pipeline runs successfully
```

### K176-S06 — Provider disabled error

Precondition example:

```text
REAL_PROVIDER_ENABLED=false
PROVIDER_MODE=openai
```

Expected:

```text
Start audit does not silently fallback to mock
audit/run fails or blocks with safe provider diagnostic
error code should be PROVIDER_DISABLED if implemented
UI shows safe actionable message
no raw stack trace
no secrets
```

### K176-S07 — Missing OpenAI API key error

Precondition example:

```text
REAL_PROVIDER_ENABLED=true
PROVIDER_MODE=openai
OPENAI_API_KEY unset
```

Expected:

```text
Start audit does not silently fallback to mock
safe provider error is shown or captured
error code should be NO_API_KEY if implemented
no raw env/config dump
no secrets
```

### K176-S08 — Caps / guardrails behavior

Precondition example:

```text
REAL_PROVIDER_MAX_PROVIDERS=1
REAL_PROVIDER_MAX_QUERIES=1
REAL_PROVIDER_MAX_RUNS_PER_QUERY=1
REAL_PROVIDER_MAX_TOTAL_RUNS=1
```

Expected:

```text
backend enforces cap
provider is not called for excess runs
UI shows safe message or audit becomes partial according to current semantics
no silent overrun
```

### K176-S09 — Polling and terminal refetch

Verify frontend polling behavior after Start audit.

Expected:

```text
polling stops on completed/partial/failed
summary is not stale
results are not stale
sources are not stale
Start button state is correct after terminal status
```

### K176-S10 — Provider timeout / forced provider failure

Use safest available method:

```text
very low OPENAI_REQUEST_TIMEOUT_SECONDS
mock provider forced failure
or invalid model if timeout is hard to force
```

Expected:

```text
safe provider error is recorded
audit reaches failed or partial according to current status semantics
UI displays safe error
no raw provider response
no stack trace
no secrets
```

### K176-S11 — Mobile one-click flow smoke test

Expected:

```text
no hidden hover-only controls required
Start audit is accessible
seed query rows are editable/removable
status and diagnostics are readable
```

### K176-S12 — Old mock Query expansion control is gone

Expected:

```text
only one seed query generation control is visible
no "Query expansion · 15 tokens" mock control remains
generation calls backend endpoint
no fake token-cost UI is shown
```

## Required result table

At the end of the checklist, include a result table:

```markdown
| Scenario | Status | Notes | Issue ID |
|---|---|---|---|
| K176-S01 | Not run |  |  |
| K176-S02 | Not run |  |  |
| K176-S03 | Not run |  |  |
```

Allowed statuses:

```text
Not run
Pass
Fail
Blocked
Partial
```

## Required issue capture section

Add a section:

```markdown
# Captured Issues
```

With this template:

```markdown
## ISSUE-K176-001 — Short title

### Scenario
K176-Sxx

### Severity
Blocker | Major | Minor | Cosmetic

### Actual result
What happened.

### Expected result
What should have happened.

### Evidence
Screenshot/log/API response if available.

### Suggested next step
Fix now / defer / needs investigation.
```

## Acceptance criteria

- `docs/OPENAI_ONE_CLICK_VERIFICATION.md` exists.
- It contains all required scenarios K176-S01 through K176-S12.
- Each scenario has purpose, preconditions, steps, expected result, and failure notes.
- It includes a result table.
- It includes a captured issues template.
- It clearly states that no CLI/manual post-processing should be required after clicking Start audit.
- It clearly states that no raw provider responses, raw prompts, stack traces, or secrets should be exposed in normal UI.
- No runtime code is changed.

## Non-goals

- Do not run the checklist in this task.
- Do not fix OpenAI bugs in this task.
- Do not add Claude/Anthropic.
- Do not change provider adapters.
- Do not change frontend behavior.
- Do not change backend runtime code.
- Do not change scoring/parser logic.

---

# TASK-K177 — Run OpenAI One-Click Verification and Capture Actual Issues

## Goal

Run the manual verification checklist from:

```text
docs/OPENAI_ONE_CLICK_VERIFICATION.md
```

Capture actual pass/fail results and create a concrete issue list for stabilization.

This task is primarily verification/documentation. Do not fix bugs unless they are tiny test/setup corrections explicitly required to complete verification.

## Files to update/create

Update:

```text
docs/OPENAI_ONE_CLICK_VERIFICATION.md
```

Optional, if the team prefers separate result logs:

```text
docs/OPENAI_ONE_CLICK_VERIFICATION_RESULTS.md
```

## Required scenarios to run

Run all scenarios from `docs/OPENAI_ONE_CLICK_VERIFICATION.md`:

```text
K176-S01 — Mock L1 one-click audit
K176-S02 — OpenAI L1 one-click audit
K176-S03 — OpenAI L2 one-click audit
K176-S04 — Typed seed queries survive save/reload/run
K176-S05 — Legacy seed_queries compatibility
K176-S06 — Provider disabled error
K176-S07 — Missing OpenAI API key error
K176-S08 — Caps / guardrails behavior
K176-S09 — Polling and terminal refetch
K176-S10 — Provider timeout / forced provider failure
K176-S11 — Mobile one-click flow smoke test
K176-S12 — Old mock Query expansion control is gone
```

If a scenario cannot be run, mark it as:

```text
Blocked
```

and explain why.

## Issue capture format

For every failed, partial, or blocked scenario, add an issue using this format:

```markdown
## ISSUE-K177-001 — Short title

### Scenario
K176-Sxx

### Severity
Blocker | Major | Minor | Cosmetic

### Actual result
What happened.

### Expected result
What should have happened.

### Evidence
Screenshot/log/API response if available.

### Suggested next step
Fix now / defer / needs investigation.
```

## Acceptance criteria

- All K176 scenarios are marked as `Pass`, `Fail`, `Blocked`, or `Partial`.
- Every non-pass scenario has a captured issue.
- Issues include severity, actual result, expected result, evidence, and suggested next step.
- The document clearly states whether OpenAI one-click flow is ready for stabilization or blocked by setup.
- No secrets/API keys are committed.
- No runtime code changes are made, unless a tiny setup/doc correction is necessary and explicitly documented.
- No unrelated bugs are fixed.

## Non-goals

- Do not fix the captured issues in this task.
- Do not add provider diagnostics yet.
- Do not add provider parity checklist yet.
- Do not add Claude/Anthropic.
- Do not change scoring/parser.
- Do not change the pipeline design.

---

# TASK-K178 — Normalize Provider Error Model

## Goal

Implement a normalized backend provider error model based on:

```text
docs/PROVIDER_CONTRACT.md
```

Provider errors from mock/OpenAI/current provider execution must be converted into safe, structured, frontend-safe error objects.

This task should not add UI diagnostics yet. It prepares the backend error layer for API/UI diagnostics in later tasks.

## Required implementation

### 0. Normalize provider setup and selection failures

Provider failures are not limited to `adapter.query()` exceptions.

Normalize provider-related failures that happen before the provider call as well:

```text
provider factory errors
provider disabled/config errors
missing provider API key
pilot policy/cap errors
unsupported provider/mode errors
unsupported SCDL level errors
```

These failures must use the same normalized provider error model and must remain safe for API/UI exposure.

### 1. Add normalized error code enum

Add a backend enum equivalent to:

```python
class ProviderErrorCode(str, Enum):
    PROVIDER_DISABLED = "PROVIDER_DISABLED"
    NO_API_KEY = "NO_API_KEY"
    INVALID_API_KEY = "INVALID_API_KEY"
    INVALID_MODEL = "INVALID_MODEL"
    UNSUPPORTED_L2 = "UNSUPPORTED_L2"
    TIMEOUT = "TIMEOUT"
    RATE_LIMIT = "RATE_LIMIT"
    EMPTY_RESPONSE = "EMPTY_RESPONSE"
    INVALID_RESPONSE = "INVALID_RESPONSE"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    PROVIDER_REQUEST_FAILED = "PROVIDER_REQUEST_FAILED"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    UNKNOWN_PROVIDER_ERROR = "UNKNOWN_PROVIDER_ERROR"
```

Use the project’s existing enum/schema conventions if they differ.

### 2. Add normalized provider error DTO/model

Add a backend model equivalent to:

```python
class NormalizedProviderError(BaseModel):
    code: ProviderErrorCode
    message: str
    provider: str
    model: str | None = None
    level: Literal["L1", "L2"] | None = None
    retryable: bool = False
    details: dict[str, Any] = Field(default_factory=dict)
```

Rules:

```text
message must be safe for frontend display
details must be secret-free
details must not include raw provider response bodies
details must not include raw prompts
details must not include request headers
details must not include API keys
details must not include stack traces
```

### 3. Add error normalization helpers

Add helper functions/classes to convert common provider failures to normalized errors.

Recommended helpers:

```python
provider_disabled_error(provider: str, model: str | None, level: str | None) -> NormalizedProviderError
no_api_key_error(provider: str, model: str | None, level: str | None) -> NormalizedProviderError
invalid_model_error(provider: str, model: str | None, level: str | None) -> NormalizedProviderError
unsupported_l2_error(provider: str, model: str | None) -> NormalizedProviderError
timeout_error(provider: str, model: str | None, level: str | None) -> NormalizedProviderError
rate_limit_error(provider: str, model: str | None, level: str | None) -> NormalizedProviderError
empty_response_error(provider: str, model: str | None, level: str | None) -> NormalizedProviderError
invalid_response_error(provider: str, model: str | None, level: str | None) -> NormalizedProviderError
provider_request_failed_error(provider: str, model: str | None, level: str | None) -> NormalizedProviderError
unknown_provider_error(provider: str, model: str | None, level: str | None) -> NormalizedProviderError
```

Exact structure may vary, but the mapping layer should be explicit and reusable.

### 4. Map existing provider statuses/errors

If current provider response uses statuses like:

```python
ProviderStatus = Literal["success", "error", "timeout", "rate_limited"]
```

Map them as follows:

```text
timeout      -> TIMEOUT
rate_limited -> RATE_LIMIT
error        -> PROVIDER_REQUEST_FAILED or more specific code if available
success with empty/blank raw_answer -> EMPTY_RESPONSE
invalid/unparseable provider response -> INVALID_RESPONSE
```

If existing error dict already contains a known code, preserve it only if it is in `ProviderErrorCode`.

Otherwise map to `PROVIDER_REQUEST_FAILED` or `UNKNOWN_PROVIDER_ERROR`.

### 5. Normalize OpenAI adapter errors

Update OpenAI provider adapter error handling so common failures become normalized errors.

Minimum expected mapping:

```text
missing OPENAI_API_KEY      -> NO_API_KEY
provider disabled/config off -> PROVIDER_DISABLED
timeout                     -> TIMEOUT
rate limit                  -> RATE_LIMIT
invalid model/config         -> INVALID_MODEL or CONFIGURATION_ERROR
empty answer                 -> EMPTY_RESPONSE
invalid response shape       -> INVALID_RESPONSE
other provider request error -> PROVIDER_REQUEST_FAILED
unknown exception            -> UNKNOWN_PROVIDER_ERROR
```

Do not leak OpenAI raw error payloads to frontend-safe error fields.

### 6. Normalize mock adapter errors

Mock provider should be able to produce deterministic normalized failures for tests.

Examples:

```text
mock timeout -> TIMEOUT
mock rate limit -> RATE_LIMIT
mock empty response -> EMPTY_RESPONSE
mock unsupported L2 -> UNSUPPORTED_L2
```

Do not break existing deterministic mock success behavior.

### 7. Keep API shape changes minimal

This task is backend error model preparation.

Do not redesign public API response DTOs yet unless required internally.

Detailed API exposure is for:

```text
TASK-K179 — Add provider diagnostics to API
```

However, internal models should be ready for API exposure.

## Safety requirements

Normalized provider errors must not include:

```text
API keys
authorization headers
request headers
raw prompts
raw provider responses
stack traces
environment dumps
full exception repr if it contains sensitive data
```

## Tests to add/update

Add task-scoped backend tests.

### Unit tests for error DTO/helpers

Test:

```text
each ProviderErrorCode exists
helper returns expected code/message/provider/retryable
details are optional and default to {}
serialization is JSON-safe
```

### Provider status mapping tests

Test:

```text
timeout status -> TIMEOUT
rate_limited status -> RATE_LIMIT
generic error status -> PROVIDER_REQUEST_FAILED
success with empty answer -> EMPTY_RESPONSE
unknown error code -> PROVIDER_REQUEST_FAILED or UNKNOWN_PROVIDER_ERROR
```

### OpenAI adapter error tests

Mock the OpenAI client; do not make real calls.

Test:

```text
missing key -> NO_API_KEY
timeout exception -> TIMEOUT
rate limit exception -> RATE_LIMIT
invalid model/config -> INVALID_MODEL or CONFIGURATION_ERROR
empty answer -> EMPTY_RESPONSE
invalid response shape -> INVALID_RESPONSE
generic OpenAI request failure -> PROVIDER_REQUEST_FAILED
unknown exception -> UNKNOWN_PROVIDER_ERROR
```

### Mock provider tests

Test deterministic mock failures if the mock provider supports/gets failure modes.

```text
mock timeout -> TIMEOUT
mock rate limit -> RATE_LIMIT
mock empty response -> EMPTY_RESPONSE
mock unsupported L2 -> UNSUPPORTED_L2
```

### Safety tests

Test that normalized frontend-safe error serialization does not include obvious sensitive fields:

```text
api_key
authorization
headers
raw_response
prompt
stack_trace
traceback
```

## Acceptance criteria

- `ProviderErrorCode` exists.
- Normalized provider error DTO/model exists.
- Reusable error normalization helpers exist.
- Current provider statuses/errors map to normalized codes.
- OpenAI common errors normalize to safe provider errors.
- Mock provider can produce deterministic normalized failure outputs for tests.
- Empty successful answers become `EMPTY_RESPONSE`.
- No raw provider response, raw prompt, stack trace, API key, or request headers appear in normalized frontend-safe errors.
- Task-scoped backend tests pass.
- Touched-file ruff passes.

## Non-goals

- Do not add provider diagnostics UI.
- Do not expose a new diagnostics block in frontend yet unless required internally.
- Do not add Claude/Anthropic.
- Do not redesign provider adapter architecture beyond what is necessary for normalized errors.
- Do not change parser/scoring behavior.
- Do not change audit status semantics unless current code cannot represent normalized provider failures.
- Do not fix unrelated legacy failures.

---

# TASK-K179 — Add Provider Diagnostics to API

## Goal

Expose normalized provider diagnostics through backend API responses in a safe, structured way.

This task builds on:

```text
TASK-K178 — Normalize provider error model
docs/PROVIDER_CONTRACT.md
```

The goal is to make provider failures visible to frontend and users without exposing raw provider responses, prompts, stack traces, request headers, API keys, or secrets.

Do not implement UI rendering in this task. UI work belongs to `TASK-K180`.

## API surfaces to update

Add provider diagnostics where provider execution failures are visible or actionable.

Minimum targets:

```text
POST /audits/{id}/run-pipeline
GET /audits/{id}/status
GET /audits/{id}/results
GET /audits/{id}/summary
```

If the project has run-level detail endpoints, include diagnostics there too.

Do not expose diagnostics on unrelated endpoints.

## Diagnostic DTO

Add a frontend-safe API DTO equivalent to:

```python
class ProviderDiagnosticDTO(BaseModel):
    code: str
    message: str
    provider: str
    model: str | None = None
    level: Literal["L1", "L2"] | None = None
    retryable: bool = False
```

Optional fields if already useful:

```python
run_id: int | str | None = None
query_id: int | str | None = None
```

Avoid exposing `details` by default unless project policy explicitly allows a safe allowlist.

## Response shape

Use the project’s existing DTO style.

For single failure response:

```json
{
  "provider_error": {
    "code": "NO_API_KEY",
    "message": "OpenAI API key is not configured.",
    "provider": "openai",
    "model": "gpt-4.1-mini",
    "level": "L1",
    "retryable": false
  }
}
```

For audit status / summary with multiple runs:

```json
{
  "provider_diagnostics": [
    {
      "code": "TIMEOUT",
      "message": "OpenAI request timed out.",
      "provider": "openai",
      "model": "gpt-4.1-mini",
      "level": "L2",
      "retryable": true,
      "run_id": 123,
      "query_id": 45
    }
  ]
}
```

For result rows:

```json
{
  "query": "Best SEO agencies in Finland",
  "status": "failed",
  "provider_error": {
    "code": "TIMEOUT",
    "message": "OpenAI request timed out.",
    "provider": "openai",
    "model": "gpt-4.1-mini",
    "level": "L2",
    "retryable": true
  }
}
```

## Required behavior

### Pipeline run endpoint

`POST /audits/{id}/run-pipeline` should return safe diagnostics if provider execution fails.

If the pipeline completes with partial usable data:

```text
return current successful response shape
include provider_diagnostics if relevant
audit status may be partial according to current status semantics
```

If the pipeline fails due to provider configuration/error:

```text
return safe error response or normal pipeline response with failed status
include provider_error/provider_diagnostics
do not expose raw exception
```

Use current project error-handling style if it already has a clear convention.

### Audit status endpoint

`GET /audits/{id}/status` should include provider diagnostics when audit is:

```text
failed
partial
running with failed runs already recorded, if applicable
```

### Results endpoint

`GET /audits/{id}/results` should expose per-result or per-run provider diagnostics for failed/partial runs.

Rules:

```text
successful result rows should not need provider_error
failed result rows should include provider_error if available
legacy failed rows without normalized error should show safe generic diagnostic
```

Generic fallback:

```json
{
  "code": "UNKNOWN_PROVIDER_ERROR",
  "message": "Provider request failed.",
  "provider": "openai",
  "retryable": false
}
```

### Summary endpoint

`GET /audits/{id}/summary` should include aggregate provider diagnostics if relevant.

If multiple runs fail with the same error, deduplicate diagnostics where reasonable.

Do not let diagnostic aggregation break existing summary response.

## Safety requirements

API diagnostics must not include:

```text
API keys
authorization headers
request headers
raw prompts
raw provider responses
stack traces
tracebacks
environment dumps
full exception repr if it contains sensitive data
```

Allowed fields:

```text
code
message
provider
model
level
retryable
run_id
query_id
```

Only include `details` if an explicit allowlist is implemented.

## Storage/source-of-truth rule

Prefer deriving provider diagnostics from existing execution storage:

```text
raw_responses.error_object
raw_responses.provider_metadata
runs.status
jobs/audit pipeline summary where applicable
```

Do not add new database columns/tables unless diagnostics cannot be derived from existing storage.

If new storage is required:

```text
add an Alembic migration
document why existing storage is insufficient
keep the migration task-scoped
```

## Backward compatibility

Do not break existing frontend contracts.

Rules:

```text
existing fields remain available
diagnostic fields are additive
legacy audits without normalized provider errors still load
legacy failed runs get generic safe diagnostic if needed
successful audits without provider errors should behave as before
```

## Tests to add/update

Add task-scoped backend/API tests.

### Pipeline endpoint tests

Test:

```text
provider config error returns/exposes safe provider_error
provider timeout returns/exposes safe provider_error
partial audit response can include provider_diagnostics
successful audit response does not include unsafe diagnostic data
```

### Status endpoint tests

Test:

```text
failed audit includes provider_diagnostics
partial audit includes provider_diagnostics
successful audit has empty/omitted provider_diagnostics according to chosen DTO style
legacy failed audit does not crash
```

### Results endpoint tests

Test:

```text
failed run row includes provider_error
successful row does not include provider_error or has null according to chosen style
legacy failed run gets safe generic diagnostic
no raw provider response in result DTO
```

### Summary endpoint tests

Test:

```text
summary includes aggregate provider_diagnostics for failed provider runs
duplicate diagnostics are deduplicated if implemented
summary remains backward-compatible
no raw provider response/prompt/secrets included
```

### Safety tests

Assert serialized API response does not contain obvious sensitive keys:

```text
api_key
authorization
headers
raw_response
raw_prompt
prompt
stack_trace
traceback
OPENAI_API_KEY
sk-
```

## Acceptance criteria

- Provider diagnostics DTO exists for API responses.
- Pipeline run endpoint can expose safe provider error/diagnostics.
- Audit status endpoint can expose safe provider diagnostics.
- Results endpoint can expose per-run provider error where relevant.
- Summary endpoint can expose aggregate provider diagnostics where relevant.
- Existing API fields remain backward-compatible.
- Legacy failed provider runs do not crash diagnostics serialization.
- No raw provider responses, raw prompts, stack traces, request headers, API keys, or secrets appear in API diagnostics.
- Task-scoped backend/API tests pass.
- Touched-file ruff passes.

## Non-goals

- Do not implement frontend UI rendering.
- Do not add Claude/Anthropic.
- Do not change provider adapter architecture beyond using normalized errors from K178.
- Do not redesign audit status semantics.
- Do not change parser/scoring behavior.
- Do not expose raw provider response inspection in user-facing APIs.
- Do not fix unrelated legacy failures.

---

# TASK-K180 — Add Provider Diagnostics UI

## Goal

Display safe provider diagnostics in the frontend UI using the provider diagnostic fields added in:

```text
TASK-K179 — Add Provider Diagnostics to API
```

The UI should make provider failures understandable to users without exposing raw provider responses, prompts, stack traces, request headers, API keys, or secrets.

## Required UI surfaces

Add provider diagnostic display to these areas if they exist:

```text
Audit detail/status page
Audit summary page
Audit results table
Pipeline start/run action feedback
```

Optional, if already easy:

```text
Audit list/dashboard row status
```

## Frontend types

Add or update frontend API types to include provider diagnostics.

Suggested types:

```ts
export type ProviderDiagnosticCode =
  | "PROVIDER_DISABLED"
  | "NO_API_KEY"
  | "INVALID_API_KEY"
  | "INVALID_MODEL"
  | "UNSUPPORTED_L2"
  | "TIMEOUT"
  | "RATE_LIMIT"
  | "EMPTY_RESPONSE"
  | "INVALID_RESPONSE"
  | "PROVIDER_UNAVAILABLE"
  | "PROVIDER_REQUEST_FAILED"
  | "CONFIGURATION_ERROR"
  | "UNKNOWN_PROVIDER_ERROR"

export type ProviderDiagnostic = {
  code: ProviderDiagnosticCode
  message: string
  provider: string
  model?: string | null
  level?: "L1" | "L2" | null
  retryable?: boolean
  runId?: string | number | null
  queryId?: string | number | null
}
```

Use existing frontend naming conventions if different.

## Display rules

Show backend-provided safe `message`.

Do not derive low-level messages from raw errors.

Do not display diagnostic `details` unless backend exposes a strict safe allowlist.

Recommended pattern:

```text
Alert / Card
Title: Provider issue
Body: backend-safe message
Meta: provider, level, model, retryable
```

## Required behavior by page

### Audit detail/status page

If status response includes `provider_diagnostics`, display a diagnostics block.

Show it when:

```text
audit status is failed
audit status is partial
audit status is running and failed run diagnostics already exist
```

If no diagnostics exist, do not show an empty block.

### Pipeline start action feedback

When the user clicks `Start audit` and the pipeline response includes `provider_error` or `provider_diagnostics`, show the message near the start/action area.

Do not show raw API error bodies.

The Start button state must remain correct after error/terminal status.

### Summary page

If summary response includes aggregate `provider_diagnostics`, show a compact provider diagnostics card.

If there are multiple diagnostics:

- display unique diagnostics by `code + provider + level + model`
- show count if available or derivable from identical diagnostics
- keep the card compact

Do not let provider diagnostics break existing summary cards/charts.

### Results table

If a result row includes `provider_error`, show it inline for that failed row.

Suggested display:

```text
Status: failed
Provider issue: OpenAI request timed out.
```

If successful row has no diagnostic, show nothing extra.

## Safety requirements

Frontend must not display any field containing:

```text
api_key
authorization
headers
raw_response
raw_prompt
prompt
stack_trace
traceback
OPENAI_API_KEY
ANTHROPIC_API_KEY
sk-
```

If such fields appear unexpectedly in an API response, frontend should ignore them.

Frontend rendering must be whitelist-based. Render only these diagnostic fields:

```text
code
message
provider
model
level
retryable
runId
queryId
```

All other diagnostic fields must be ignored by UI components.

Do not add UI for raw response inspection in this task.

## Backward compatibility

Existing API responses without diagnostics must still render normally.

Rules:

```text
provider_diagnostics missing -> no diagnostics block
provider_diagnostics empty -> no diagnostics block
provider_error missing/null -> no diagnostics block
legacy failed audit without diagnostics -> existing UI behavior continues
```

## Tests to add/update

Add task-scoped frontend tests.

### Type/API tests

If frontend has API/client tests:

```text
parses provider_error
parses provider_diagnostics
handles missing diagnostics
handles empty diagnostics
```

### Audit detail/status UI tests

Test:

```text
renders diagnostics block when provider_diagnostics exists
does not render diagnostics block when missing/empty
shows provider/message/level/model/retryable
does not show unsafe fields if present
```

### Pipeline action tests

Test:

```text
Start audit response with provider_error shows safe message
Start audit response with provider_diagnostics shows safe message
Start button state remains usable/correct after provider error
```

### Summary UI tests

Test:

```text
summary diagnostics card renders aggregate diagnostics
summary without diagnostics renders normally
multiple diagnostics render compactly
```

### Results table tests

Test:

```text
failed row with provider_error displays message
successful row without provider_error does not show provider issue
unsafe fields are ignored
```

## Acceptance criteria

- Frontend types support `provider_error` and `provider_diagnostics`.
- Audit detail/status page displays provider diagnostics safely.
- Pipeline start action displays provider errors safely.
- Summary page displays aggregate diagnostics safely.
- Results table displays row-level provider errors safely.
- Existing successful/legacy audits without diagnostics render as before.
- Unsafe fields are not rendered.
- No raw provider responses, raw prompts, stack traces, request headers, API keys, or secrets are displayed.
- Task-scoped frontend tests pass.
- TypeScript passes for touched files.

## Non-goals

- Do not add Claude/Anthropic.
- Do not change backend API contracts beyond consuming K179 fields.
- Do not implement raw response inspection UI.
- Do not change scoring/parser behavior.
- Do not redesign audit status semantics.
- Do not add retry buttons unless already supported by backend.
- Do not fix unrelated frontend bugs.

---

# TASK-K181 — Add Provider Parity Checklist

## Goal

Create a provider parity checklist document that defines the minimum support matrix and verification criteria for each AI provider.

This checklist will be used before adding Anthropic/Claude and before marking any real provider as supported.

This task is documentation-only. Do not change runtime code.

## File to create

```text
docs/PROVIDER_PARITY.md
```

## Required document structure

### 1. Purpose

Explain that this checklist is used to:

```text
- compare provider capabilities
- prevent provider-specific behavior from leaking into parser/scoring/frontend
- confirm L1/L2 support status
- confirm normalized output/error/usage/source behavior
- define readiness before marking a provider as supported
```

### 2. Provider support matrix

Create a table like:

```markdown
| Provider | Status | L1 | L2 | Notes |
|---|---|---|---|---|
| mock | supported for tests/dev | yes | configurable/mock only | deterministic; no real calls |
| openai | active real provider | yes | yes | via Responses API web tools |
| anthropic | planned | planned | not assumed | initial target: L1 only |
```

Use actual project status if it differs.

### 3. Required parity checklist

Add a checklist template that every provider must satisfy.

```markdown
## Provider: <provider_name>

### Capability
- [ ] Adapter implemented
- [ ] L1 supported
- [ ] L2 supported or explicitly unsupported
- [ ] Unsupported L2 returns `UNSUPPORTED_L2`
- [ ] No silent fallback from L2 to L1
- [ ] No silent fallback from real provider to mock
- [ ] Configured model is used; no silent model replacement

### Normalized output
- [ ] Successful response maps to normalized answer text
- [ ] Empty answer maps to `EMPTY_RESPONSE`
- [ ] Raw response is internally storable if needed
- [ ] Raw response is not exposed to normal frontend endpoints
- [ ] Sources/citations normalize to provider source shape
- [ ] Missing sources are handled safely
- [ ] Usage normalizes when available
- [ ] Missing usage does not fail the run

### Normalized errors
- [ ] Provider disabled maps to `PROVIDER_DISABLED`
- [ ] Missing API key maps to `NO_API_KEY`
- [ ] Invalid API key maps to `INVALID_API_KEY`
- [ ] Invalid model/config maps to `INVALID_MODEL` or `CONFIGURATION_ERROR`
- [ ] Timeout maps to `TIMEOUT`
- [ ] Rate limit maps to `RATE_LIMIT`
- [ ] Invalid provider response maps to `INVALID_RESPONSE`
- [ ] Provider request failure maps to `PROVIDER_REQUEST_FAILED`
- [ ] Unknown exception maps to `UNKNOWN_PROVIDER_ERROR`
- [ ] Retryable errors are marked correctly

### Safety
- [ ] No API keys in API responses
- [ ] No request headers in API responses
- [ ] No raw prompts in frontend-safe responses
- [ ] No raw provider responses in frontend-safe responses
- [ ] No stack traces in frontend-safe responses
- [ ] No secrets in logs/snapshots
- [ ] Provider metadata is JSON-serializable and secret-free

### Testing
- [ ] Unit tests use mocked provider/client calls
- [ ] CI does not call real provider APIs
- [ ] L1 success test exists
- [ ] L2 success test exists if supported
- [ ] Unsupported L2 test exists if unsupported
- [ ] Timeout test exists
- [ ] Rate-limit test exists
- [ ] Missing key test exists
- [ ] Invalid model/config test exists
- [ ] Empty response test exists
- [ ] Invalid response test exists
- [ ] Source normalization test exists if provider can return sources
- [ ] Usage normalization test exists if provider returns usage
- [ ] No-secret-leakage test exists

### Manual verification
- [ ] One-query L1 audit verified manually
- [ ] One-query L2 audit verified manually if supported
- [ ] Unsupported L2 verified manually if not supported
- [ ] Provider disabled scenario verified
- [ ] Missing key scenario verified
- [ ] Timeout/failure scenario verified if feasible
- [ ] Summary/results render after execution
- [ ] Sources/citations render or safe empty state appears
- [ ] Provider diagnostics render safely in UI
```

### 4. Mock provider checklist

Add an initial section for `mock`.

Expected status:

```text
Mock provider is required for deterministic local/test execution.
Mock provider is not a real visibility source.
Mock provider must never be silently used as fallback when a real provider is configured.
```

Checklist should mark or state:

```text
L1: supported for tests/dev
L2: supported only as deterministic simulation if implemented
Real calls: never
CI: yes, allowed
```

### 5. OpenAI provider checklist

Add an initial section for `openai`.

Expected status:

```text
OpenAI is the first active real provider.
L1 is supported.
L2 is supported through Responses API web/search tools.
```

Use statuses:

```text
Done
Partial
Not verified
Not supported
Planned
```

Do not pretend unknown items are done.

### 6. Anthropic/Claude future checklist

Add a future section for `anthropic`.

Expected status:

```text
Anthropic is future work.
Initial target is L1 only.
L2 is not assumed.
Unsupported L2 must return UNSUPPORTED_L2 until explicitly implemented and verified.
```

### 7. Provider readiness definition

A provider may be marked as supported only if:

```text
- adapter is implemented
- supported SCDL levels are explicit
- unsupported levels return normalized errors
- output normalization is implemented
- error normalization is implemented
- no silent fallback exists
- safety/no-secret-leakage tests pass
- CI uses mock tests only
- manual one-query verification passes
- provider diagnostics are visible in API/UI when failures occur
```

## Acceptance criteria

- `docs/PROVIDER_PARITY.md` exists.
- It includes purpose and provider support matrix.
- It includes a reusable checklist template.
- It includes initial `mock` section.
- It includes initial `openai` section.
- It includes future `anthropic` section.
- It defines provider readiness criteria.
- It states that Anthropic/Claude is future work and must not be implemented in this task.
- It states that mock must not be used as silent fallback for real providers.
- It states that CI must not call real providers.
- No runtime code is changed.

## Non-goals

- Do not implement Claude/Anthropic.
- Do not modify OpenAI adapter.
- Do not modify mock provider.
- Do not modify frontend.
- Do not modify backend runtime code.
- Do not run provider verification.
- Do not change parser/scoring.

---

# TASK-K182 — Stabilize OpenAI One-Click Happy Path Based on Captured Issues

## Goal

Fix only the concrete OpenAI one-click flow issues captured during:

```text
TASK-K177 — Run OpenAI One-Click Verification and Capture Actual Issues
```

This task should turn the OpenAI path into a stable UI-driven flow:

```text
create audit
→ generate or manually enter typed seed queries
→ save audit
→ click Start audit
→ backend runs full pipeline
→ UI polls status
→ terminal status appears
→ summary/results/sources render
```

No CLI post-processing should be required.

## Required input

Before starting this task, read:

```text
docs/OPENAI_ONE_CLICK_VERIFICATION.md
docs/OPENAI_ONE_CLICK_VERIFICATION_RESULTS.md
docs/PROVIDER_CONTRACT.md
docs/PROVIDER_PARITY.md
```

If `docs/OPENAI_ONE_CLICK_VERIFICATION_RESULTS.md` does not exist, use the result table and captured issues section inside:

```text
docs/OPENAI_ONE_CLICK_VERIFICATION.md
```

## Scope rule

Only fix issues explicitly captured in `TASK-K177`.

Do not broaden this task into general refactoring.

Do not fix issues that were not captured in K177 unless they directly block verification of a captured K177 issue.
If such a blocker appears, document it in the verification results before fixing it.

Allowed issue categories:

```text
OpenAI one-click pipeline failures
typed seed query execution issues
pipeline post-processing not running automatically
polling/refetch stale state
provider caps/guardrail bugs
provider diagnostics not surfaced correctly after K178–K180
summary/results/sources not updating after terminal status
Start audit button state bugs
safe provider error display bugs
mobile blockers for the one-click path
```

Not allowed:

```text
adding Claude/Anthropic
changing scoring methodology
redesigning parser
redesigning audit status model
rewriting provider architecture
fixing unrelated legacy failures
adding new product features
```

## Functional requirements

### One-click execution

After user clicks `Start audit`:

```text
backend schedules/executes jobs
raw responses are saved
post-processing runs automatically
parsed results are saved
scores are saved
summary/results/sources reflect data
final audit status is set
```

No manual commands should be required:

```text
scripts/process_audit_results.py
scripts/run_audit_pipeline.py
```

### Typed seed query compatibility

Verify and fix if needed:

```text
pipeline uses final saved seed_query_items
legacy seed_queries list[str] still works
generated query source remains ai after edit
manual query source is user
removed queries are not run
query type does not break execution
```

### Provider diagnostics

Verify and fix if needed:

```text
NO_API_KEY shown safely
PROVIDER_DISABLED shown safely
TIMEOUT shown safely
RATE_LIMIT shown safely if reproducible
INVALID_MODEL shown safely if reproducible
no raw prompt exposed
no raw response exposed
no stack trace exposed
no API key exposed
```

### Polling/refetch

Verify and fix if needed:

```text
polling starts when audit becomes running
polling stops on completed/partial/failed
audit detail refetches after terminal status
summary refetches after terminal status
results refetch after terminal status
sources refetch after terminal status
audit list/dashboard invalidates if applicable
Start button state is correct after terminal status
```

### Status semantics

Do not redesign status semantics.

Use existing project meanings:

```text
created
running
completed
partial
failed
```

Expected behavior:

```text
completed — all expected runs terminal and processed/accounted for
partial — usable results exist but some runs/processing failed/skipped
failed — no usable data or fatal pipeline error
```

Provider success but parser does not find the brand is not a provider failure.

### Caps/guardrails

Verify and fix if needed:

```text
REAL_PROVIDER_MAX_PROVIDERS
REAL_PROVIDER_MAX_QUERIES
REAL_PROVIDER_MAX_RUNS_PER_QUERY
REAL_PROVIDER_MAX_TOTAL_RUNS
```

Rules:

```text
caps are enforced before provider execution
excess runs are not sent to real provider
UI/API gets safe explanation when cap blocks execution
no silent overrun
```

## Tests to add/update

Add task-scoped tests based on the specific captured issues.

### Backend

```text
pipeline endpoint runs execution + post-processing
OpenAI provider success creates parsed/scored results
typed seed query items are used by pipeline
legacy seed_queries are still accepted
provider config errors return safe diagnostics
caps prevent excess provider runs
terminal status set correctly
```

Use mocked provider calls for automated tests.

No real OpenAI calls in CI.

### Frontend

```text
Start audit triggers pipeline endpoint
polling starts and stops correctly
terminal status invalidates/refetches summary/results/sources
provider diagnostics render after provider failure
duplicate Start submissions are prevented
typed seed query UI works through save/run if relevant
```

### Safety

Assert API/UI output does not contain:

```text
api_key
authorization
headers
raw_response
raw_prompt
prompt
stack_trace
traceback
OPENAI_API_KEY
sk-
```

## Verification after fixes

Re-run relevant failed/partial scenarios from:

```text
docs/OPENAI_ONE_CLICK_VERIFICATION.md
```

At minimum re-run all scenarios that were:

```text
Fail
Partial
Blocked
```

If time allows, re-run:

```text
K176-S01 — Mock L1 one-click audit
K176-S02 — OpenAI L1 one-click audit
K176-S03 — OpenAI L2 one-click audit
K176-S04 — Typed seed queries survive save/reload/run
K176-S09 — Polling and terminal refetch
```

Update the verification results document.

## Acceptance criteria

- All blocker issues from K177 are fixed or explicitly marked blocked by environment/setup.
- Major one-click path issues are fixed or explicitly deferred with rationale.
- OpenAI L1 one-click flow works from UI without CLI post-processing.
- OpenAI L2 one-click flow works from UI or fails safely with normalized diagnostics.
- Typed seed queries are used correctly by pipeline.
- Polling/refetch behavior is correct after terminal status.
- Provider diagnostics render safely where relevant.
- Caps/guardrails do not silently overrun real provider limits.
- No raw provider responses, raw prompts, stack traces, request headers, API keys, or secrets are exposed in API/UI.
- Task-scoped backend/frontend tests pass.
- Touched-file ruff/typecheck pass.
- Verification results are updated.

## Non-goals

- Do not add Claude/Anthropic.
- Do not implement new provider adapters.
- Do not redesign provider abstraction.
- Do not redesign scoring/parser.
- Do not add new query generation features.
- Do not fix unrelated legacy failures.
- Do not perform broad UI redesign.

---

# TASK-K183 — Finalize OpenAI Provider Baseline and Claude Readiness Decision

## Goal

Finalize Phase K by documenting whether OpenAI is stable enough to be used as the baseline real provider and whether the project is ready to start Anthropic/Claude integration.

This is primarily documentation/review. Runtime code changes should be avoided unless they are tiny documentation alignment fixes.

## Required input

Read:

```text
docs/PROVIDER_CONTRACT.md
docs/PROVIDER_PARITY.md
docs/OPENAI_ONE_CLICK_VERIFICATION.md
docs/OPENAI_ONE_CLICK_VERIFICATION_RESULTS.md
```

Also inspect recent implementation notes from:

```text
TASK-K178
TASK-K179
TASK-K180
TASK-K182
```

## Files to update

Update:

```text
docs/PROVIDER_PARITY.md
docs/OPENAI_ONE_CLICK_VERIFICATION.md
```

Optional new file:

```text
docs/CLAUDE_READINESS_DECISION.md
```

## Work items

### 1. Update OpenAI parity status

In `docs/PROVIDER_PARITY.md`, update the OpenAI section based on actual implementation and verification.

Use statuses:

```text
Done
Partial
Not verified
Not supported
Planned
Blocked
```

Must cover:

```text
Adapter implemented
L1 supported
L2 supported
Unsupported L2 handling
Normalized answer_text
Normalized sources
Normalized usage
Normalized errors
API diagnostics
UI diagnostics
No secret leakage
Mock tests only in CI
Manual one-click verification
Caps/guardrails
Typed seed query execution
```

Do not mark unknown items as `Done`.

### 2. Summarize OpenAI baseline readiness

Add a short section:

```markdown
# OpenAI Baseline Readiness
```

Include one of:

```text
Ready
Ready with known limitations
Not ready
```

Recommended format:

```markdown
## OpenAI Baseline Readiness

Status: Ready with known limitations

Evidence:
- OpenAI L1 one-click audit: Pass
- OpenAI L2 one-click audit: Pass/Partial
- Provider diagnostics: Pass
- Typed seed queries through pipeline: Pass

Known limitations:
- ...
```

### 3. Decide Claude readiness

Add a section:

```markdown
# Claude Readiness Decision
```

Allowed decisions:

```text
Proceed to Claude L1 adapter
Do not proceed yet
Proceed only after specific blockers are fixed
```

Decision criteria:

Proceed only if:

```text
OpenAI L1 one-click flow works
provider errors are normalized
provider diagnostics are visible in API/UI
no silent fallback exists
mock CI path is stable
provider contract is current
provider parity checklist exists
```

Do not require OpenAI L2 perfection if Claude initial target is L1 only, but any known provider-layer blocker must be fixed first.

### 4. Define Claude initial scope if proceeding

If decision is `Proceed to Claude L1 adapter`, define initial scope:

```text
Anthropic/Claude L1 only
No L2 web search
No silent fallback
No parser/scoring changes
No frontend redesign
No raw response exposure
Mocked tests only in CI
Manual one-query Claude L1 verification required
```

Explicitly state:

```text
Claude L2 is unsupported until designed and verified.
Claude L2 requests must return UNSUPPORTED_L2.
```

### 5. Capture blockers if not proceeding

If decision is `Do not proceed yet`, list blockers:

```markdown
## Blockers Before Claude

| Blocker | Severity | Required fix |
|---|---|---|
| ... | Blocker | ... |
```

## Acceptance criteria

- `docs/PROVIDER_PARITY.md` OpenAI section is updated with actual status.
- OpenAI baseline readiness is explicitly stated.
- Claude readiness decision is explicitly stated.
- If proceeding, Claude initial scope is limited to L1 only.
- If not proceeding, blockers are listed.
- No unknown items are marked as done.
- No runtime code is changed.
- No Claude/Anthropic adapter is implemented.

## Non-goals

- Do not add Anthropic/Claude.
- Do not change OpenAI adapter.
- Do not change provider diagnostics.
- Do not change frontend.
- Do not change parser/scoring.
- Do not fix new bugs in this task.
