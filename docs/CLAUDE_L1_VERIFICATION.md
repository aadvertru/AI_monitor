# Claude L1 Verification

This document verifies Anthropic/Claude L1 through the normal UI-driven audit
flow. No real API keys, raw provider responses, prompts, request headers, stack
traces, or secrets should be recorded here.

Allowed statuses: `Not run`, `Pass`, `Fail`, `Blocked`, `Partial`.

## Environment

```text
Date: 2026-05-04
Backend URL: not run in this task
Frontend URL: not run in this task
Database: local development database expected
REAL_PROVIDER_ENABLED: requires manual setup
PROVIDER_MODE: anthropic
ANTHROPIC_API_KEY: required but not inspected or recorded
ANTHROPIC_L1_MODEL: claude-3-5-haiku-latest by default
```

## Result Table

| Scenario | Status | Notes | Issue ID |
|---|---|---|---|
| L188-S01 | Blocked | Requires live backend/frontend with `PROVIDER_MODE=anthropic` and a real Anthropic API key. | ISSUE-L188-001 |
| L188-S02 | Blocked | Requires backend restart with `ANTHROPIC_API_KEY` unset. | ISSUE-L188-001 |
| L188-S03 | Blocked | Requires backend restart with invalid Anthropic model/config. | ISSUE-L188-001 |
| L188-S04 | Blocked | Requires UI/backend live run for Anthropic L2 unsupported behavior. | ISSUE-L188-001 |
| L188-S05 | Blocked | Requires backend restart with `REAL_PROVIDER_ENABLED=0`. | ISSUE-L188-001 |
| L188-S06 | Blocked | Requires backend restart with provider-mode mismatch. | ISSUE-L188-001 |
| L188-S07 | Blocked | Requires a known Anthropic error during live run. | ISSUE-L188-001 |
| L188-S08 | Blocked | Requires live create/edit/save/run flow with typed seed queries. | ISSUE-L188-001 |

## L188-S01 - Claude L1 one-click audit

### Purpose

Verify normal Claude L1 flow from UI.

### Preconditions

- Backend running with `REAL_PROVIDER_ENABLED=1`.
- Backend running with `PROVIDER_MODE=anthropic`.
- `ANTHROPIC_API_KEY` configured in backend environment.
- Frontend running.
- User can log in.

### Steps

1. Log in.
2. Open `/audits/new`.
3. Create an audit with provider `anthropic`.
4. Select SCDL `L1`.
5. Add at least one seed query.
6. Save/create the audit.
7. Click `Start audit`.
8. Wait for terminal status.
9. Open Summary and Results.

### Expected result

- Audit reaches `completed` or `partial`.
- Claude answer is saved.
- Post-processing runs automatically.
- Parsed/scored result appears.
- Summary/results render.
- Sources/citations are empty or show safe empty state.
- No CLI post-processing is needed.
- No unsafe provider data is exposed.

### Actual result

Not run.

### Status

Blocked

### Issue ID

ISSUE-L188-001

## L188-S02 - Missing Anthropic API key

### Purpose

Verify missing key returns safe diagnostics and no fallback.

### Preconditions

- Backend running with `REAL_PROVIDER_ENABLED=1`.
- Backend running with `PROVIDER_MODE=anthropic`.
- `ANTHROPIC_API_KEY` unset.

### Steps

1. Create or open an Anthropic L1 audit.
2. Click `Start audit`.
3. Inspect detail/status/summary/results diagnostics.

### Expected result

- `NO_API_KEY` diagnostic appears.
- No fallback to OpenAI/mock.
- Terminal status follows existing semantics.
- No secrets or raw config are exposed.

### Actual result

Not run.

### Status

Blocked

### Issue ID

ISSUE-L188-001

## L188-S03 - Invalid Anthropic model/config

### Purpose

Verify invalid model/config returns safe diagnostics.

### Preconditions

- Backend running with `PROVIDER_MODE=anthropic`.
- `ANTHROPIC_API_KEY` configured.
- `ANTHROPIC_L1_MODEL` set to an invalid value.

### Steps

1. Create or open an Anthropic L1 audit.
2. Click `Start audit`.
3. Inspect diagnostics.

### Expected result

- `INVALID_MODEL` or `CONFIGURATION_ERROR`.
- No fallback.
- No raw provider response, stack trace, or secrets.

### Actual result

Not run.

### Status

Blocked

### Issue ID

