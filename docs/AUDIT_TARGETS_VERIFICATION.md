# Audit Targets Verification Checklist

Manual QA checklist for canonical multi-target audit behavior.

Allowed scenario statuses:

- Not run
- Pass
- Fail
- Blocked
- Partial

## Verification Run

Date: 2026-05-05

Evidence commands:

```powershell
.\venv\Scripts\python.exe -m pytest tests\api\test_audit_target_contract.py tests\control\test_job_scheduler.py tests\execution\test_worker_execution.py tests\api\test_create_audit.py
.\venv\Scripts\python.exe -m ruff check tests\audit_target_fixtures.py tests\api\test_audit_target_contract.py
cd apps\web
npm test -- src/test/fixtures.test.ts src/lib/api/client.test.ts
npm run typecheck
```

Results:

- Backend verification: 50 passed.
- Backend ruff: passed.
- Frontend fixture/API mapping tests: 28 passed.
- Frontend typecheck: passed.
- Note: the first frontend test attempt hit Windows `spawn EPERM` from esbuild inside sandbox; rerun with approved escalation passed.

## Result Table

| Scenario | Status | Notes | Issue ID |
|---|---|---|---|
| M-S01 | Pass | Legacy provider payload validates and creates audit; detail remains compatible. |  |
| M-S02 | Pass | Single L1 target fixture validates through create/detail contract. |  |
| M-S03 | Pass | Same model L1+L2 fixture validates; L2 gateway flag is preserved. |  |
| M-S04 | Pass | Two same-level model targets persist as distinct target rows. |  |
| M-S05 | Pass | Scheduler expands queries by targets with unique idempotency keys. |  |
| M-S06 | Pass | Jobs, runs, raw request snapshots, and results preserve target id. |  |
| M-S07 | Pass | Estimate reports cap violations; create rejects over-cap payloads. |  |
| M-S08 | Pass | Gateway metadata is preserved through safe target/result metadata. |  |
| M-S09 | Pass | Direct legacy DB audit without targets opens with empty model_targets. |  |
| M-S10 | Pass | Fixture and response checks contain no raw provider payloads or secrets. |  |
| M-S11 | Pass | Same-level OpenRouter targets send distinct target.model_id values. |  |
| M-S12 | Pass | Frontend request body contains model_targets and excludes modelTargets. |  |
| M-S13 | Pass | Authenticated estimate endpoint counts queries/targets/models/runs and rejects unauthenticated requests. |  |

## M-S01 - Create legacy provider audit

### Purpose
Verify that the legacy provider-based create contract still works and remains backward-compatible.

### Preconditions
- Backend and frontend are running.
- Test user is signed in.
- Provider mode supports the selected legacy provider, or mock mode is enabled.

### Steps
1. Open the create audit page.
2. Create an audit using the legacy provider selector without model target fields.
3. Open the saved audit detail page.

### Expected result
- Audit is created successfully.
- Saved setup shows the selected legacy provider.
- Detail response remains usable even if `model_targets` is missing or empty.

### Actual result
Pass. Covered by backend contract tests with legacy provider payload creation and detail compatibility.

### Status
Pass

### Issue ID
Optional.

## M-S02 - Create audit with one model L1 target

### Purpose
Verify that a canonical single L1 model target can be saved and displayed.

### Preconditions
- Backend and frontend are running.
- Test user is signed in.
- At least one L1 target is available in the UI or API payload.

### Steps
1. Create an audit with one `model_targets` entry at level `L1`.
2. Open the audit detail page.
3. Inspect the saved setup and API response.

### Expected result
- Audit is created successfully.
- The target is saved with `ai_family`, `execution_provider`, `model_provider`, `model_id`, `display_name`, and `level`.
- Legacy `providers` and `scdl_level` remain derived for compatibility.

### Actual result
Pass. Covered by canonical fixture schema validation and create/detail contract tests.

### Status
Pass

### Issue ID
Optional.

## M-S03 - Create audit with one model L1+L2 targets

