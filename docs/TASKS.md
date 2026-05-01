# Phase F2 — Real Response Post-Processing and Analysis Tasks

This file contains tasks for closing the post-processing gap after the first real OpenAI provider execution.

Current state:
- OpenAI real provider execution can save `RawResponse`.
- Parser/scoring/aggregation are not yet automatically applied to stored real raw responses.
- The next goal is to process stored responses, verify UI, test L2 source mapping, and analyze Russian-language parser/scoring quality.

Implementation note:
- TASK-135 must start by inspecting existing parser/scoring function signatures.
- The post-processing service should adapt storage records into the existing DTO/input shape expected by parser/scoring.
- Do not change parser/scoring contracts during this phase unless a task explicitly escalates and is approved.

---

## TASK-135 — Add audit result post-processing service

### Status
Ready

### Goal
Add a backend service that processes stored successful raw audit responses into parsed results, scores, and refreshed audit aggregation.

### Why
Real OpenAI provider execution currently stores `RawResponse`, but the audit remains incomplete until existing parser, scoring, and aggregation logic are applied to those stored responses.

### Context
The real OpenAI pilot can now execute provider calls and save raw answers. This task closes the `raw → parsed → scored → aggregated` gap without calling OpenAI again. The service must be reusable by CLI, admin/debug tools, and future background execution paths.

Expected flow:

```text
successful runs without ParsedResult
→ load stored RawResponse
→ run existing parser
→ run existing scoring
→ save ParsedResult
→ save Score
→ refresh aggregation/summary/status
```

### Scope
- Add a reusable backend service/function for post-processing one audit by `audit_id`.
- Find successful runs for the audit that have stored raw responses but do not yet have parsed results and/or scores.
- Load `raw_responses.raw_answer` and related provider response data from storage.
- Run the existing parser on stored raw response data.
- Run the existing scoring logic on the parsed result.
- Persist `ParsedResult` records using existing storage patterns.
- Persist `Score` records using existing storage patterns.
- Ensure existing summary/results endpoints reflect newly saved `ParsedResult` and `Score` records.
- Update audit status using explicit post-processing rules:
  - `completed` only when all expected runs are terminal and successful/error accounting is complete.
  - `partial` when terminal provider/parser/scoring errors exist or some expected runs cannot be processed.
  - do not mark the audit as `failed` only because the provider run succeeded but the parser did not find the brand.
- Reconstruct or adapt the stored raw response into the existing parser input contract without changing parser signatures, for example:
  - stored `raw_answer`
  - stored citations/sources where available
  - provider metadata where available
  - brand/audit/query context required by the parser
- Keep the transformation boundary explicit:
  - storage data → existing parser/scoring DTO/input shape → parser → scoring → storage
- Make the service idempotent:
  - already processed runs must not create duplicate parsed results or duplicate scores
  - re-running the service should be safe
- Return a structured processing summary, including:
  - audit id
  - total runs inspected
  - runs processed
  - runs skipped because already processed
  - runs skipped because raw response is missing
  - runs skipped because run status is not successful
  - per-run processing errors, reported without failing the whole service where possible
  - fatal service errors, such as missing audit or database failure
- Add tests for service behavior.

### Out of scope
- Do not add the CLI command in this task.
- Do not call the real OpenAI API.
- Do not re-run provider execution.
- Do not change parser logic.
- Do not change scoring formulas.
- Do not change provider adapter behavior.
- Do not change raw response storage contract.
- Do not add frontend UI.
- Do not expose raw answers in normal user-facing UI.
- Do not implement background workers or scheduling.
- Do not process all audits globally unless explicitly needed for tests; this task is audit-id scoped.

### Acceptance criteria
- A stored successful raw response can be parsed, scored, and saved.
- A run without raw response is skipped safely and reported.
- A non-successful run is skipped safely and reported.
- A run that already has parsed/scored output is skipped or updated according to the existing storage convention without duplication.
- Re-running the service for the same audit is safe and does not create duplicate records.
- Existing summary/results endpoints reflect newly saved parsed/scored data after processing.
- Audit status follows the explicit post-processing rules from this task.
- Parser input is built by adapting stored response data into the existing parser contract without changing parser signatures.
- The service returns a structured processing summary with separate per-run errors and fatal service errors.
- Existing mock-provider pipeline behavior remains unchanged.
- Existing parser/scoring tests still pass.
- No real external provider API calls happen in automated tests.

