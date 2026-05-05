# OpenRouter Gateway Verification

This document tracks manual verification for OpenRouter gateway execution.
No real API keys, raw prompts, request headers, raw provider responses, stack
traces, or secrets should be recorded here.

## Environment

Date: 2026-05-05

Live verification was run locally with backend/frontend development servers and
a locally configured OpenRouter API key. The key value was not inspected or
recorded.

Expected backend env for OpenRouter live verification:

```text
REAL_PROVIDER_ENABLED=1
PROVIDER_MODE=openrouter
OPENROUTER_API_KEY=<set locally, never recorded>
OPENROUTER_L1_MODEL=<allowlisted model id>
OPENROUTER_L2_MODEL=<allowlisted model id>
OPENROUTER_ALLOWED_MODELS=<comma-separated allowlist>
OPENROUTER_WEB_SEARCH_ENABLED=true for L2 scenarios
```

Known valid model-id rule: OpenRouter model ids must not include a leading `~`.
For example, use `google/gemini-2.0-flash-001`, not
`~google/gemini-2.0-flash-001`.

## Result Table

| Scenario | Status | Notes | Issue |
|---|---|---|---|
| OR-S01 | Pass | OpenRouter L1 gateway execution was manually verified with routed Gemini/Claude-style model ids after correcting model config. | - |
| OR-S02 | Blocked | OpenRouter L2 web-search execution still needs a dedicated live run with `OPENROUTER_WEB_SEARCH_ENABLED=true` and an L2 model. | ISSUE-OR-003 |
| OR-S03 | Blocked | L2 source/citation rendering still needs a real L2 response with sources or a confirmed safe empty state. | ISSUE-OR-003 |
| OR-S04 | Covered by tests | Missing-key behavior is covered by mocked config/provider tests; live restart with key unset was not repeated. | - |
| OR-S05 | Pass | Invalid/not-allowlisted model was observed in UI as a safe provider diagnostic; no secret/raw payload exposure was seen. | ISSUE-OR-001 |
| OR-S06 | Covered by tests | Web-search-disabled behavior is covered by mocked OpenRouter provider tests; live restart was not repeated. | - |
| OR-S07 | Covered by tests | Provider-mode guardrails are covered by pilot/factory tests. | - |
| OR-S08 | Covered by tests | No-fallback behavior is covered by factory/pipeline/guardrail tests. | - |
| OR-S09 | Partial | Typed seed query create/edit/save was manually exercised; OpenRouter L1 execution consumes saved query text. Full L2 typed-query run remains pending with OR-S02. | - |
| OR-S10 | Pass | Safe provider diagnostics were visible for invalid model/config failure; no key/header/raw prompt/raw response/stack trace was exposed in normal UI. | ISSUE-OR-001 |

## OR-S01 - OpenRouter L1 one-click audit

Purpose: verify a normal L1 audit runs through OpenRouter gateway without web
search.

Expected result:

- audit reaches terminal completed/partial state
- execution uses OpenRouter gateway
- configured OpenRouter model id is used
- no sources are required for L1
- no fallback to OpenAI/mock/native Anthropic

Actual result: Pass. OpenRouter L1 execution was manually verified after
correcting model ids and restarting backend config. Routed Gemini and
Claude-style model ids were exercised through OpenRouter. Incorrect model ids
produce safe diagnostics rather than falling back.

## OR-S02 - OpenRouter L2 experimental one-click audit

Purpose: verify a normal L2 audit runs through OpenRouter gateway web-search
server tool.

Expected result:

- request path uses configured OpenRouter L2 model
- metadata includes `gateway_l2_experimental=true`
- `web_search_tool=openrouter:web_search`
- no fallback to L1/OpenAI/mock

Actual result: Blocked/pending. The code path is implemented and covered by
mocked tests, but a dedicated live L2 web-search run has not been completed.

## OR-S03 - L2 sources or safe empty state

Purpose: verify L2 source rendering when sources are returned and safe empty
state when sources are missing.

Expected result:

- sources are normalized when OpenRouter returns citations/annotations
- missing sources do not fail usable answer
- safe empty sources state is shown
- no raw annotations/tool results are exposed

Actual result: Blocked/pending until OR-S02 is run with a live L2 response.

## OR-S04 - Missing OpenRouter key

Purpose: verify missing key maps to safe diagnostics.

Expected result:

- no external call
- normalized `NO_API_KEY`
- no key names/secrets/headers/raw prompt/raw response in API or UI

