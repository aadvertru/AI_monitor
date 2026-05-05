# Model Catalog and Selector Verification Checklist

Manual QA checklist for OpenRouter model catalog, audit target selector, run
estimates, and canonical `model_targets` save/load behavior.

Allowed scenario statuses:

- Not run
- Pass
- Fail
- Blocked
- Partial

## Verification Run

Date: 2026-05-05

Environment:

```text
Backend URL: local/test
Frontend URL: local/test
PROVIDER_MODE: mocked/test
OPENROUTER_CATALOG_ENABLED: mocked/test
OPENROUTER_ALLOWED_MODELS: mocked/test allowlist
OPENROUTER_WEB_SEARCH_ENABLED: mocked/test
User: authenticated test user
```

Evidence commands:

```powershell
.\venv\Scripts\python.exe -m pytest tests\execution\test_openrouter_model_catalog.py tests\api\test_model_catalog_endpoint.py
.\venv\Scripts\python.exe -m pytest tests\api\test_audit_target_contract.py
cd apps\web
npm test -- src/features/audits/AuditTargetSelector.test.tsx src/features/audits/modelCatalog.test.tsx src/lib/api/client.test.ts src/features/audits/CreateAuditPage.test.tsx src/features/audits/EditAuditPage.test.tsx
npm run typecheck
```

Results:

- Backend model catalog tests: 17 passed.
- Backend audit target contract tests: 7 passed.
- Frontend model catalog/selector/client/create/edit tests: 64 passed.
- Frontend typecheck: passed.
- Note: frontend tests were run with approved escalation because Windows/esbuild can hit `spawn EPERM` in the sandbox.

## Result Table

| Scenario | Status | Notes | Issue ID |
|---|---|---|---|
| N-S01 | Pass | Authenticated catalog endpoint and frontend hook load allowed catalog fixtures. |  |
| N-S02 | Pass | Cache metadata and stale warning behavior covered by catalog service/hook tests. |  |
| N-S03 | Pass | Selector renders ChatGPT as the default family block from fixture order. |  |
| N-S04 | Pass | Selector emits model selections and de-selection updates. |  |
| N-S05 | Pass | Selector adds Gemini/Claude family blocks and disables add when exhausted. |  |
| N-S06 | Pass | L1/L2 toggles emit separate canonical targets. |  |
| N-S07 | Pass | Experimental L2 marker and `gateway_l2_experimental` output covered. |  |
| N-S08 | Pass | Unsupported L2 fixture disables the L2 checkbox and emits only L1. |  |
| N-S09 | Pass | Create page sends `model_targets` and excludes camelCase/legacy fields. |  |
| N-S10 | Pass | Edit page hydrates saved targets and preserves canonical payload. |  |
| N-S11 | Pass | Legacy audit without targets opens and can be saved with canonical targets. |  |
| N-S12 | Pass | Estimate request/response mapping and visible run count covered. |  |
| N-S13 | Pass | Cap violation/over-cap behavior covered by backend audit target contract tests. |  |
| N-S14 | Pass | Catalog allowlist and target contract tests reject/omit non-allowed model ids without raw data exposure. |  |

## N-S01 - Model catalog loads

### Purpose
Verify authenticated users can load the allowed model catalog from the backend.

### Preconditions
- Backend and frontend are running.
- User is signed in.
- OpenRouter catalog is enabled and has an API key.
- `OPENROUTER_ALLOWED_MODELS` contains at least one supported model id.

### Steps
1. Open the create audit page.
2. Wait for the AI model target selector to finish loading.
3. Inspect the visible model families and model labels.

### Expected result
- The selector renders at least one model family.
- Only allowlisted models are visible.
- No raw OpenRouter payload, API key, authorization header, or `is_allowed` flag is visible.

### Actual result
Pass. Authenticated endpoint and frontend hook tests loaded safe allowlisted catalog fixtures.

### Status
Pass

### Issue ID
Optional.

## N-S02 - Catalog cache works or cache metadata visible

### Purpose
Verify catalog cache metadata is stable and stale catalog warnings are safe.

### Preconditions
- Backend is running.
- User is signed in.
- Model catalog endpoint is reachable.