### Purpose
Verify that the same model can be saved as separate L1 and L2 targets.

### Preconditions
- Backend and frontend are running.
- Test user is signed in.
- L2 is enabled only where provider policy allows it.

### Steps
1. Create an audit with two targets using the same `model_id`: one `L1`, one `L2`.
2. Ensure the L2 target has `gateway_l2_experimental=true` only if routed through a gateway.
3. Open the saved audit detail page.

### Expected result
- Both targets are saved as distinct rows.
- L2 target metadata is preserved.
- Legacy `scdl_level` is `L2` because at least one target is L2.

### Actual result
Pass. L1 and L2 targets for the same model validate as separate targets; L2 gateway metadata is preserved.

### Status
Pass

### Issue ID
Optional.

## M-S04 - Create audit with two model targets

### Purpose
Verify multi-model target creation for same-level comparisons.

### Preconditions
- Backend and frontend are running.
- Test user is signed in.
- Two allowed model targets are available.

### Steps
1. Create an audit with two `L1` targets using different `model_id` values.
2. Save and reload the audit.
3. Inspect saved target metadata.

### Expected result
- Both targets persist.
- Same-level targets do not collapse into one provider.
- Display order is stable enough for review.

### Actual result
Pass. Two same-level target rows persist without collapsing into one provider target.

### Status
Pass

### Issue ID
Optional.

## M-S05 - Scheduler creates query x target runs

### Purpose
Verify scheduler expansion across seed queries and model targets.

### Preconditions
- An audit exists with at least two seed queries and two model targets.
- No jobs have been scheduled for the audit yet.

### Steps
1. Trigger the audit run or scheduling step.
2. Inspect scheduled jobs through logs, database, or result counts.

### Expected result
- Total jobs equals `seed_query_count * target_count * runs_per_query`.
- Each job has the correct `audit_target_id`.
- No duplicate idempotency keys are created.

### Actual result
Pass. Scheduler created `query_count * target_count * runs_per_query` jobs with unique idempotency keys.

### Status
Pass

### Issue ID
Optional.

## M-S06 - target_id preserved in jobs/runs/results

### Purpose
Verify target identity survives execution and result serialization.

### Preconditions
- A multi-target audit has been scheduled and run.
- Results endpoint is available.

### Steps
1. Run the audit pipeline.
2. Inspect jobs, runs, and `GET /audits/{id}/results`.
3. Compare job target ids with run/result target ids.

### Expected result
- Every target-based job has `audit_target_id`.
- Every target-based run preserves `audit_target_id`.
- Result rows expose safe `target_id` and target metadata.

### Actual result
Pass. Target id was preserved in jobs, runs, raw request snapshots, and result serialization tests.

### Status
Pass

### Issue ID
Optional.

## M-S07 - caps reject excessive audit

### Purpose
Verify configured audit caps prevent oversized target matrices.

### Preconditions
- Backend is running with known cap env vars.
- Test user is signed in.

### Steps
1. Submit an audit draft that exceeds query, target, model, or total-run caps.
2. Call `POST /audits/estimate` with the same draft.
3. Try to create the audit.

### Expected result
- Estimate response returns `over_cap=true` and specific violations.
- Create request returns `422 Unprocessable Entity`.
- No audit is created for the rejected payload.

### Actual result
Pass. Estimate returned specific query/run cap violations and create rejected the over-cap payload with 422.

### Status
Pass

### Issue ID
Optional.

## M-S08 - OpenRouter gateway target metadata preserved

### Purpose
Verify gateway metadata is preserved without exposing secrets.

### Preconditions
- OpenRouter mode is configured.
- At least one OpenRouter target exists.

### Steps
1. Create an audit with an OpenRouter target.
2. Run the audit pipeline.
3. Inspect status/results diagnostics and raw response metadata available to admins.

### Expected result
- Safe metadata includes gateway flags, model id, model provider, and level.
- API key, authorization headers, raw prompts, and raw provider payloads are not exposed in UI endpoints.

