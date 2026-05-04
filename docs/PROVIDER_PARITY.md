# Provider Parity Checklist

This checklist defines the minimum support and verification standard for AI
providers in AI Brand Visibility Monitor. It is used to compare provider
capabilities, prevent provider-specific behavior from leaking into parser,
scoring, aggregation, API responses, or frontend code, confirm L1/L2 support,
and decide when a provider is ready to be marked as supported.

Anthropic/Claude is future work. Do not implement it as part of this document.

## Provider Support Matrix

| Provider | Status | L1 | L2 | Notes |
|---|---|---|---|---|
| `mock` | supported for tests/dev | yes | deterministic simulation | Required for CI and local deterministic tests; never a real visibility source. |
| `openai` | active real provider | yes | yes | First real provider. Uses backend-owned OpenAI execution and normalized outputs. |
| `anthropic` | planned | planned | not assumed | Future work. Initial target is L1 only until explicitly implemented and verified. |

## Provider Checklist Template

Use this template for every provider before marking it supported.

### Capability

- [ ] Adapter implemented
- [ ] L1 supported
- [ ] L2 supported or explicitly unsupported
- [ ] Unsupported L2 returns `UNSUPPORTED_L2`
- [ ] No silent fallback from L2 to L1
- [ ] No silent fallback from real provider to mock
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

Decision: Proceed to Claude L1 adapter.

Rationale:

- OpenAI L1 one-click flow works.
- Provider errors are normalized.
- Provider diagnostics are visible in API and UI.
- Silent fallback is prohibited by contract and guardrail tests.
- Mock CI path is stable.
- Provider contract is current.
- Provider parity checklist exists.

Initial Claude scope:

- Anthropic/Claude L1 only.
- No L2 web search.
- No silent fallback to mock or another real provider.
- No parser/scoring changes.
- No frontend redesign.
- No raw response exposure.
- Mocked tests only in CI.
- Manual one-query Claude L1 verification required.

Claude L2 is unsupported until designed and verified. Claude L2 requests must
return `UNSUPPORTED_L2`.

## Provider: anthropic

Anthropic/Claude is future work. Initial target is L1 only. L2 is not assumed.
Until L2 is explicitly implemented and verified, unsupported L2 must return
`UNSUPPORTED_L2`. Do not add Anthropic/Claude runtime code as part of parity
documentation work.

| Area | Status | Notes |
|---|---|---|
| Adapter implemented | Planned | Future task. |
| L1 support | Planned | Initial target only. |
| L2 support | Not verified | Must not be assumed. |
| Unsupported L2 handling | Planned | Required before exposing L2 choice for Anthropic. |
| Normalized output/errors | Planned | Must match `docs/PROVIDER_CONTRACT.md`. |
| CI behavior | Planned | Must use mocked client/provider calls only. |
| Manual verification | Planned | Required before support claim. |

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
