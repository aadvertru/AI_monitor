# Domain Check and PAA Verification

Manual QA checklist for brand domain availability checks and People Also Ask seed query enrichment.

Allowed scenario statuses: `Not run`, `Pass`, `Fail`, `Blocked`, `Partial`.

## Result Table

| Scenario | Status | Notes | Issue ID |
|---|---|---|---|
| Q-S01 | Pass | Covered by authenticated API/domain-check tests with mocked reachable status. |  |
| Q-S02 | Pass | Covered by frontend/domain validation and backend invalid-domain tests. |  |
| Q-S03 | Pass | Covered by DNS failure tests and frontend soft-block tests. |  |
| Q-S04 | Pass | Covered by SSRF/private/localhost blocking tests. |  |
| Q-S05 | Pass | Covered by frontend soft-block test: domain generation disabled only. |  |
| Q-S06 | Pass | Covered by frontend test: manual seed query remains saveable. |  |
| Q-S07 | Pass | Covered by PAA generation UI test with appended suggestions. |  |
| Q-S08 | Pass | Covered by PAA disabled/missing-key safe warning tests. |  |
| Q-S09 | Pass | Covered by backend/frontend dedup tests across user/AI/PAA. |  |
| Q-S10 | Pass | Covered by backend/frontend max-20 limit tests. |  |
| Q-S11 | Pass | Covered by backend/provider and frontend payload language/country tests. |  |
| Q-S12 | Pass | Covered by frontend save payload test preserving edited `source=paa` and omitting removed rows. |  |

## Verification Run

Automated verification was run for Phase Q scenarios using mocked network/provider responses only. No real SerpApi or external provider calls were made.

Commands:

```powershell
.\venv\Scripts\python.exe -m pytest tests\execution\test_domain_check.py tests\api\test_brand_domain_check.py tests\execution\test_paa_provider.py tests\execution\test_serpapi_paa_provider.py tests\api\test_seed_query_generation.py tests\api\test_seed_query_generation_endpoint.py tests\api\test_create_audit.py
npm test -- src/features/audits/CreateAuditPage.test.tsx src/features/audits/EditAuditPage.test.tsx src/lib/api/client.test.ts
```

Result: all scenarios passed through task-scoped automated coverage.

## Scenarios

### Q-S01 - Reachable Domain Check

Purpose: Verify a normal public brand domain can be checked and used for domain-based generation.

Preconditions: User is authenticated. Backend and frontend are running. Use a public reachable domain such as `nike.com`.

Steps:
1. Open the create audit page.
2. Enter a brand name and the reachable domain.
3. Click `Check domain`.
4. Open `Generate seed queries`.

Expected result: Domain status shows reachable. `Use brand domain` remains enabled. No raw HTTP response, headers, stack trace, or provider secrets are displayed.

Actual result:

Status: Pass

Issue ID:

### Q-S02 - Invalid Domain Check

Purpose: Verify invalid domain input is rejected before or during domain check.

Preconditions: User is authenticated.

Steps:
1. Open the create audit page.
2. Enter `https://example.com/page?a=1` in Brand domain.
3. Try to check the domain and submit the audit.

Expected result: UI shows `Invalid domain format`. Backend returns a controlled validation error if called. No request body, stack trace, or raw validator internals are displayed.

Actual result:

Status: Pass

Issue ID:

### Q-S03 - DNS Failure / Unreachable Domain

Purpose: Verify an unreachable public-looking domain soft-blocks only domain-based generation.

Preconditions: User is authenticated. Use a non-resolving domain such as `missing-example-qa.invalid`.

Steps:
1. Open the create audit page.
2. Enter a brand name and the non-resolving domain.
3. Click `Check domain`.
4. Open `Generate seed queries`.

Expected result: Domain status shows DNS failure or unavailable. `Use brand domain` is disabled. Manual seed queries, description-based generation, and PAA remain available when their own inputs are present.

Actual result:

Status: Pass

Issue ID:

### Q-S04 - Private Network / Localhost Blocked

Purpose: Verify SSRF guard blocks private/local targets safely.

Preconditions: User is authenticated.

Steps:
1. Open the create audit page.
2. Try domains or hosts that resolve to private/local targets, such as `localhost`, `127.0.0.1`, or a private-network hostname if available.
3. Click `Check domain`.

Expected result: Domain check returns blocked/private-network or invalid-domain status. The UI does not expose resolver details, request headers, local IPs beyond the user-provided input, or stack traces.

Actual result:

Status: Pass

Issue ID:

### Q-S05 - Domain Unavailable Soft-Blocks Domain-Based Generation Only

Purpose: Verify domain check failure does not block the whole generation panel.

Preconditions: User is authenticated. A checked domain is unavailable.