### Test requirements
- Add service-level test for processing one successful stored raw response.
- Add test confirming `ParsedResult` is saved.
- Add test confirming `Score` is saved.
- Add test confirming existing summary/results endpoint data reflects newly saved parsed/scored records.
- Add test confirming audit status behavior for completed processing.
- Add test confirming audit status behavior for partial processing with terminal errors or skipped runs.
- Add test confirming parser miss / brand-not-found does not automatically mark audit as failed.
- Add test confirming stored raw response data is adapted into the existing parser input contract.
- Add test for missing raw response skip behavior.
- Add test for non-successful run skip behavior.
- Add idempotency test confirming re-running does not duplicate parsed results or scores.
- Add test confirming parser/scoring are run from stored raw response data, not from a provider call.
- Add assertion or mock guard confirming no real OpenAI API call is made.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/api/...post_processing...`
- `apps/api/...services...`
- `apps/api/...aggregation...`
- `apps/api/...repositories...`
- `libs/...parser...`
- `libs/...scoring...`
- `tests/...post_processing...`
- `tests/...aggregation...`

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run:
- backend post-processing service tests
- backend parser/scoring tests
- backend aggregation tests affected by this service
- backend audit API tests if audit status/summary behavior is affected
- backend lint/typecheck commands if available

### Dependencies
- TASK-130 — Implement OpenAI real provider adapter for L1 and L2
- TASK-131 — Add real-provider dry-run mode
- TASK-132 — Add raw response inspection screen/log

### Escalate if
- Existing storage model cannot link `Run`, `RawResponse`, `ParsedResult`, and `Score` unambiguously.
- Existing parser requires provider-specific input that cannot be reconstructed from stored raw response data.
- Existing scoring requires fields not produced by the parser.
- Existing summary/results endpoints cannot reflect newly saved parsed/scored data without changing their contracts.
- Parser/scoring signatures require a DTO/input shape that cannot be reconstructed from storage without contract changes.
- Idempotent processing cannot be implemented without a schema or uniqueness decision.
- Audit status rules are unclear after post-processing.
- Implementing this task requires changing parser, scoring, provider, raw response, or aggregation contracts.

### Done means
Inherits project defaults from `/AGENTS.md`.

Additional completion requirements:
- PR summary explains how the service is idempotent.
- PR summary confirms no real provider calls are made.
- PR summary includes the processing summary shape returned by the service.

---

## TASK-136 — Add CLI command to process stored audit results

### Status
Ready

### Goal
Add a local CLI command that runs the audit result post-processing service for a specific stored audit.

### Why
After real OpenAI provider execution saves raw responses, developers need a safe manual command to process stored raw results into parsed results, scores, and refreshed summary before inspecting the UI.

### Context
TASK-135 added a reusable post-processing service for one `audit_id`. This task must add only a thin CLI wrapper around that service. Business logic must remain in the service, not in the script.

Expected local usage example:

```powershell
.\venv\Scripts\python.exe scripts\process_audit_results.py --audit-id 8
```

### Scope
- Add a CLI script or project-equivalent command for processing one audit by id.
- Accept required `--audit-id` argument.
- Initialize backend config/database session using the existing project pattern.
- Call the post-processing service from TASK-135.
- Print a safe structured summary to stdout, including:
  - audit id
  - total runs inspected
  - runs processed
  - already processed skips
  - missing raw response skips
  - non-successful run skips
  - errors, if any
- Return successful process exit code when processing completes without fatal error.
- Return non-zero process exit code for invalid arguments, missing audit, or fatal processing failure.
- Ensure the CLI does not print raw answers, API keys, provider secrets, auth cookies, or sensitive config.
- Add tests for CLI behavior with mocked service/database where practical.
- Document the command in pilot notes or the relevant developer docs.

### Out of scope
- Do not implement post-processing logic inside the CLI.
- Do not call the real OpenAI API.
- Do not trigger provider execution.
- Do not process all audits globally.
- Do not add frontend UI.
- Do not expose raw provider answers.
- Do not change parser logic.
- Do not change scoring formulas.
- Do not change aggregation logic.
- Do not change storage contracts.
- Do not add background workers or scheduler integration.

### Acceptance criteria
- CLI can be run with `--audit-id`.
- CLI can be executed from the repository root on Windows PowerShell, for example:
  - `.\venv\Scripts\python.exe scripts\process_audit_results.py --audit-id 8`
- CLI calls the post-processing service from TASK-135.
- CLI prints safe processing summary.
- CLI exits non-zero for missing or invalid `--audit-id`.
- CLI exits non-zero for missing audit or fatal service error.
- CLI output does not include raw answers or secrets.
- CLI command is documented.
- Existing backend tests still pass.
- No real external provider API calls happen in automated tests.

### Test requirements
- Add test for CLI argument parsing with valid `--audit-id`.
- Add test or smoke check confirming the script import path works when executed from the repository root.
- Add test confirming CLI calls the post-processing service.
- Add test for missing `--audit-id`.
- Add test for invalid `--audit-id`.
- Add test for service success summary output.
- Add test for service fatal error producing non-zero exit code.
- Add test or assertion confirming CLI output does not include raw answers or secrets.
- Add assertion or mock guard confirming no real OpenAI API call is made.

### Files likely affected
Optional hint, not a hard boundary.
- `scripts/process_audit_results.py`
- `apps/api/...post_processing...`
- `apps/api/...database...`
- `tests/...cli...`
- `tests/...post_processing...`
- `docs/...`
- `docs/REAL_PROVIDER_PILOT_NOTES.md`

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run:
- backend CLI tests
- backend post-processing service tests
- backend parser/scoring tests if touched
- backend lint/typecheck commands if available

### Dependencies
- TASK-135 — Add audit result post-processing service

### Escalate if
- The project has no clear way to initialize config/database sessions from scripts.
- The CLI cannot be executed from the repository root without import path hacks.
- CLI execution would require duplicating service logic.
- The post-processing service cannot distinguish fatal errors from per-run processing errors.
- Missing audit behavior is unclear.
- Running the CLI would require real OpenAI API calls.
- Safe output cannot be guaranteed without exposing raw response content.

### Done means
Inherits project defaults from `/AGENTS.md`.

Additional completion requirements:
- Document the exact command for Windows PowerShell local usage.
- PR summary confirms the CLI is a thin wrapper around the service.
- PR summary confirms no raw answers or secrets are printed.

---

## TASK-137 — Process current real audit and verify UI

### Status
Ready

### Goal
Process the current stored real OpenAI audit and manually verify that parsed results, scores, summary, and UI views update correctly.

### Why
The real OpenAI pilot has already produced stored raw responses, but the product value is only visible after post-processing converts raw responses into parsed results, scores, aggregation, and frontend display.

### Context
TASK-135 added the post-processing service. TASK-136 added the CLI command for processing one stored audit by `audit_id`.

The immediate target is the current real audit created during testing, for example audit `#8`, unless another audit id is specified at execution time. If audit `#8` is unavailable, use the latest OpenAI-only audit with a successful stored `RawResponse`.

