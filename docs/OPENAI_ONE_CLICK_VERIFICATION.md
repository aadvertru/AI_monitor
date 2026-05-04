# OpenAI One-Click Verification

This checklist verifies that the OpenAI audit flow works end-to-end from the UI without CLI post-processing.

One-click means:

```text
login/register
-> create audit
-> fill brand fields
-> generate or manually enter typed seed queries
-> save audit
-> click Start audit
-> backend runs full pipeline
-> UI polls status
-> terminal status appears
-> summary/results/sources are visible
```

No CLI commands should be required after clicking `Start audit`.

Normal UI must not expose raw provider responses, raw prompts, stack traces, request headers, API keys, or secrets.

Allowed statuses for this checklist:

```text
Not run
Pass
Fail
Blocked
Partial
```

## Environment Notes

Record the actual environment before running:

```text
Date: 2026-05-03
Backend URL: http://127.0.0.1:8000
Frontend URL: http://127.0.0.1:5173
Database: local development SQLite database
REAL_PROVIDER_ENABLED: active working OpenAI config observed; exact secret/config not inspected
PROVIDER_MODE: openai path verified through UI
OPENAI_L1_MODEL: not inspected
OPENAI_L2_MODEL: not inspected
REAL_PROVIDER_MAX_PROVIDERS: not inspected
REAL_PROVIDER_MAX_QUERIES: not inspected
REAL_PROVIDER_MAX_RUNS_PER_QUERY: not inspected
REAL_PROVIDER_MAX_TOTAL_RUNS: not inspected
Browser/device: Codex in-app browser, desktop viewport
User: user@example.com
```

Do not write API keys or secrets into this file.

## K176-S01 - Mock L1 One-Click Audit

### Purpose

Verify complete UI-to-pipeline flow without real provider dependency.

### Preconditions

- Backend is running.
- Frontend is running.
- User can log in.
- Mock provider is available.
- No real provider call is required.

### Steps

1. Log in.
2. Open `/audits/new`.
3. Create an audit with provider `mock`.
4. Select SCDL `L1`.
5. Add at least one seed query manually or through generation if mock generation is configured.
6. Save/create the audit.
7. Click `Start audit`.
8. Wait until status reaches a terminal state.
9. Open Summary, Results, and Sources.

### Expected Result

- Audit reaches `completed` or another known valid terminal status.
- No CLI command is needed.
- Summary renders.
- Results render.
- Sources render or show a safe empty state.
- Raw provider response is not exposed in normal UI.

### Failure Notes

- Record final status, visible error text, backend log excerpt, and whether any CLI command was needed.

## K176-S02 - OpenAI L1 One-Click Audit

### Purpose

Verify real OpenAI L1 provider path from UI.

### Preconditions

- Backend is running with real provider mode enabled.
- `REAL_PROVIDER_ENABLED=true`.
- `PROVIDER_MODE=openai`.
- `OPENAI_API_KEY` is configured in the backend environment.
- OpenAI L1 model is configured.
- User can log in.

### Steps

1. Log in.
2. Open `/audits/new`.
3. Create an audit with provider `openai`.
4. Select SCDL `L1`.
5. Add one seed query.
6. Save/create the audit.
7. Click `Start audit`.
8. Wait until status reaches a terminal state.
9. Open Summary, Results, and Sources.

### Expected Result

- OpenAI answer is saved.
- Post-processing runs automatically.
- Parsed/scored result appears.
- Audit reaches `completed` or `partial` according to current status semantics.
- No web citations are expected for L1.
- No raw provider response is exposed to normal UI.
- No CLI post-processing is required.

### Failure Notes

- Record final status, provider diagnostic if shown, backend log excerpt, and whether raw/provider unsafe data appeared.

## K176-S03 - OpenAI L2 One-Click Audit

### Purpose

Verify OpenAI L2 web-enabled path.

### Preconditions

- Backend is running with real provider mode enabled.
- `REAL_PROVIDER_ENABLED=true`.
- `PROVIDER_MODE=openai`.
- `OPENAI_API_KEY` is configured in the backend environment.
- OpenAI L2 model is configured.
- OpenAI L2/web tool path is enabled.
- User can log in.

### Steps

1. Log in.
2. Open `/audits/new`.
3. Create an audit with provider `openai`.
4. Select SCDL `L2`.
5. Add one seed query.
6. Save/create the audit.
7. Click `Start audit`.
8. Wait until status reaches a terminal state.
9. Open Summary, Results, and Sources.

### Expected Result

- Web-enabled provider path is used.
- Audit reaches `completed` or `partial` according to current status semantics.
- Summary and results render.
- Sources/citations render if the provider returns them.
- Safe empty source state appears if no sources are returned.
- No raw provider response is exposed.
- No CLI post-processing is required.

### Failure Notes