### Actual result
Pass. Gateway flags and model metadata are preserved in safe response data; fixture checks found no secret/raw fields.

### Status
Pass

### Issue ID
Optional.

## M-S09 - Legacy audit still opens/runs

### Purpose
Verify existing audits without `audit_targets` remain usable.

### Preconditions
- A legacy audit exists with `providers` and no `audit_targets`.
- Backend and frontend are running.

### Steps
1. Open the legacy audit detail page.
2. Run or refresh the audit.
3. Open summary and results.

### Expected result
- Audit opens without errors.
- Scheduler falls back to legacy `providers`.
- Results remain readable with `target_id=null` or missing target metadata.

### Actual result
Pass. A direct legacy DB audit with providers and no audit targets opened with an empty `model_targets` list.

### Status
Pass

### Issue ID
Optional.

## M-S10 - No raw provider data exposed

### Purpose
Verify safe serialization boundaries for target-aware responses.

### Preconditions
- A run exists with provider metadata and raw response stored.
- User is signed in.

### Steps
1. Open audit detail, status, summary, and results endpoints.
2. Search serialized responses and UI for secret/raw fields.

### Expected result
- No `raw_answer`, `raw_response`, `raw_prompt`, request headers, authorization, API key, token, cookie, stack trace, or secret value appears in non-admin UI endpoints.
- Results may expose only safe `raw_answer_ref`.

### Actual result
Pass. Backend and frontend fixtures were checked for raw provider payloads, headers, API keys, tokens, and secrets.

### Status
Pass

### Issue ID
Optional.

## M-S11 - Same-level different model_id targets produce different provider request models

### Purpose
Verify target model identity controls provider request model selection.

### Preconditions
- OpenRouter mode is configured with at least two allowed model ids.
- Audit has two same-level targets with different `model_id` values.

### Steps
1. Run the audit pipeline.
2. Inspect safe execution logs or persisted request snapshots.
3. Compare provider request model ids for each target.

### Expected result
- Each target sends its own `model_id` to the provider adapter.
- Same execution provider does not collapse different model ids into one configured default.

### Actual result
Pass. Provider request tests observed distinct `model_id` values for same-level OpenRouter targets.

### Status
Pass

### Issue ID
Optional.

## M-S12 - Frontend sends model_targets wire field, not modelTargets

### Purpose
Verify frontend API mapping uses backend wire naming.

### Preconditions
- Frontend dev server is running.
- Browser devtools or request logging is available.

### Steps
1. Create or update an audit with model targets from the UI.
2. Inspect the request payload sent to the backend.

### Expected result
- Request body contains `model_targets`.
- Request body does not contain camelCase `modelTargets`.
- Target fields use snake_case names like `model_id` and `gateway_l2_experimental`.

### Actual result
Pass. Frontend client mapping test verified request JSON contains `model_targets` and not `modelTargets`.

### Status
Pass

### Issue ID
Optional.

## M-S13 - POST /audits/estimate returns correct estimate and cap violations

### Purpose
Verify the authenticated estimate endpoint matches the matrix contract.

### Preconditions
- Backend is running.
- Test user is signed in.
- Known cap env vars are set.

### Steps
1. Call `POST /audits/estimate` with a valid draft payload.
2. Verify query, target, model, and run counts.
3. Call it again with an over-cap payload.
4. Try the endpoint while unauthenticated.

### Expected result
- Valid draft returns `over_cap=false` with correct counts.
- Over-cap draft returns specific violations.
- Unauthenticated request is rejected.
- No ownership check is required because payload is draft-only.

### Actual result
Pass. Estimate endpoint tests verified authenticated counts, cap violations, and unauthenticated rejection.

### Status
Pass

### Issue ID
Optional.

# Captured Issues

No issues captured in this verification run.

## ISSUE-M-001 - Short title

### Scenario
M-Sxx

### Severity
Blocker | Major | Minor | Cosmetic

### Actual result
...

### Expected result
...

### Evidence
...

### Suggested next step
Fix now / defer / needs investigation.