Expected manual flow:

```text
dry-run provider already saved RawResponse
→ run process_audit_results CLI
→ refresh UI
→ inspect results page
→ inspect summary page
→ verify raw answer is not exposed in normal UI
```

### Scope
- Select the current real OpenAI audit to process.
- If the default example audit id is unavailable, select the latest OpenAI-only audit with a successful stored `RawResponse`.
- Run the CLI from TASK-136 for that audit.
- Confirm the CLI reports processed/skipped/error counts clearly.
- Confirm successful raw responses produce `ParsedResult` records.
- Confirm successful parsed results produce `Score` records.
- Confirm audit summary/aggregation is refreshed.
- Refresh frontend UI and manually verify:
  - audit detail/status page
  - results page
  - summary page
  - competitors section, if parser extracts competitors
  - sources section, if sources are available
- Confirm summary is no longer only default zero values when successful parsed/scored data exists.
- Confirm raw answer is not exposed in normal user-facing UI.
- Record observations and issues in `docs/REAL_PROVIDER_PILOT_NOTES.md` or a project-equivalent notes document.
- Record any discovered bugs as follow-up bug/task entries.

### Out of scope
- Do not implement new parser logic in this task.
- Do not change scoring formulas in this task.
- Do not change aggregation definitions in this task.
- Do not change OpenAI adapter behavior unless a tiny blocking pilot fix is explicitly required and documented.
- Do not run large real-provider audits.
- Do not increase pilot caps.
- Do not expose raw answers in normal user-facing UI.
- Do not add new UI features beyond minimal fixes required to verify the current pilot audit.
- Do not commit API keys, secrets, raw sensitive data, or local `.env` files.

