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

Stored successful raw responses can be post-processed into parsed results and
scores with:

```powershell
.\venv\Scripts\python.exe scripts\process_audit_results.py --audit-id <id>
```

The full local backend pipeline can be run end-to-end with:

```powershell
.\venv\Scripts\python.exe scripts\run_audit_pipeline.py --audit-id <id>
```

For controlled API-layer validation, admins can run the same full pipeline with:

```text
POST /dev/audits/{audit_id}/run-pipeline
```

This endpoint is intentionally dev/admin-only. It requires authentication,
rejects non-admin users, applies the existing audit access checks, and returns
only the safe pipeline summary. It is not a public production execution
contract.

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

### 2026-05-01 stored real audit post-processing

- Task: `TASK-137`
- Selected audit id: `8`
- UI-relative audit number: `6`
- Brand: `Окна Лабрадор`
- Domain: `labrador-spb.ru`
- SCDL level: `L1`
- Provider: `openai`
- Query count: `1`
- Runs per query: `1`
- Command:

```powershell
.\venv\Scripts\python.exe scripts\process_audit_results.py --audit-id 8
```

- CLI summary:

```json
{
  "audit_id": 8,
  "audit_status": "completed",
  "errors": [],
  "fatal_error": null,
  "runs_processed": 1,
  "skipped_already_processed": 0,
  "skipped_missing_raw_response": 0,
  "skipped_non_successful_run": 0,
  "total_runs_inspected": 1
}
```

- Parsed result created: yes, for stored run `10`
- Score created: yes, for stored run `10`
- Parser result: brand was not detected in the stored answer
- Saved final score: `0.0`
- Summary refresh: yes
  - total runs: `1`
  - successful runs: `1`
  - visibility ratio: `0.0`
  - average score: `0.0`
  - provider scores: `{"openai": 0.0}`
  - critical query reason: `not_visible`
- Competitors: none extracted
- Sources: none extracted
- Raw answer exposure: normal results/summary response DTOs expose only `raw_answer_ref`, not the raw answer
- UI verification: confirmed by the user after authenticated refresh; summary/results/sources rendered the processed audit as expected and did not expose the full raw answer in normal user-facing views
- Follow-up: Russian-language parser/scoring quality needs analysis in `TASK-139`; the current parser miss is an analysis finding, not a provider execution failure

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

### 2026-05-01 stored real L2 web-search audit

- Task: `TASK-138`
- Selected audit id: `10`
- UI-relative audit number: `8`
- Brand: `Окна Лабрадор`
- Domain: `labrador-spb.ru`
- SCDL level: `L2`
- Provider: `openai`
- Query count: `1`
- Runs per query: `1`
- Source intelligence setting: enabled
- OpenAI model observed in provider metadata: `gpt-4.1-mini`
- Dry-run command:

```powershell
.\venv\Scripts\python.exe scripts\run_real_provider_dry_run.py --audit-id 10
```

- Dry-run summary:

```text
{'audit_id': 10, 'provider_mode': 'openai', 'providers': ['openai'], 'scdl_level': 'L2', 'query_count': 1, 'runs_per_query': 1, 'total_jobs': 1, 'executed_jobs': 1, 'success_count': 1, 'error_count': 0, 'timeout_count': 0, 'rate_limited_count': 0, 'audit_status': 'completed'}
```

- Post-processing command:

```powershell
.\venv\Scripts\python.exe scripts\process_audit_results.py --audit-id 10
```

- Post-processing summary:

```json
{
  "audit_id": 10,
  "audit_status": "completed",
  "errors": [],
  "fatal_error": null,
  "runs_processed": 1,
  "skipped_already_processed": 0,
  "skipped_missing_raw_response": 0,
  "skipped_non_successful_run": 0,
  "total_runs_inspected": 1
}
```

- Raw response stored: yes, raw response id `12`
- Parsed result created: yes, for stored run `12`
- Score created: yes, for stored run `12`
- Provider metadata stored safely:
  - provider: `openai`
  - model: `gpt-4.1-mini`
  - usage: input `309`, output `56`, total `365`
- Citations returned by OpenAI: none (`[]`)
- Source mapping result: no source rows to map; source intelligence UI should render the empty state
- Parser result: brand was not detected in the stored answer
- Saved final score: `0.0`
- Summary refresh: yes
  - total runs: `1`
  - successful runs: `1`
  - visibility ratio: `0.0`
  - average score: `0.0`
  - provider scores: `{"openai": 0.0}`
  - critical query reason: `not_visible`
- L2 web-search evidence:
  - adapter contract test confirms the `L2` request payload includes `tools=[{"type": "web_search"}]`, `tool_choice="auto"`, and `include=["web_search_call.action.sources"]`
  - the selected audit was stored as `scdl_level=L2` and executed through the OpenAI dry-run path
- Request snapshot gap:
  - stored `raw_responses.request_snapshot` currently records only query, provider, and run number
  - it does not store a safe execution-mode/request-shape proof that web search was enabled
  - follow-up task: store redacted execution metadata such as `scdl_level`, `web_search_enabled`, model, and included source mapping keys in the raw response request snapshot or provider metadata
- UI verification: confirmed by the user after authenticated refresh; summary/results/sources rendered correctly, with Sources showing the expected empty state and no full raw answer exposed in normal user-facing views
- Encoding observation: audit `10` was initially created through an ad hoc PowerShell here-string that corrupted Cyrillic to question marks before provider execution. The local stored audit/query fields were repaired afterward for UI inspection, but the raw L2 provider answer reflects the originally corrupted prompt. A safe pilot-audit creation helper is recommended before the next L2 quality run.

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