ISSUE-L188-001

## L188-S04 - Claude L2 is unsupported

### Purpose

Verify Anthropic L2 does not silently downgrade to L1.

### Preconditions

- Backend running with `PROVIDER_MODE=anthropic`.
- Anthropic audit can be created with SCDL `L2`, or UI blocks it explicitly.

### Steps

1. Create or open an Anthropic L2 audit.
2. Click `Start audit` if UI allows it.
3. Inspect diagnostics.

### Expected result

- UI blocks Anthropic L2 with clear unsupported message, or backend returns/stores
  `UNSUPPORTED_L2`.
- Anthropic client is not called for L2.
- No fallback to Claude L1, OpenAI, or mock.

### Actual result

Not run.

### Status

Blocked

### Issue ID

ISSUE-L188-001

## L188-S05 - Provider disabled

### Purpose

Verify real provider disabled guardrail.

### Preconditions

- Backend running with `REAL_PROVIDER_ENABLED=0`.
- Backend running with `PROVIDER_MODE=anthropic`.

### Steps

1. Create or open an Anthropic L1 audit.
2. Click `Start audit`.
3. Inspect diagnostics.

### Expected result

- `PROVIDER_DISABLED`.
- No Anthropic call.
- No fallback.
- Safe UI/API error only.

### Actual result

Not run.

### Status

Blocked

### Issue ID

ISSUE-L188-001

## L188-S06 - Provider mode guardrail

### Purpose

Verify provider-mode mismatch blocks Anthropic execution.

### Preconditions

- Backend running with `REAL_PROVIDER_ENABLED=1`.
- Backend running with `PROVIDER_MODE=openai`.
- Anthropic audit exists or can be created.

### Steps

1. Open Anthropic audit.
2. Click `Start audit`.
3. Inspect diagnostics.

### Expected result

- Safe provider-mode diagnostic.
- Anthropic does not run.
- No fallback to OpenAI/mock.

### Actual result

Not run.

### Status

Blocked

### Issue ID

ISSUE-L188-001

## L188-S07 - Provider diagnostics render safely

### Purpose

Verify Anthropic diagnostics render safely in UI.

### Preconditions

- A known Anthropic error can be triggered.
- Frontend and backend running.

### Steps

1. Trigger known Anthropic error.
2. Inspect status/detail/summary/results.

### Expected result

- Diagnostic visible where expected.
- Provider shown as `anthropic`.
- Level shown as L1 if available.
- No raw response, prompt, stack trace, API key, or secret.

### Actual result

Not run.

### Status

Blocked

### Issue ID

ISSUE-L188-001

## L188-S08 - Typed seed queries with Claude L1

### Purpose

Verify typed seed query persistence and execution with Claude L1.

### Preconditions

- Backend running with `PROVIDER_MODE=anthropic`.
- `ANTHROPIC_API_KEY` configured.
- Frontend running.

### Steps

1. Create audit.
2. Generate/edit/delete/add seed query rows.
3. Save audit.
4. Reload audit setup.
5. Run Anthropic L1.
6. Inspect Summary and Results.

### Expected result

- Query text/type/source persist correctly.
- Generated source remains `ai` after edit.
- Manual source is `user`.
- Deleted query is not executed.
- Final saved query list is used by Claude L1 pipeline.

### Actual result

Not run.

### Status

Blocked

### Issue ID

ISSUE-L188-001

## Captured Issues

## ISSUE-L188-001 - Live Anthropic verification requires manual environment setup

### Scenario

L188-S01 through L188-S08

### Severity

Major

### Actual result

Scenarios were not run in this implementation session because they require live
backend/frontend sessions and, for real Claude L1 success, a real Anthropic API
key. No key was inspected or recorded.

### Expected result

Run the scenarios in a controlled local environment and record pass/fail status
without committing secrets or unsafe provider payloads.

### Evidence

Automated L185-L187 tests use mocked clients/providers only and pass. No real
Anthropic API calls were made.

### Suggested next step

Run manual verification after starting the backend with `PROVIDER_MODE=anthropic`
and a real `ANTHROPIC_API_KEY`.

### L189 status

Blocked by environment/setup. No runtime code change is appropriate until live
verification produces a concrete Claude L1 failure. Existing L185-L187 mocked
tests cover config, wrapper, adapter, factory, guardrails, L1 pipeline wiring,
and L2 `UNSUPPORTED_L2` behavior without real Anthropic calls.
