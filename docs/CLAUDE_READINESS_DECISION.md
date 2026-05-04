# Claude Readiness Decision

Decision: Proceed to Claude L1 adapter.

Date: 2026-05-03

## Basis

OpenAI is ready with known limitations as the baseline real provider:

- OpenAI L1 one-click flow works.
- OpenAI L2 one-click flow works.
- Provider errors are normalized.
- Provider diagnostics are visible in API and UI.
- No silent fallback is allowed by contract and guardrail tests.
- Mock/client-stub CI path is stable.
- `docs/PROVIDER_CONTRACT.md` is current.
- `docs/PROVIDER_PARITY.md` exists and defines provider readiness criteria.

## Initial Claude Scope

- Anthropic/Claude L1 only.
- No L2 web search.
- No parser/scoring changes.
- No frontend redesign.
- No raw response exposure.
- No silent fallback to mock, OpenAI, or another provider.
- Mocked tests only in CI.
- Manual one-query Claude L1 verification required before support is claimed.

Claude L2 is unsupported until designed and verified. Claude L2 requests must
return `UNSUPPORTED_L2`.

## Known Constraints

- Do not require OpenAI L2 perfection before starting Claude L1.
- Do not mark Claude as supported until its own parity checklist is satisfied.
- Do not call real Anthropic APIs in automated tests.