- Record final status, whether sources appeared, provider diagnostic if shown, and backend log excerpt.

## K176-S04 - Typed Seed Queries Survive Save/Reload/Run

### Purpose

Verify typed seed query data is preserved and used by the pipeline.

### Preconditions

- Backend and frontend are running.
- User can log in.
- Seed query generation endpoint is available or manual typed rows can be created.

### Steps

1. Log in.
2. Open `/audits/new`.
3. Fill brand fields.
4. Generate seed query suggestions or add typed rows manually.
5. Edit one generated query text.
6. Remove one generated query.
7. Add one manual query.
8. Save/create the audit.
9. Reload the audit detail page.
10. Open edit setup and confirm query rows load.
11. Save setup again.
12. Click `Start audit`.
13. Open Summary and Results after terminal status.

### Expected Result

- Query text persists.
- Query type persists for generated typed queries.
- Generated query source remains `ai` after text edit.
- Manual query persists with source `user`.
- Pipeline uses final visible query list.
- Removed queries are not run.
- Summary/results reflect the final query count.

### Failure Notes

- Record missing/lost fields, run count mismatch, and any query that appears after removal.

## K176-S05 - Legacy `seed_queries` Compatibility

### Purpose

Verify old audits or old API payloads using `seed_queries: list[str]` still work.

### Preconditions

- A legacy audit exists, or one can be created through API/test setup with legacy `seed_queries`.
- Backend and frontend are running.
- User owns the audit.

### Steps

1. Open the legacy audit detail page.
2. Open edit setup.
3. Confirm legacy queries appear in the editor.
4. Save without changing query content.
5. Reload edit setup.
6. Start the audit.
7. Open Summary and Results after terminal status.

### Expected Result

- Legacy queries load.
- Legacy queries are treated as source `user`.
- Missing type does not crash UI.
- Save/reload does not corrupt queries.
- Pipeline runs successfully.

### Failure Notes

- Record any UI crash, query loss, type/source corruption, or pipeline failure.

## K176-S06 - Provider Disabled Error

### Purpose

Verify disabled real provider does not silently fallback to mock and produces safe diagnostics.

### Preconditions

Example backend config:

```text
REAL_PROVIDER_ENABLED=false
PROVIDER_MODE=openai
```

- Backend restarted with this config.
- Frontend is running.
- User can log in.

### Steps

1. Log in.
2. Create or open an OpenAI audit.
3. Click `Start audit`.
4. Observe status/action area and API response if available.

### Expected Result

- Start audit does not silently fallback to mock.
- Audit/run fails or blocks with safe provider diagnostic.
- Error code should be `PROVIDER_DISABLED` once normalized diagnostics are implemented.
- UI shows a safe actionable message.
- No raw stack trace.
- No secrets.

### Failure Notes

- Record if mock fallback happened, whether provider was called, and any unsafe output.

## K176-S07 - Missing OpenAI API Key Error

### Purpose

Verify missing OpenAI key produces safe diagnostics and no silent fallback.

### Preconditions

Example backend config:

```text
REAL_PROVIDER_ENABLED=true
PROVIDER_MODE=openai
OPENAI_API_KEY unset
```

- Backend restarted with this config.
- Frontend is running.
- User can log in.

### Steps

1. Log in.
2. Create or open an OpenAI audit.
3. Click `Start audit`.
4. Observe status/action area and API response if available.

### Expected Result

- Start audit does not silently fallback to mock.
- Safe provider error is shown or captured.
- Error code should be `NO_API_KEY` once normalized diagnostics are implemented.
- No raw env/config dump.
- No secrets.

### Failure Notes

- Record visible UI message, API response, backend log excerpt, and whether secrets appeared.

## K176-S08 - Caps / Guardrails Behavior

### Purpose

Verify real-provider caps are enforced before provider execution.

### Preconditions

Example backend config:

```text
REAL_PROVIDER_ENABLED=true
PROVIDER_MODE=openai
REAL_PROVIDER_MAX_PROVIDERS=1
REAL_PROVIDER_MAX_QUERIES=1
REAL_PROVIDER_MAX_RUNS_PER_QUERY=1
REAL_PROVIDER_MAX_TOTAL_RUNS=1
```

- Backend restarted with strict caps.
- Frontend is running.
- User can log in.

### Steps

1. Log in.
2. Create an OpenAI audit that exceeds one of the caps.
3. Click `Start audit`.
4. Observe whether provider execution begins.

### Expected Result

- Backend enforces cap.
- Provider is not called for excess runs.
- UI shows safe message or audit becomes terminal according to current semantics.
- No silent overrun.

### Failure Notes

- Record which cap was exceeded, whether any run was sent to provider, and visible/API error.

## K176-S09 - Polling and Terminal Refetch

### Purpose

Verify frontend polling/refetch behavior after `Start audit`.