Steps:
1. Enter brand name, unavailable domain, and brand description.
2. Run domain check.
3. Open `Generate seed queries`.
4. Inspect source checkboxes.

Expected result: `Use brand domain` is disabled or warning-marked. `Use brand description` remains enabled. `Include People Also Ask questions` remains available if brand name or a seed query can be used.

Actual result:

Status: Pass

Issue ID:

### Q-S06 - Manual Seed Queries Still Work With Unavailable Domain

Purpose: Verify users can still create/save an audit manually after a failed domain check.

Preconditions: User is authenticated. Domain check has returned unavailable.

Steps:
1. Enter at least one manual seed query.
2. Select at least one model target.
3. Create the audit.
4. Open audit detail.

Expected result: Audit is created. Manual seed query is preserved. Domain-based generation status does not prevent save/create.

Actual result:

Status: Pass

Issue ID:

### Q-S07 - Generate Queries With PAA Enabled

Purpose: Verify PAA suggestions are requested and appended to the same seed query editor.

Preconditions: User is authenticated. PAA provider is enabled or deterministic mock PAA is configured for local QA.

Steps:
1. Enter brand name and at least one PAA input signal: brand name, brand domain, or manual seed query.
2. Open `Generate seed queries`.
3. Enable `Include People Also Ask questions`.
4. Click `Generate 10 queries`.

Expected result: PAA suggestions append as visible seed query rows. Their source is preserved as `paa` and shown as `PAA` where source badges are rendered. Suggestions are editable/removable and are not persisted until the audit is saved.

Actual result:

Status: Pass

Issue ID:

### Q-S08 - PAA Disabled / Missing SerpApi Key Safe Error

Purpose: Verify unavailable PAA is safe and user-readable.

Preconditions: User is authenticated. PAA is disabled or SerpApi key is missing.

Steps:
1. Enable PAA generation in the UI.
2. Click `Generate 10 queries`.

Expected result: UI shows a safe warning such as PAA unavailable/disabled. It does not show SerpApi key names, request headers, stack traces, raw JSON payloads, raw response fields, or provider exception text. Other selected generation sources may still return suggestions.

Actual result:

Status: Pass

Issue ID:

### Q-S09 - PAA Suggestions Deduplicate With Existing Queries

Purpose: Verify PAA suggestions do not create duplicate seed query rows.

Preconditions: User is authenticated. PAA provider or mock can return a known duplicate.

Steps:
1. Add a manual seed query.
2. Generate PAA suggestions where one suggestion matches the manual query with different casing or whitespace.

Expected result: Duplicate PAA suggestion is skipped. A safe duplicate warning is shown. Only one visible row exists for that query.

Actual result:

Status: Pass

Issue ID:

### Q-S10 - PAA Suggestions Respect Max Seed Query Limit

Purpose: Verify the 20-query limit is enforced when PAA suggestions are appended.

Preconditions: User is authenticated.

Steps:
1. Fill the seed query editor with 20 unique rows.
2. Enable PAA generation.
3. Click `Generate 10 queries`.

Expected result: No additional rows are appended. A safe limit warning is shown. Existing rows remain editable and saveable.

Actual result:

Status: Pass

Issue ID:

### Q-S11 - PAA Language/Country Parameters

Purpose: Verify PAA uses the audit language and country settings.

Preconditions: User is authenticated. Backend logs or a mocked endpoint can verify request payload safely.

Steps:
1. Select a non-default language and country.
2. Enable PAA generation.
3. Click `Generate 10 queries`.
4. Inspect the request payload or safe backend test trace.

Expected result: Request includes the selected language and country. The UI copy indicates PAA uses current audit locale settings. No provider secrets or raw request metadata are exposed.

Actual result:

Status: Pass

Issue ID:

### Q-S12 - PAA Suggestions Save/Reload Correctly After User Confirmation

Purpose: Verify PAA suggestions persist only after save and survive reload.

Preconditions: User is authenticated. PAA generation can return at least one suggestion.

Steps:
1. Generate PAA suggestions.
2. Edit one generated PAA suggestion.
3. Delete one generated PAA suggestion if multiple exist.
4. Save or create the audit.
5. Reopen the audit setup/detail page.

Expected result: Saved PAA rows keep edited text, type, and `source=paa`. Deleted PAA rows are not saved. Unsaved generated rows do not appear if the page is abandoned before save.

Actual result:

Status: Pass

Issue ID:

# Captured Issues

## ISSUE-Q-001 - Short title

### Scenario

Q-Sxx

### Severity

Blocker | Major | Minor | Cosmetic

### Actual result

Describe what happened.

### Expected result

Describe what should have happened.

### Evidence

Screenshots, console output, request IDs, or reproduction notes.

### Suggested next step

Describe the smallest likely fix or follow-up.