### Acceptance criteria
- Current selected real audit is processed through the CLI.
- Selected audit id is documented in pilot notes.
- CLI output is captured or summarized in pilot notes.
- At least one successful stored raw response is converted into parsed result data if available.
- At least one parsed result is converted into score data if available.
- Audit summary/aggregation is refreshed after processing.
- Results page displays processed row data or a controlled empty/error state.
- Summary page displays refreshed metrics or a controlled empty/error state.
- Competitors and sources are either displayed when available or explicitly documented as absent.
- Raw answer is not visible in normal user-facing UI.
- Follow-up bugs/tasks are recorded for any observed issues.
- No secrets or API keys are committed.

### Test requirements
- No automated test is required to call the real OpenAI API.
- Run the post-processing CLI manually for the selected audit.
- Manually verify CLI output.
- Manually verify parsed result persistence.
- Manually verify score persistence.
- Manually verify summary refresh.
- Manually verify frontend results display.
- Manually verify frontend summary display.
- Manually verify raw answer is not exposed in normal UI.
- If any code changes are made, run the relevant backend/frontend tests affected by those changes.

### Files likely affected
Optional hint, not a hard boundary.
- `docs/REAL_PROVIDER_PILOT_NOTES.md`
- local `.env` file, not committed
- small backend/frontend fix files only if required to complete verification

### Commands
Use project commands from `/AGENTS.md`.

Expected local command example:

```powershell
.\venv\Scripts\python.exe scripts\process_audit_results.py --audit-id 8
```

If audit id differs, replace `8` with the selected stored real audit id.

If code changes are made, run:
- relevant backend post-processing tests
- relevant backend parser/scoring/aggregation tests
- relevant frontend tests/build if UI was touched

### Dependencies
- TASK-135 — Add audit result post-processing service
- TASK-136 — Add CLI command to process stored audit results

### Escalate if
- The selected audit has no stored successful raw responses.
- CLI cannot connect to the expected local database.
- Post-processing creates duplicate parsed results or duplicate scores.
- Parser/scoring cannot process stored raw responses without contract changes.
- Summary cannot be refreshed without changing aggregation contracts.
- Frontend display requires raw answer exposure to work.
- Any secret or API key appears in logs, UI, notes, or committed files.
- Completing verification requires changing parser, scoring, aggregation, provider, raw response, or audit state contracts.

### Done means
Inherits project defaults from `/AGENTS.md`.

Additional completion requirements:
- `docs/REAL_PROVIDER_PILOT_NOTES.md` includes:
  - audit id processed
  - CLI command used
  - processing summary
  - whether parsed results were created
  - whether scores were created
  - whether summary refreshed
  - UI verification result
  - follow-up bugs/tasks
- PR summary confirms no secrets or API keys were committed.

---

## TASK-138 — Test OpenAI L2 web-search response and source mapping

### Status
Ready

### Goal
Run and verify a controlled OpenAI `L2` web-search audit path, including source/citation mapping from raw provider response to backend storage, aggregation, and UI display.

### Why
`L2` is the SCDL mode where web search is enabled, so it must be validated separately from `L1` to confirm that web-search payloads, returned sources/citations, parser behavior, and source intelligence UI work on real OpenAI responses.

### Context
TASK-130 implemented the OpenAI adapter with `L1` and `L2` support. TASK-131 added dry-run mode. TASK-132 added raw response inspection. TASK-135 and TASK-136 added post-processing service and CLI. TASK-137 processed the current real audit and verified basic UI behavior.

This task focuses specifically on the OpenAI `L2` path.

Expected L2 flow:

