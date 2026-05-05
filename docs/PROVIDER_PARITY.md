# Provider Parity Checklist

This checklist defines the minimum support and verification standard for AI
providers in AI Brand Visibility Monitor. It is used to compare provider
capabilities, prevent provider-specific behavior from leaking into parser,
scoring, aggregation, API responses, or frontend code, confirm L1/L2 support,
and decide when a provider is ready to be marked as supported.

OpenRouter is the active next provider integration. It is a gateway provider:
the backend calls OpenRouter while the routed model may belong to Anthropic,
Google, OpenAI, Meta, xAI, or another upstream provider.

Native Anthropic/Claude is deferred/unverified while the project moves to the
OpenRouter gateway path. Claude L1 can be tested through OpenRouter model ids.

## Provider Support Matrix

| Provider | Type | Status | L1 | L2 | Notes |
|---|---|---|---|---|---|
| `mock` | native/test | supported | yes | deterministic simulation | Required for CI and local deterministic tests; never a real visibility source. |
| `openai` | native | baseline | yes | yes | Primary verified strict L2/source-capable path. |
| `openrouter` | gateway | L1 verified / L2 experimental | verified | experimental pending live source verification | One key, many L1 models; L2 is best-effort gateway web search and remains experimental until live source behavior is validated. |
| `anthropic` | native | deferred/unverified | deferred | future | Native branch deferred; use OpenRouter for Claude L1 comparisons. |
| `perplexity` | native | future | future | future | Optional future citation/search provider. |

## Provider Checklist Template

Use this template for every provider before marking it supported.

### Capability

- [ ] Adapter implemented
- [ ] L1 supported
- [ ] L2 supported or explicitly unsupported
- [ ] Unsupported L2 returns `UNSUPPORTED_L2`
- [ ] No silent fallback from L2 to L1
- [ ] No silent fallback from real provider to mock
- [ ] Gateway providers distinguish execution provider, model provider, and model id
- [ ] Configured model is used; no silent model replacement

### Normalized Output

- [ ] Successful response maps to normalized answer text
- [ ] Empty answer maps to `EMPTY_RESPONSE`
- [ ] Raw response is internally storable if needed
- [ ] Raw response is not exposed to normal frontend endpoints
- [ ] Sources/citations normalize to provider source shape
- [ ] Missing sources are handled safely
- [ ] Usage normalizes when available
- [ ] Missing usage does not fail the run

### Normalized Errors

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

### Manual Verification

- [ ] One-query L1 audit verified manually
- [ ] One-query L2 audit verified manually if supported
- [ ] Unsupported L2 verified manually if not supported
- [ ] Provider disabled scenario verified
- [ ] Missing key scenario verified
- [ ] Timeout/failure scenario verified if feasible
- [ ] Summary/results render after execution
- [ ] Sources/citations render or safe empty state appears
- [ ] Provider diagnostics render safely in UI

## Provider: mock

Mock provider is required for deterministic local/test execution. It is not a
real visibility source and must never be silently used as fallback when a real
provider is configured.

| Area | Status | Notes |
|---|---|---|
| Adapter implemented | Done | Deterministic adapter exists for tests/dev. |
| L1 support | Done | Returns deterministic answer data. |
| L2 support | Done | Deterministic simulation only; no real web access. |
| Real calls | Not supported | Mock must never call external APIs. |
| CI allowed | Done | Mock is the only provider class allowed for automated provider tests. |
| Error modes | Done | Supports deterministic timeout, rate-limit, invalid response, and unsupported L2 modes. |
| Secret safety | Done | No provider secrets are required. |

## Provider: openai

OpenAI is the first active real provider. L1 is supported. L2 is supported
through backend-owned OpenAI execution with web/search tooling where configured.
Real OpenAI calls are manual/dev-only and must not run in CI.