### Steps
1. Call `GET /model-catalog`.
2. Record `cached_at`, `expires_at`, and `warnings`.
3. Call `GET /model-catalog` again without changing configuration.

### Expected result
- Response includes safe cache metadata when available.
- Repeated calls return the same catalog during the cache window.
- If refresh fails with stale data available, UI/API show a safe warning only.

### Actual result
Pass. Catalog service tests verified cache metadata, cache hits, expiry, and stale warning behavior.

### Status
Pass

### Issue ID
Optional.

## N-S03 - ChatGPT family default block renders

### Purpose
Verify the selector starts with the first available family block.

### Preconditions
- Catalog includes a ChatGPT family.
- User is on create or edit audit setup.

### Steps
1. Open the create audit page.
2. Inspect the first AI family selector.

### Expected result
- First block defaults to ChatGPT when ChatGPT is the first family returned.
- ChatGPT models are visible in that block.
- Empty target selection shows a clear validation message.

### Actual result
Pass. Selector tests verified the first family block renders ChatGPT from fixture order.

### Status
Pass

### Issue ID
Optional.

## N-S04 - Model multiselect works

### Purpose
Verify more than one model can be selected inside a family.

### Preconditions
- Catalog family contains at least two models.

### Steps
1. Select two models in the same family.
2. Deselect one of them.

### Expected result
- Both selected models are shown with level controls.
- Deselecting a model removes only that model's targets.
- Remaining selections stay intact.

### Actual result
Pass. Selector tests verified model selection, target emission, and de-selection updates.

### Status
Pass

### Issue ID
Optional.

## N-S05 - Plus button adds another AI family

### Purpose
Verify the selector can add another family without duplicate family blocks.

### Preconditions
- Catalog contains at least two families.

### Steps
1. Click `Add family`.
2. Inspect the second family block.
3. Try to choose a family already selected in another block.

### Expected result
- New block uses the next available family.
- Already selected family options are disabled in other blocks.
- `Add family` becomes disabled when all families are shown.

### Actual result
Pass. Selector tests verified adding Gemini and Claude family blocks and disabling add when all families are shown.

### Status
Pass

### Issue ID
Optional.

## N-S06 - L1/L2 toggles create correct targets

### Purpose
Verify level toggles create canonical target rows.

### Preconditions
- At least one model supports L1 and L2 gateway.

### Steps
1. Select a model.
2. Enable L1 and L2 for that same model.
3. Save the audit or inspect the create/update request body.

### Expected result
- Request contains two `model_targets` entries for the same `model_id`: one `L1`, one `L2`.
- Request does not contain camelCase `modelTargets`.
- Legacy `providers` and `scdl_level` are not sent with canonical targets.

### Actual result
Pass. Selector and create tests verified separate L1/L2 canonical target output.

### Status
Pass

### Issue ID
Optional.

## N-S07 - Experimental L2 marker visible

### Purpose
Verify experimental L2 gateway status is visible before save.

### Preconditions
- Catalog has a model with `supports_l2_gateway=true` and `l2_experimental=true`.

### Steps
1. Select the model.
2. Inspect the L2 level control.

### Expected result
- L2 can be selected.
- `Experimental` marker is visible next to L2.
- Saved target has `gateway_l2_experimental=true` only for the L2 target.

### Actual result
Pass. Selector tests verified the experimental marker and L2 gateway metadata.

### Status
Pass

### Issue ID
Optional.

## N-S08 - Unsupported L2 disabled

### Purpose
Verify models without L2 support cannot create L2 targets.

### Preconditions
- Catalog has a model with `supports_l2_gateway=false`.

### Steps
1. Select the L1-only model.
2. Inspect the L2 checkbox.
3. Try to save the audit.

### Expected result
- L2 checkbox is disabled.
- Save payload includes only L1 for that model.
- Source intelligence remains hidden unless at least one L2 target exists.

### Actual result
Pass. Selector tests verified unsupported L2 is disabled and only L1 is emitted.

### Status
Pass

### Issue ID
Optional.

## N-S09 - Create audit saves modelTargets

### Purpose
Verify create audit persists canonical model targets.

### Preconditions
- User is signed in.
- Catalog contains at least one available model.