```text
create or select L2 audit
→ execute OpenAI with web search enabled
→ store RawResponse
→ inspect raw response
→ process stored results
→ verify sources/citations in backend and UI
```

### Scope
- Create or select a small OpenAI-only audit with `scdl_level=L2`.
- Use safe pilot limits:
  - OpenAI only
  - max 3–5 queries
  - max 1 run per query unless explicitly approved
- Confirm the OpenAI request path enables web search for `L2`.
- Verify L2 evidence using stored request snapshot, provider metadata, adapter test evidence, or another documented proof path.
- If current stored request snapshot only includes query/provider/run number and cannot prove web-search enablement, document this gap and create a follow-up task to store safe execution-mode/request-shape metadata.
- Confirm `L1` no-web behavior is not accidentally used for the selected audit.
- Execute the `L2` dry-run or real-provider pilot path.
- Confirm raw responses are stored.
- Inspect raw responses using the TASK-132 inspection path.
- Check whether OpenAI returned citations/sources or web-search metadata.
- Confirm citations/sources are mapped into the existing provider response/raw response shape where available.
- Run post-processing CLI for the `L2` audit.
- Confirm parsed results and scores are created where successful raw responses exist.
- Confirm aggregation/summary refreshes.
- Verify frontend source intelligence view:
  - sources render when source data exists
  - empty source state renders when OpenAI returns no usable sources
  - malformed/partial source data does not crash the UI
- Document findings in `docs/REAL_PROVIDER_PILOT_NOTES.md` or a project-equivalent notes document.
- Record follow-up bugs/tasks for citation mapping, parser, aggregation, or UI issues.

### Out of scope
- Do not run large real-provider audits.
- Do not increase real-provider caps.
- Do not add providers other than OpenAI.
- Do not change parser logic in this task.
- Do not change scoring formulas in this task.
- Do not change aggregation definitions in this task.
- Do not redesign source intelligence UI.
- Do not expose full raw provider answers in normal user-facing UI.
- Do not commit API keys, secrets, raw sensitive data, or local `.env` files.
- Do not treat “OpenAI returned no citations” as a code bug unless the raw response proves citations were present but not mapped.

### Acceptance criteria
- A controlled OpenAI `L2` audit is executed or fails with a controlled documented provider error.
- `L2` request path is verified to include web-search configuration/tooling using stored request snapshot, provider metadata, adapter test evidence, or another documented proof path.
- If request snapshot/provider metadata cannot prove L2 web-search enablement, the gap is documented and a follow-up task is created.
- Pilot caps are respected.
- Raw responses are stored for executed runs.
- Raw responses are inspectable without exposing secrets.
- OpenAI source/citation behavior is documented, including whether sources were returned.
- If sources/citations are returned, backend mapping preserves them in the existing source/citation shape.
- Post-processing creates parsed results and scores for successful stored responses where possible.
- Aggregation/summary refreshes after post-processing.
- Source intelligence UI displays populated, empty, or error states safely.
- Follow-up bugs/tasks are recorded for any source/citation mapping issues.
- No secrets or API keys are committed.

### Test requirements
- No automated test is required to call the real OpenAI API.
- Manually verify the selected audit uses `scdl_level=L2`.
- Manually verify or inspect that the OpenAI request path enables web search.
- Verify `scdl_level=L2` and web-search-enabled evidence from stored request snapshot, provider metadata, adapter test evidence, or another documented proof path.
- Manually verify raw response storage.
- Manually verify raw response inspection.
- Manually verify whether citations/sources are present in raw response.
- Manually verify post-processing CLI result for the `L2` audit.
- Manually verify source intelligence UI behavior.
- If any code changes are made, run relevant backend provider/post-processing tests.
- If citation/source mapping code is changed, add or update mocked unit/contract tests using redacted fixture data.
- If UI code is changed, run relevant frontend tests/build.
- Manually verify no API keys or secrets appear in logs, UI, notes, or committed files.

### Files likely affected
Optional hint, not a hard boundary.
- `docs/REAL_PROVIDER_PILOT_NOTES.md`
- `docs/REAL_RESPONSE_ANALYSIS.md`
- redacted OpenAI L2 fixture files only if explicitly needed
- small backend/frontend fix files only if required to complete verification

### Commands
Use project commands from `/AGENTS.md`.