### Preconditions

- Backend and frontend are running.
- User can log in.
- A mock or OpenAI audit can be run to terminal status.

### Steps

1. Open an audit in `created` state.
2. Click `Start audit`.
3. Observe button state while running.
4. Wait for terminal status.
5. Open Summary, Results, and Sources.
6. Refresh the browser page.
7. Return to audit list.

### Expected Result

- Polling starts when audit is running.
- Polling stops on `completed`, `partial`, or `failed`.
- Detail/status is not stale.
- Summary is not stale.
- Results are not stale.
- Sources are not stale.
- Audit list/dashboard reflects updated terminal status.
- Start button state is correct after terminal status.

### Failure Notes

- Record stale screen/route, polling that never stops, or missing refetch.

## K176-S10 - Provider Timeout / Forced Provider Failure

### Purpose

Verify provider failures are safely recorded and surfaced.

### Preconditions

Use the safest available method:

```text
very low OPENAI_REQUEST_TIMEOUT_SECONDS
mock provider forced failure
invalid model if timeout is hard to force
```

- Backend is restarted with the chosen failure config.
- Frontend is running.
- User can log in.

### Steps

1. Create or open an audit using the failure setup.
2. Click `Start audit`.
3. Wait for terminal status or controlled failure.
4. Open Summary and Results.

### Expected Result

- Safe provider error is recorded.
- Audit reaches `failed` or `partial` according to current status semantics.
- UI displays safe error once diagnostics are implemented.
- No raw provider response.
- No stack trace.
- No secrets.

### Failure Notes

- Record failure method, final status, UI/API message, and backend log excerpt.

## K176-S11 - Mobile One-Click Flow Smoke Test

### Purpose

Verify the one-click flow is usable on a mobile device.

### Preconditions

- Phone and development PC are on the same network.
- Frontend is reachable from phone.
- Backend is reachable from phone.
- User can log in from phone.

### Steps

1. Open the frontend on mobile.
2. Log in.
3. Create a mock audit.
4. Add/edit/remove seed query rows.
5. Save/create audit.
6. Click `Start audit`.
7. Open Summary and Results.

### Expected Result

- No hidden hover-only controls are required.
- Start audit is accessible.
- Seed query rows are editable/removable.
- Status and diagnostics are readable.
- Summary/results are readable.

### Failure Notes

- Record viewport/device, blocked control, unreachable endpoint, or unreadable UI.

## K176-S12 - Old Mock Query Expansion Control Is Gone

### Purpose

Verify there is only one seed query generation UX.

### Preconditions

- Frontend is running.
- User can log in.

### Steps

1. Open `/audits/new`.
2. Inspect seed query controls.
3. Open edit setup for a created audit.
4. Inspect seed query controls.

### Expected Result

- Only one seed query generation control is visible.
- No `Query expansion · 15 tokens` mock control remains.
- Generation calls backend endpoint.
- No fake token-cost UI is shown for query generation.

### Failure Notes

- Record any duplicate generation controls or fake token-cost UI.

# Result Table

| Scenario | Status | Notes | Issue ID |
|---|---|---|---|
| K176-S01 | Pass | Mock L1 audit `22` completed from UI; summary/results/sources rendered. |  |
| K176-S02 | Pass | OpenAI L1 audit `23` completed from UI; result row rendered without raw response exposure. |  |
| K176-S03 | Pass | OpenAI L2 audit `24` completed from UI; summary/results/sources rendered safely. |  |
| K176-S04 | Pass | Typed audit `26`: generated/edited/manual query rows persisted and 11 final rows ran. |  |
| K176-S05 | Pass | Legacy payload audit `27`: `seed_queries` loaded as no-type user queries, saved, and completed. |  |
| K176-S06 | Blocked | Requires backend restart with `REAL_PROVIDER_ENABLED=false`; current live backend was kept running. | ISSUE-K177-001 |
| K176-S07 | Blocked | Requires backend restart with `OPENAI_API_KEY` unset; current backend has working OpenAI config and secrets were not inspected. | ISSUE-K177-002 |
| K176-S08 | Blocked | Requires backend restart with stricter `REAL_PROVIDER_*` caps; current live backend config was not changed. | ISSUE-K177-003 |
| K176-S09 | Pass | Terminal detail and dashboard list showed completed status after UI run. |  |
| K176-S10 | Blocked | Requires backend restart with forced timeout/invalid model or special mock failure mode. | ISSUE-K177-004 |
| K176-S11 | Blocked | Real mobile device/network flow cannot be executed from the in-app browser. | ISSUE-K177-005 |
| K176-S12 | Pass | Create/edit expose only `Generate seed queries`; old `Query expansion - 15 tokens` UI absent. |  |

# Captured Issues

## ISSUE-K177-001 - Provider disabled scenario requires backend restart

