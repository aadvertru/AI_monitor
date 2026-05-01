# Real provider pilot notes

Date: 2026-05-01

## Environment

- Mode: local controlled dry-run
- Provider mode: `openai`
- Real provider enabled: `true`
- Provider: OpenAI
- OpenAI API family: Responses API
- L1 model config: `gpt-4.1-mini`
- L2 model config: `gpt-4.1-mini`
- Query count: 1 per pilot audit
- Runs per query: 1
- Secret handling: no real API key was committed or documented

## Commands

The dry-run path used the same local execution function exposed by:

```powershell
.\venv\Scripts\python.exe scripts\run_real_provider_dry_run.py --audit-id <id> --db-url <DATABASE_URL>
```

For this validation pass, temporary SQLite databases under `testtmp/` were used
and a dummy non-secret key was set only to reach the adapter capability check.
The OpenAI SDK is not installed in the current environment, so no real OpenAI
network call was made.

## L1 Pilot

- SCDL level: `L1`
- Provider: `openai`
- Query: non-sensitive test query, `best ai visibility monitoring tools`
- Result: controlled provider error
- Error code: `sdk_not_installed`
- Error message: `openai package is required for OpenAIProviderAdapter.`
- Raw response stored: yes, as an error raw response
- Raw response inspection: available through `GET /audits/{audit_id}/runs/{run_id}/raw`
- Parser/scoring/aggregation observation: no successful raw answer was available, so parser/scoring were not expected to produce parsed scores
- UI observation: frontend should show the audit as inspectable with error rows once pointed at this stored data

## L2 Pilot

- SCDL level: `L2`
- Provider: `openai`
- Query: non-sensitive test query, `best ai visibility monitoring tools`
- Result: controlled provider error
- Error code: `sdk_not_installed`
- Error message: `openai package is required for OpenAIProviderAdapter.`
- Raw response stored: yes, as an error raw response
- Raw response inspection: available through `GET /audits/{audit_id}/runs/{run_id}/raw`
- Parser/scoring/aggregation observation: no successful web-enabled raw answer was available, so source/citation behavior could not be evaluated on real data
- UI observation: frontend should show the audit as inspectable with error rows once pointed at this stored data

## Findings

- Pilot caps were enforced before execution.
- Dry-run used OpenAI only and rejected non-enabled real execution in tests.
- Raw response storage worked for controlled provider errors.
- The current environment cannot complete a successful real OpenAI pilot until the `openai` SDK is installed and a real local `OPENAI_API_KEY` is supplied outside version control.
- No real API keys, secrets, prompts beyond non-sensitive test queries, or raw real provider answers were committed.

## Follow-up

- Install the OpenAI SDK in the backend environment before the next real-data pilot attempt.
- Re-run L1 and L2 with a real local API key stored outside the repository.
- After successful raw answers are stored, repeat parser/scoring/aggregation comparison in `TASK-134`.