Expected local processing command example:

```powershell
.\venv\Scripts\python.exe scripts\process_audit_results.py --audit-id <L2_AUDIT_ID>
```

If code changes are made, run:
- relevant backend provider tests
- relevant backend post-processing tests
- relevant backend parser/scoring/aggregation tests if affected
- relevant frontend tests/build if UI was touched

### Dependencies
- TASK-130 — Implement OpenAI real provider adapter for L1 and L2
- TASK-131 — Add real-provider dry-run mode
- TASK-132 — Add raw response inspection screen/log
- TASK-135 — Add audit result post-processing service
- TASK-136 — Add CLI command to process stored audit results
- TASK-137 — Process current real audit and verify UI

### Escalate if
- OpenAI `L2` web search is unsupported by the configured model/API.
- The raw OpenAI response contains citations/sources that cannot be represented by the existing provider/raw response contract.
- Web-search execution requires increasing pilot caps.
- L2 source mapping requires changing parser, scoring, aggregation, provider, or raw response contracts.
- There is no reliable way to prove L2 web-search enablement from stored metadata, logs, or tests.
- Source intelligence UI requires exposing full raw provider answers.
- Any secret or API key appears in logs, UI, notes, or committed files.
- The implementation requires a new provider, new billing logic, or product decision outside this task.

### Done means
Inherits project defaults from `/AGENTS.md`.

Additional completion requirements:
- `docs/REAL_PROVIDER_PILOT_NOTES.md` includes:
  - L2 audit id
  - query count and runs per query
  - OpenAI model used
  - confirmation of web-search request path
  - proof source for web-search enablement, such as request snapshot, provider metadata, or adapter test evidence
  - any gap in current request snapshot/provider metadata
  - whether raw responses were stored
  - whether citations/sources were returned
  - whether citations/sources mapped correctly
  - post-processing summary
  - source intelligence UI result
  - follow-up bugs/tasks
- PR summary confirms no secrets or API keys were committed.

---

## TASK-139 — Analyze real Russian-language parser/scoring quality

### Status
Ready

### Goal
Evaluate how the existing parser, scoring, aggregation, and UI handle real Russian-language OpenAI `L1` and `L2` audit responses.

### Why
The current parser/scoring logic was mostly validated on mock data, but real Russian-language AI answers may expose issues in brand detection, competitor extraction, sentiment detection, recommendation detection, source handling, and score quality.

### Context
TASK-137 verified that stored real responses can be post-processed into parsed results, scores, summary, and UI views. TASK-138 specifically verified the OpenAI `L2` web-search path and source/citation behavior.

This task is an analysis and follow-up planning task. It should identify quality gaps and propose concrete follow-up fixes, not immediately rewrite parser or scoring logic.

Target example brand from testing:

```text
Окна Лабрадор
```

### Scope
- Select a small set of real Russian-language `L1` and/or `L2` audit responses.
- Use non-sensitive test queries only.
- Review stored raw answers through the approved raw response inspection path.
- Compare raw answers against parsed results.
- Compare parsed results against saved scores.
- Compare per-run scores against summary/aggregation output.
- Compare backend data against frontend display.
- Evaluate brand detection quality for Russian text:
  - exact brand mentions
  - inflected/variant mentions if present
  - quoted brand mentions
  - domain mentions if present
  - false positives
  - false negatives
- Evaluate competitor extraction quality:
  - competitors listed near the brand
  - competitors listed instead of the brand
  - missed competitors
  - false competitors
- Evaluate sentiment/recommendation extraction quality:
  - positive/negative/neutral classification
  - “recommended”, “best”, “top”, “порекомендовать”, “лучшие” style wording
  - weak or indirect recommendations
- Evaluate scoring quality:
  - visibility score
  - prominence/position behavior
  - recommendation score
  - source quality score
  - final score
  - visibility cap behavior
- Evaluate `L1` versus `L2` differences:
  - source/citation availability
  - brand visibility changes
  - competitor differences
  - score differences
- Evaluate UI quality for real Russian text:
  - Cyrillic rendering
  - long query/answer fragments
  - competitor/source display
  - empty states
  - score readability