### Scenario

K176-S06

### Severity

Minor

### Actual Result

Scenario was not run in the browser session because it requires restarting the backend with `REAL_PROVIDER_ENABLED=false`.
The active backend was kept running to complete the normal mock/OpenAI verification flows.

### Expected Result

Run with provider disabled and verify no silent fallback to mock, safe diagnostics, and no secret/stack trace exposure.

### Evidence

Current browser run verified the active OpenAI backend path instead. No disabled-provider backend was started.

### Suggested Next Step

Run in a separate backend session or restart backend with the required env before K178/K179 diagnostics work.

## ISSUE-K177-002 - Missing OpenAI API key scenario requires backend restart

### Scenario

K176-S07

### Severity

Minor

### Actual Result

Scenario was not run because it requires restarting the backend with `OPENAI_API_KEY` unset.
The current backend had a working OpenAI configuration and secrets were not inspected or printed.

### Expected Result

Run with missing OpenAI key and verify safe `NO_API_KEY` diagnostic, no fallback, and no secret/config dump.

### Evidence

OpenAI L1/L2 scenarios passed on the active backend, which implies a working provider configuration.

### Suggested Next Step

Run this scenario in a controlled backend session after K178/K179 normalized diagnostics are implemented.

## ISSUE-K177-003 - Caps/guardrails scenario requires backend restart

### Scenario

K176-S08

### Severity

Minor

### Actual Result

Scenario was not run because it requires restarting the backend with strict `REAL_PROVIDER_*` caps.
The active backend config was not changed during browser verification.

### Expected Result

Run with strict caps and verify provider execution is blocked before excess real-provider calls.

### Evidence

No strict-cap backend session was started.

### Suggested Next Step

Run after K178/K179 so cap failures can be verified through safe provider diagnostics.

## ISSUE-K177-004 - Timeout/forced provider failure scenario requires controlled failure config

### Scenario

K176-S10

### Severity

Minor

### Actual Result

Scenario was not run because it requires a backend restart with forced timeout, invalid model, or a deterministic mock failure mode.

### Expected Result

Run a controlled failure and verify safe provider error recording, terminal status, and no raw provider/stack/secret exposure.

### Evidence

No forced-failure backend session was started.

### Suggested Next Step

Run after K178 normalized error model is implemented, so expected `TIMEOUT` or `INVALID_MODEL` diagnostics can be validated.

## ISSUE-K177-005 - Real mobile one-click flow cannot be executed from in-app browser

### Scenario

K176-S11

### Severity

Minor

### Actual Result

Scenario was not run on a real mobile device. The Codex in-app browser verified desktop UI only.

### Expected Result

Run on an actual phone connected to the same network and verify login, create/edit seed query rows, start audit, and summary/results readability.

### Evidence

No mobile browser/device was available to the automated in-app browser session.

### Suggested Next Step

Run manually on a phone after the local network login issue is resolved.

# K177 Readiness Summary

Status: Ready for stabilization with setup-blocked diagnostics scenarios.

Evidence:

- Mock L1 one-click audit: Pass.
- OpenAI L1 one-click audit: Pass.
- OpenAI L2 one-click audit: Pass.
- Typed seed queries through save/reload/run: Pass.
- Legacy `seed_queries` compatibility: Pass.
- Polling/terminal refetch smoke: Pass.
- Old mock query expansion control removed: Pass.

Blocked scenarios are environment/configuration checks that require controlled backend restarts:

- provider disabled
- missing OpenAI API key
- strict caps
- forced timeout/failure
- real mobile device smoke test

# OpenAI Baseline Readiness

Status: Ready with known limitations.

Evidence:

- OpenAI L1 one-click audit: Pass.
- OpenAI L2 one-click audit: Pass.
- Mock L1 one-click audit: Pass.
- Typed seed queries through save/reload/run: Pass.
- Legacy `seed_queries` compatibility: Pass.
- Polling and terminal refetch smoke: Pass.
- Old mock query expansion control removed: Pass.
- Provider diagnostics are covered after K178-K180.

Known limitations:

- Provider disabled, missing key, strict caps, and forced provider failure scenarios require controlled backend restarts for live manual verification.
- Real mobile one-click smoke remains blocked until local-network mobile login is stable.
- Source/citation rendering depends on provider-returned source data; safe empty state is acceptable.

# Claude Readiness Decision

Decision: Proceed to Claude L1 adapter.

Scope:

- Anthropic/Claude L1 only.
- Claude L2 is unsupported until designed and verified.
- Claude L2 requests must return `UNSUPPORTED_L2`.
- No silent fallback.
- No parser/scoring changes.
- No frontend redesign.
- No raw response exposure.
- Mocked tests only in CI.
- Manual one-query Claude L1 verification required before marking Claude supported.