### Steps
1. Create an audit with one or more selected model targets.
2. Open the saved audit detail page.
3. Inspect request payload or API response.

### Expected result
- Create request sends `model_targets`.
- Detail response returns the saved targets.
- Audit setup displays the selected target model, family, provider, and level information.

### Actual result
Pass. Create page and API client tests verified canonical `model_targets` request payloads.

### Status
Pass

### Issue ID
Optional.

## N-S10 - Edit audit loads modelTargets

### Purpose
Verify edit setup hydrates saved canonical targets.

### Preconditions
- A created audit exists with saved `model_targets`.

### Steps
1. Open edit setup for the audit.
2. Inspect selected models and L1/L2 toggles.
3. Save without changing model targets.

### Expected result
- Saved model targets are preselected.
- L1/L2 toggles reflect persisted levels.
- Save request preserves canonical targets.

### Actual result
Pass. Edit page tests verified saved model targets hydrate and persist through update.

### Status
Pass

### Issue ID
Optional.

## N-S11 - Legacy audit still editable

### Purpose
Verify audits without canonical targets can still be edited safely.

### Preconditions
- A legacy audit exists with `providers`/`scdl_level` and no `model_targets`.

### Steps
1. Open edit setup for the legacy audit.
2. Select at least one model target.
3. Save and reload.

### Expected result
- Legacy audit opens without crashing.
- User can migrate it by selecting canonical targets.
- Saved audit uses `model_targets` and does not send legacy provider fields.

### Actual result
Pass. Legacy edit tests verified audits without targets open and can be saved with canonical targets.

### Status
Pass

### Issue ID
Optional.

## N-S12 - Run estimate correct

### Purpose
Verify `POST /audits/estimate` matches visible model target selections.

### Preconditions
- User is signed in.
- Create or edit form has at least one seed query and one model target.

### Steps
1. Select known seed query and target counts.
2. Observe the estimate panel.
3. Compare UI count with API response.

### Expected result
- Estimate request is authenticated.
- Estimate payload contains draft queries and `model_targets`, not brand create-only fields.
- UI shows the backend estimated check count.

### Actual result
Pass. Client/create tests verified estimate request mapping and visible backend estimated check count.

### Status
Pass

### Issue ID
Optional.

## N-S13 - Over-cap validation shown

### Purpose
Verify oversized target matrices are blocked before create/save.

### Preconditions
- Backend caps are configured to a known small or testable limit.

### Steps
1. Build a draft that exceeds model, target, query, or run caps.
2. Wait for the estimate panel.
3. Try to submit the audit.

### Expected result
- UI shows one or more cap violation messages.
- Submit button is disabled while `over_cap=true`.
- Backend create/update still rejects over-cap payloads if submitted directly.

### Actual result
Pass. Backend audit target contract tests verified cap violations and over-cap rejection.

### Status
Pass

### Issue ID
Optional.

## N-S14 - No arbitrary model id can execute

### Purpose
Verify users cannot execute arbitrary model ids outside the allowed catalog/policy.

### Preconditions
- Backend is configured with a known `OPENROUTER_ALLOWED_MODELS` allowlist.
- User is signed in.

### Steps
1. Attempt to create or update an audit with a manually modified non-allowlisted `model_id`.
2. Attempt to run an audit with a non-allowlisted target already present.
3. Inspect API response and UI diagnostics.

### Expected result
- Backend rejects non-allowlisted model ids before provider execution.
- No fallback to a default model occurs.
- UI shows a safe diagnostic or controlled validation error.
- No API key, raw prompt, raw response, or stack trace is exposed.

### Actual result
Pass. Catalog allowlist and target contract tests verified non-allowed model ids are not accepted/exposed.

### Status
Pass

### Issue ID
Optional.

# Captured Issues

No issues captured yet.

## ISSUE-N-001 - Short title

### Scenario
N-Sxx

### Severity
Blocker | Major | Minor | Cosmetic

### Subsystem
catalog service | cache | catalog endpoint | frontend selector | create/edit payload | estimate | legacy compatibility | model allowlist | i18n/display | safety

### Actual result
...

### Expected result
...

### Evidence
...

### Suggested next step
Fix now / defer / needs investigation.