Actual result: Covered by mocked tests. Live backend restart with the key unset
was not repeated during this verification pass.

## OR-S05 - Invalid or not-allowlisted model

Purpose: verify model routing policy blocks invalid models before execution.

Expected result:

- no silent fallback
- normalized `INVALID_MODEL` or `CONFIGURATION_ERROR`
- frontend-safe diagnostic does not dump full allowlist or secrets

Actual result: Pass. Invalid model configuration was observed in the UI as a
safe provider diagnostic. The root cause was an incorrectly configured model id
and was resolved by using a valid OpenRouter model id.

## OR-S06 - Web search disabled for L2

Purpose: verify L2 refuses to run when web search is disabled.

Expected result:

- no OpenRouter client call
- normalized `CONFIGURATION_ERROR`
- no fallback to L1

Actual result: Covered by mocked provider tests. Live backend restart with web
search disabled was not repeated.

## OR-S07 - Provider mode guardrail

Purpose: verify `PROVIDER_MODE` blocks the wrong real provider.

Expected result:

- OpenRouter audit does not run unless `PROVIDER_MODE=openrouter`
- safe fatal error/diagnostic
- no fallback to configured native provider or mock

Actual result: Covered by pilot/factory tests. OpenRouter gateway providers are
only routed through the OpenRouter adapter in OpenRouter mode.

## OR-S08 - No fallback

Purpose: verify failures do not fallback to another provider or level.

Expected result:

- OpenRouter L1 failure does not fallback to OpenAI/Anthropic/mock
- OpenRouter L2 failure does not fallback to L1/native OpenAI/mock
- final status and diagnostics make failure visible

Actual result: Covered by tests and live invalid-model diagnostics. Invalid
model/config failures stayed visible and did not silently use another provider.

## OR-S09 - Typed seed queries

Purpose: verify typed seed query save/load/edit flow still runs through gateway
pipeline.

Expected result:

- generated/manual typed queries persist
- edited generated query keeps provenance
- pipeline consumes final saved query texts
- summary/results render normally

Actual result: Partial. Typed query create/edit/save behavior was manually
exercised. Gateway L1 execution consumes saved query text. Full L2 typed-query
verification remains pending with OR-S02.

## OR-S10 - Unsafe data not exposed

Purpose: verify diagnostics and UI remain secret-safe.

Expected result:

- no API keys, authorization headers, raw prompts, raw responses, stack traces,
  `Bearer`, raw annotations, or raw tool results appear in normal API/UI
- provider diagnostics show safe code/message/provider/model/level only

Actual result: Pass for invalid model/config diagnostics. No unsafe provider
data was visible in the normal UI during verification.

## Captured Issues

### ISSUE-OR-001 - Invalid OpenRouter model id shows safe diagnostics

Severity: Minor

Actual result: A model id with a leading `~` produced a safe provider diagnostic
such as model configuration invalid.

Expected result: Invalid model config must fail visibly, without fallback and
without exposing secrets or raw provider payloads.

Status: Resolved by configuration. Use valid OpenRouter model ids without a
leading `~`, for example `google/gemini-2.0-flash-001`.

### ISSUE-OR-002 - Source intelligence was configurable for L1

Severity: Minor

Actual result: The frontend allowed `Source intelligence` to be selected for
L1 even though L1 has no web access and cannot produce source citations.

Expected result: Source intelligence should be available only for L2.

Status: Fixed. Create/edit forms now hide Source intelligence for L1, show it
for L2, clear the value when switching back to L1, and force
`enable_source_intelligence=false` in L1 payloads.

### ISSUE-OR-003 - OpenRouter L2 live source verification remains pending

Severity: Setup-blocked

Actual result: OpenRouter L2 is implemented and covered by mocked tests, but a
dedicated live L2 web-search run with source/citation inspection was not
completed.

Expected result: Run one L2 audit with a configured L2 model and web search
enabled, then inspect Summary/Results/Sources for normalized citations or safe
empty source state.

Status: Deferred to the next live L2 verification pass.

### L199 status

Concrete issues from L198 were stabilized:

- invalid model config behavior remains safe and visible
- OpenRouter provider-mode/factory coverage was restored
- OpenRouter gateway multi-provider identity collapse is guarded
- Source intelligence is hidden/disabled for L1 and payload-safe

No parser, scoring, storage, or native-provider redesign was introduced.