| Area | Status | Notes |
|---|---|---|
| Adapter implemented | Done | Adapter exists behind backend provider selection. |
| L1 support | Done | Verified through mocked tests and manual one-query runs. |
| L2 support | Done | Supported through configured OpenAI web/search path. |
| Unsupported L2 handling | Not supported | OpenAI currently supports L2 in this project; this requirement applies to providers without L2. |
| Normalized answer text | Done | Success maps to `raw_answer`/answer text for parser input. |
| Normalized sources | Partial | Sources/citations are normalized when provider returns them; empty source state is safe. |
| Normalized usage | Done | Usage is stored as JSON-safe provider metadata. |
| Normalized errors | Done | Provider errors use the normalized provider error codes. |
| API diagnostics | Done | Status, summary, results, and pipeline responses expose safe diagnostics. |
| UI diagnostics | Done | Detail, summary, and results render safe provider diagnostics. |
| No secret leakage | Done | API/UI diagnostics do not expose keys, headers, prompts, raw responses, or stack traces. |
| Mock tests only in CI | Done | Automated tests use mock/client stubs, not real provider calls. |
| Manual one-click verification | Partial | Core mock/OpenAI L1/L2 one-click scenarios passed; config-restart and mobile scenarios remain manual/setup-blocked. |
| Caps/guardrails | Done | Pilot caps and provider-mode checks guard real-provider execution. |
| Typed seed query execution | Done | Pipeline consumes saved typed seed query text. |

## OpenAI Baseline Readiness

Status: Ready with known limitations.

Evidence:

- OpenAI L1 one-click audit: Pass.
- OpenAI L2 one-click audit: Pass.
- Provider error normalization: Pass.
- API provider diagnostics: Pass.
- UI provider diagnostics: Pass.
- Typed seed queries through pipeline: Pass.
- Caps/guardrails: covered by automated tests and manual restart checklist.
- CI provider behavior: mock/client stubs only, no real provider calls.

Known limitations:

- Real provider disabled, missing key, strict caps, and forced timeout scenarios still require manual backend restarts for live verification.
- Mobile one-click flow remains a manual device/network check.
- Source/citation availability depends on what the provider returns; safe empty source states are expected.

## Claude Readiness Decision

Decision: Defer native Claude in favor of OpenRouter gateway integration.

Rationale:

- OpenAI L1 one-click flow works.
- Provider errors are normalized.
- Provider diagnostics are visible in API and UI.
- Silent fallback is prohibited by contract and guardrail tests.
- Mock CI path is stable.
- Provider contract is current.
- Provider parity checklist exists.

Current native Claude scope:

- Deferred/unverified.
- No native L2 web search in the active path.
- No silent fallback to mock or another real provider.
- No parser/scoring changes.
- No frontend redesign.
- No raw response exposure.
- Mocked tests only in CI.
- Future manual one-query native Claude verification required before support claim.

Claude via OpenRouter is gateway execution, not native Anthropic execution.

## Provider: openrouter

OpenRouter is the active gateway provider integration.

OpenRouter L1 means an AI answer without web access through OpenRouter. It must
not use web search, plugins, `:online`, browsing tools, or external source
enrichment.

OpenRouter L2 is experimental gateway web search. It is not equivalent to
native OpenAI L2 or a future native Anthropic/Perplexity/Gemini L2 path.
Sources/citations are best-effort.

Gateway metadata must track:

```text
execution_provider=openrouter
model_provider=<prefix before slash>
model_id=<openrouter model id>
gateway=true
gateway_l2_experimental=true|false
```

No fallback is allowed from OpenRouter L1/L2 to native OpenAI, native Anthropic,
mock, or a different OpenRouter level/model.

| Area | Status | Notes |
|---|---|---|
| Adapter implemented | Done | Mocked backend coverage exists. |
| L1 support | Done | Primary gateway model-comparison path; no web search/tools. Live L1 gateway runs were verified locally with routed Gemini/Claude-style model ids. |
| L2 support | Experimental pending live source verification | Best-effort OpenRouter web-search server tool behavior. Implemented and tested with mocked client responses, but not yet source-verified with a live L2 response. |
| Gateway model allowlist | Done | Required before execution. |
| Normalized answer text | Done | Implemented for L1/L2 mocked responses. |
| Normalized sources | Done | L1 empty; L2 best-effort annotations/citations/sources. |
| Normalized errors | Done | Matches `docs/PROVIDER_CONTRACT.md`. |
| Gateway metadata | Done | Distinguishes execution/model providers and model id. |
| API diagnostics | Done | Safe provider diagnostics are exposed through existing provider diagnostic DTOs. |
| UI diagnostics | Done | Invalid model/config diagnostics render safely in the existing UI. |
| CI behavior | Done | Mocked client calls only. |
| Manual L1 verification | Done | Local one-query gateway runs passed after valid OpenRouter model configuration. |
| Manual L2 verification | Pending | Required before L2 can be called ready; sources/citations must be inspected or safe empty source state confirmed. |