- Document findings in `docs/REAL_RESPONSE_ANALYSIS.md` or `docs/REAL_PROVIDER_PILOT_NOTES.md`.
- Convert observed issues into concrete follow-up bug/task proposals.

### Out of scope
- Do not change parser logic in this task.
- Do not change scoring formulas in this task.
- Do not change aggregation logic in this task.
- Do not change OpenAI adapter behavior in this task.
- Do not add new provider integrations.
- Do not run large real-provider audits.
- Do not increase pilot caps.
- Do not add frontend redesign work.
- Do not add AI-generated recommendations.
- Do not commit raw sensitive response data, API keys, or secrets.
- Do not make product decisions silently.

### Acceptance criteria
- At least one real Russian-language raw response is compared raw → parsed → scored → displayed.
- Brand detection issues are classified as acceptable behavior, false positive, false negative, or missing variant handling.
- Competitor extraction issues are classified as acceptable behavior, missed competitor, false competitor, or unsupported extraction pattern.
- Sentiment/recommendation issues are classified as acceptable behavior, misclassification, unsupported Russian keyword/pattern, or ambiguous language.
- Scoring issues are classified as acceptable behavior, formula issue, component issue, visibility issue, source issue, or aggregation issue.
- `L1`/`L2` differences are documented if both modes have usable pilot data.
- UI issues caused by Cyrillic or real Russian response shapes are documented separately from backend parser/scoring issues.
- Follow-up fixes are written as concrete task proposals or bug entries.
- No parser/scoring/provider/aggregation contract changes are made in this task.
- No secrets or API keys are included in committed notes.

### Test requirements
- No new automated tests are required if this task only documents analysis.
- Manually verify that inspected examples exist in stored raw response inspection or pilot notes.
- Manually verify that parsed results and scores correspond to the selected raw responses.
- Manually verify frontend display for selected Russian-language audit data.
- Manually verify that no API keys, secrets, auth cookies, or sensitive raw data are included in committed documentation.
- Verify the task file and analysis documents are saved as UTF-8 and Russian text such as `Окна Лабрадор` is not corrupted.
- If redacted fixtures are added from real responses, ensure sensitive data is removed and document what was redacted.
- If any code changes are made, run the relevant backend/frontend tests affected by those changes.

### Files likely affected
Optional hint, not a hard boundary.
- `docs/REAL_RESPONSE_ANALYSIS.md`
- `docs/REAL_PROVIDER_PILOT_NOTES.md`
- `docs/TASKS.md` or follow-up task backlog
- redacted fixture files only if explicitly needed

### Commands
Use project commands from `/AGENTS.md`.

If this is documentation-only, no full test run is required unless project policy requires it.

If fixtures or code are changed, run the relevant backend/frontend tests affected by those changes.

### Dependencies
- TASK-137 — Process current real audit and verify UI
- TASK-138 — Test OpenAI L2 web-search response and source mapping

### Escalate if
- No usable Russian-language real responses are available.
- Stored raw responses cannot be inspected safely.
- Real response data contains sensitive information that cannot be committed or safely redacted.
- Parser/scoring fixes are required before analysis can be completed.
- L1 or L2 behavior is too ambiguous to evaluate without a product decision.
- The analysis reveals that current parser/scoring contracts cannot represent real Russian-language behavior.

### Done means
Inherits project defaults from `/AGENTS.md`.

Additional completion requirements:
- Analysis document clearly separates:
  - provider adapter issues
  - Russian brand detection issues
  - Russian competitor extraction issues
  - Russian sentiment/recommendation issues
  - scoring issues
  - aggregation issues
  - UI issues
  - product/query-design issues
- Follow-up work is listed as concrete bugs or tasks.
- PR summary confirms no secrets, API keys, auth cookies, or sensitive raw data were committed.
- PR summary confirms UTF-8 encoding was preserved for Russian-language examples.

---

## Phase G — Post-pilot parser/scoring stabilization

Tasks in this phase must be written only after TASK-137, TASK-138, and TASK-139 are complete.

Potential areas:
- post-processing idempotency fixes
- Russian brand detection improvements
- Russian competitor extraction improvements
- sentiment/recommendation keyword expansion
- OpenAI L2 source/citation mapping fixes
- redacted real-response fixtures
- scoring calibration
- source intelligence UI fixes
