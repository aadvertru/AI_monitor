# OpenAI One-Click Verification Results

This file records the stabilization status after `TASK-K178` through
`TASK-K182`. It extends the scenario checklist in
`docs/OPENAI_ONE_CLICK_VERIFICATION.md`.

No API keys, provider secrets, raw prompts, raw provider responses, request
headers, or stack traces are recorded here.

## Environment

```text
Date: 2026-05-03
Backend: local development FastAPI backend
Frontend: local Vite frontend
Database: local development SQLite database
Provider mode: OpenAI path verified manually before K182; automated tests use mocks only
CI rule: no real provider calls
```

## Stabilization Summary

Status: Ready with setup-blocked diagnostics scenarios.

Evidence:

- Mock L1 one-click flow passed during K177 verification.
- OpenAI L1 one-click flow passed during K177 verification.
- OpenAI L2 one-click flow passed during K177 verification.
- Typed seed query save/reload/run flow passed during K177 verification.
- Legacy `seed_queries` compatibility passed during K177 verification.
- Polling and terminal refetch smoke passed during K177 verification.
- Provider error normalization was added in K178.
- API-safe provider diagnostics were added in K179.
- Frontend provider diagnostics were added in K180.
- Provider parity checklist was added in K181.
- K182 added coverage for safe cap/guardrail diagnostics on pipeline responses.

## Scenario Results

| Scenario | Status | K182 status | Notes |
|---|---|---|---|
| K176-S01 Mock L1 one-click audit | Pass | No code change needed | Completed from UI in K177. |
| K176-S02 OpenAI L1 one-click audit | Pass | No code change needed | Completed from UI in K177 without CLI post-processing. |
| K176-S03 OpenAI L2 one-click audit | Pass | No code change needed | Completed from UI in K177; sources render safely when present or empty. |
| K176-S04 Typed seed queries survive save/reload/run | Pass | No code change needed | Typed queries persisted and pipeline consumed final saved query text. |
| K176-S05 Legacy `seed_queries` compatibility | Pass | No code change needed | Legacy queries load/save/run as user-sourced no-type rows. |
| K176-S06 Provider disabled error | Blocked for live rerun | Covered by tests | Requires backend restart with `REAL_PROVIDER_ENABLED=false`; API safe diagnostic coverage exists. |
| K176-S07 Missing OpenAI API key error | Blocked for live rerun | Covered by tests | Requires backend restart with `OPENAI_API_KEY` unset; provider normalization coverage exists. |
| K176-S08 Caps / guardrails behavior | Blocked for live rerun | Covered by tests | Requires backend restart with strict caps; K182 verifies safe pipeline diagnostic for cap failures. |
| K176-S09 Polling and terminal refetch | Pass | Covered by frontend tests | Polling starts/stops and terminal state refetch behavior is covered. |
| K176-S10 Provider timeout / forced provider failure | Blocked for live rerun | Covered by tests | Requires forced timeout/invalid model config; normalized provider/API/UI diagnostics are covered with mocks. |
| K176-S11 Mobile one-click flow smoke test | Blocked | Manual only | Requires a real mobile device/network session. |
| K176-S12 Old mock query expansion control is gone | Pass | No code change needed | Only backend-backed seed query generation UX remains. |

## Captured Issue Status

| Issue | Status | Resolution |
|---|---|---|
| ISSUE-K177-001 Provider disabled scenario requires backend restart | Covered by tests; manual rerun optional | Safe `PROVIDER_DISABLED` diagnostics are exposed through pipeline response tests. |
| ISSUE-K177-002 Missing OpenAI API key scenario requires backend restart | Covered by tests; manual rerun optional | OpenAI missing key maps to safe `NO_API_KEY`; no real calls in automated tests. |
| ISSUE-K177-003 Caps/guardrails scenario requires backend restart | Covered by tests; manual rerun optional | K182 verifies cap failure maps to safe frontend diagnostic without leaking fatal detail. |
| ISSUE-K177-004 Timeout/forced provider failure requires controlled config | Covered by tests; manual rerun optional | Timeout/error diagnostics are normalized and rendered safely in API/UI tests. |
| ISSUE-K177-005 Real mobile one-click flow cannot be executed from in-app browser | Still blocked | Needs manual phone testing after local network login/debug setup is stable. |

## Safety Checks

Task-scoped tests assert or preserve that frontend-safe API/UI output does not
show these unsafe markers:

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

## Verification Commands

```powershell
.\venv\Scripts\python.exe -m pytest tests\api\test_audit_read_run_results.py tests\api\test_audit_schemas.py
cd apps\web
npm test -- src/features/audits/AuditDetailPage.test.tsx src/features/audits/AuditSummaryPage.test.tsx src/features/audits/AuditResultsPage.test.tsx src/test/fixtures.test.ts src/lib/api/client.test.ts
npm run typecheck
npm run build
```