Planned config placeholders:

```text
OPENROUTER_API_KEY
OPENROUTER_L1_MODEL
OPENROUTER_L2_MODEL
OPENROUTER_ALLOWED_MODELS
OPENROUTER_REQUEST_TIMEOUT_SECONDS
OPENROUTER_MAX_OUTPUT_TOKENS
OPENROUTER_WEB_SEARCH_ENABLED
OPENROUTER_WEB_SEARCH_TOOL
OPENROUTER_SITE_URL
OPENROUTER_APP_NAME
```

## Provider: anthropic

Native Anthropic/Claude is deferred/unverified while OpenRouter gateway
integration is active. Claude L1 comparisons should use OpenRouter model ids
until native Anthropic is reactivated for provider-specific behavior.

Native Anthropic L2 is future work. Until L2 is explicitly designed,
implemented, and verified, native Anthropic L2 requests must return
`UNSUPPORTED_L2` and must not fallback to Claude L1, OpenRouter, OpenAI, or
mock.

Current pilot policy allows one real provider mode per run. Mixed real-provider
audits are out of scope until multi-provider orchestration is explicitly
designed; this is not a permanent architecture limitation.

Frontend must never call Anthropic APIs directly. Parser/scoring must consume
normalized provider output and must not branch on Anthropic raw response shapes.

| Area | Status | Notes |
|---|---|---|
| Adapter implemented | Deferred/unverified | Native branch is not the active integration path. |
| L1 support | Deferred/unverified | Use OpenRouter for Claude L1 comparisons for now. |
| L2 support | Not supported | Future L2 phase only. |
| Unsupported L2 normalized | Deferred/unverified | Must return `UNSUPPORTED_L2` if native branch is wired. |
| No fallback to OpenRouter/OpenAI/mock | Required | Required for all native Anthropic failures. |
| Normalized answer text | Deferred/unverified | Required before support claim. |
| Normalized errors | Deferred/unverified | Must match `docs/PROVIDER_CONTRACT.md`. |
| API diagnostics | Deferred/unverified | Should reuse existing diagnostics if reactivated. |
| UI diagnostics | Deferred/unverified | Should reuse existing diagnostics if reactivated. |
| CI behavior | Required | Must use mocked client/provider calls only. |
| Manual L1 verification | Not verified | Required before support claim. |
| Manual L2 verification | Not verified | Future L2 phase only. |

Planned L1 config placeholders:

```text
ANTHROPIC_API_KEY
ANTHROPIC_L1_MODEL
ANTHROPIC_REQUEST_TIMEOUT_SECONDS
ANTHROPIC_MAX_OUTPUT_TOKENS
```

Future L2 config placeholders:

```text
ANTHROPIC_L2_MODEL
ANTHROPIC_WEB_SEARCH_TOOL_VERSION
ANTHROPIC_WEB_SEARCH_MAX_USES
```

## OpenRouter Readiness Decision

Decision: OpenRouter L1 is ready for controlled pilot use. OpenRouter L2 remains
experimental and pending live source/citation verification.

Evidence:

- OpenRouter adapter/config/client/model-policy tests pass with mocked clients.
- Factory/pilot guardrails prevent silent fallback and provider-mode drift.
- Gateway metadata distinguishes execution provider, model provider, and model id.
- Live L1 gateway runs were verified locally with routed Gemini/Claude-style model ids.
- Invalid model/config failures render safe diagnostics in the UI.
- Source intelligence is hidden/disabled for L1 in create/edit flows and forced off
  in L1 payloads.

Known limitations:

- OpenRouter L2 web-search/source behavior has not yet been validated with a live
  L2 response.
- Gateway-routed providers are not native provider integrations; provider-specific
  source semantics, cost accounting, and strict citation behavior still require
  native adapters or separate provider-specific phases.
- Current pilot allows one gateway-routed UI provider per audit to avoid multiple
  provider labels executing through the same configured model.

## Provider Readiness Definition

A provider may be marked as supported only when all of these are true:

- adapter is implemented
- supported SCDL levels are explicit
- unsupported levels return normalized errors
- output normalization is implemented
- error normalization is implemented
- no silent fallback exists
- safety/no-secret-leakage tests pass
- CI uses mock tests only and never calls real providers
- manual one-query verification passes for each supported SCDL level
- provider diagnostics are visible in API/UI when failures occur
