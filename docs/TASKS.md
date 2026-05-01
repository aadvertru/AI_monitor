# Phase F3 — Backend Audit Pipeline Orchestration Tasks

This file contains tasks for turning the current manual real-provider flow into a reusable backend pipeline.

Current state:
- `POST /audits/{id}/run` schedules jobs / marks audit running.
- Provider execution and post-processing may still require separate CLI/manual steps.
- The next goal is to create a reusable backend flow:
  - schedule jobs
  - execute pending jobs
  - save raw responses
  - post-process raw responses
  - expose updated summary/results/sources
  - set final audit status

Do not start frontend integration until this backend pipeline is stable.

---

## TASK-140 — Extract reusable audit job execution service

### Status
Ready

### Goal
Extract audit job execution into a reusable backend service that can execute pending jobs for one audit without depending on dry-run CLI logic.

### Why
The current real-provider flow is split across manual steps, and job execution logic is partly tied to real-provider dry-run behavior. A reusable execution service is needed before building a full backend audit pipeline that can be called by CLI, admin/debug endpoints, or future workers.

### Context
Current flow is approximately:

```text
POST /audits/{id}/run
→ create/schedule jobs
→ manually run dry-run execution
→ manually run post-processing CLI
→ refresh UI
```

The desired backend foundation is:

```text
schedule jobs
→ execute pending jobs for one audit
→ save raw responses
→ later post-process results
```

This task only extracts and stabilizes the job execution service. It must not add the full pipeline orchestration yet.

### Scope
- Add a reusable backend service/function for executing pending jobs for one audit, for example:
  - `execute_audit_jobs(session, audit_id, provider_factory=...)`
  - or a project-equivalent name/signature.
- Execute only jobs belonging to the requested audit.
- Execute only pending/runnable jobs according to existing job/run state rules.
- Use existing provider adapter/provider factory patterns where available.
- Preserve existing mock-provider execution behavior.
- Preserve existing OpenAI real-provider guardrails from the real-provider pilot.
- Save raw responses through the existing raw response storage path.
- Normalize provider errors using existing provider/run error handling.
- Return a structured execution summary, including:
  - audit id
  - total jobs inspected
  - jobs executed
  - jobs skipped
  - successful runs
  - failed/error/timeout/rate-limited runs
  - per-job errors
  - fatal service error, if any
- Refactor existing dry-run CLI/service code to call this reusable execution service where practical.
- Add tests for service behavior.

### Out of scope
- Do not implement full audit pipeline orchestration.
- Do not run post-processing from this service.
- Do not call parser or scoring.
- Do not add new frontend UI.
- Do not add public user-facing endpoint.
- Do not introduce background worker/queue infrastructure.
- Do not change parser, scoring, aggregation, raw response, or provider contracts.
- Do not change OpenAI adapter behavior except where required to call it through the service.
- Do not increase real-provider pilot caps.
- Do not call real OpenAI API in automated tests.

### Acceptance criteria
- Pending jobs for a single audit can be executed through the reusable service.
- Jobs from other audits are not executed.
- Already terminal jobs are skipped safely.
- Successful provider responses create or update raw response records using existing storage behavior.
- Provider errors are recorded as controlled run/job errors.
- Mock-provider execution still works through the new service.
- OpenAI execution still respects real-provider enablement, provider mode, and caps.
- Existing dry-run path uses the reusable service or remains clearly equivalent without duplicated execution logic.
- Service returns a structured execution summary.
- Existing backend tests still pass.
- Automated tests do not call real OpenAI API.

### Test requirements
- Add service-level test for executing pending mock-provider jobs for one audit.
- Add test confirming jobs from another audit are not executed.
- Add test confirming terminal jobs are skipped.
- Add test confirming successful execution stores raw response.
- Add test confirming provider error is recorded safely.
- Add test confirming execution summary includes inspected/executed/skipped/success/error counts.
- Add test confirming OpenAI real-provider execution remains blocked when disabled.
- Add test confirming real-provider caps are still enforced.
- Add regression test for dry-run path if it is refactored to call the new service.
- Add assertion or mock guard confirming no real OpenAI API call is made in automated tests.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/api/...execution...`
- `apps/api/...services...`
- `apps/api/...providers...`
- `apps/api/...orchestrator...`
- `apps/api/...dry_run...`
- `tests/...execution...`
- `tests/...providers...`
- `tests/...dry_run...`

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run:
- backend execution service tests
- backend provider tests
- backend dry-run tests if refactored
- backend audit API tests affected by run/job behavior
- backend lint/typecheck commands if available

### Dependencies
- TASK-128 — Define real provider pilot constraints
- TASK-130 — Implement OpenAI real provider adapter for L1 and L2
- TASK-131 — Add real-provider dry-run mode
- TASK-135 — Add audit result post-processing service

### Escalate if
- Existing job/run storage cannot identify pending jobs for one audit reliably.
- Existing dry-run logic cannot be refactored without changing provider contracts.
- Provider execution requires changing scheduler/orchestrator contracts.
- Raw response storage path is ambiguous or duplicated.
- Real-provider policy guard cannot be reused from this service.
- Background worker/queue infrastructure becomes necessary to complete this task.
- Implementing this task requires changing parser, scoring, aggregation, or raw response contracts.

### Done means
Inherits project defaults from `/AGENTS.md`.

Additional completion requirements:
- PR summary explains how the service is reused by dry-run or why dry-run remains separate.
- PR summary confirms no parser/scoring/post-processing is run by this service.
- PR summary confirms no real OpenAI API calls are made in automated tests.

---

## TASK-141 — Add full audit pipeline service

### Status
Ready

### Goal
Add a reusable backend service that runs the full audit pipeline for one audit: schedule jobs, execute jobs, post-process stored raw responses, and return a structured pipeline summary.

### Why
The system needs one backend-level flow that can complete an audit from scheduled execution to parsed/scored/aggregated results without requiring separate manual dry-run and post-processing commands.

### Context
TASK-140 extracted reusable job execution into a service. TASK-135 added post-processing for stored raw responses. This task composes existing pieces into one service-level pipeline.

Desired flow:

```text
run_audit_pipeline(session, audit_id)
→ schedule/create jobs if needed
→ execute pending jobs
→ store raw responses
→ post-process raw responses
→ ensure summary/results endpoints reflect parsed/scored data
→ set final audit status
→ return pipeline summary
```

This task should add orchestration only. It must not move business logic into routes or CLI scripts.

### Scope
- Add a reusable full pipeline service/function for one audit, for example:
  - `run_audit_pipeline(session, audit_id, provider_factory=...)`
  - or a project-equivalent name/signature.
- Reuse existing scheduling/job creation behavior.
- Reuse `execute_audit_jobs` from TASK-140.
- Reuse post-processing service from TASK-135.
- Ensure existing summary/results endpoints reflect newly saved parsed/scored data after the pipeline completes.
- Apply explicit audit status rules:
  - `running` while pipeline is executing.
  - `completed` when all expected runs are terminal and successful/error accounting is complete, even if the brand was not found.
  - `partial` when some terminal provider/parser/scoring errors exist but usable results exist.
  - `failed` only when no usable data can be produced or a fatal pipeline error prevents completion.
- Return a structured pipeline summary, including:
  - audit id
  - scheduling summary
  - execution summary
  - post-processing summary
  - final audit status
  - fatal error, if any
- Make the service safe to re-run:
  - do not duplicate jobs if already scheduled
  - do not re-execute terminal jobs
  - do not duplicate parsed results or scores
- Add tests for pipeline orchestration behavior.

### Out of scope
- Do not add CLI command in this task.
- Do not add frontend UI.
- Do not add public user-facing endpoint.
- Do not introduce background worker/queue infrastructure.
- Do not change parser logic.
- Do not change scoring formulas.
- Do not change provider adapter behavior.
- Do not change raw response storage contract.
- Do not increase real-provider pilot caps.
- Do not call real OpenAI API in automated tests.

### Acceptance criteria
- Full pipeline service can run one audit from scheduled jobs through post-processing.
- Service reuses scheduling, job execution, and post-processing services instead of duplicating their logic.
- Pipeline sets audit status to `running` while executing.
- Pipeline ends with `completed`, `partial`, or `failed` according to explicit rules.
- Provider success with brand not found results in completed/low-score output, not failed status.
- Re-running the pipeline is safe and does not duplicate jobs, raw responses, parsed results, or scores.
- Summary/results endpoints reflect processed data after pipeline completion.
- Service returns a structured pipeline summary.
- Existing mock-provider behavior remains unchanged.
- Existing real-provider guardrails remain enforced.
- Existing backend tests still pass.
- Automated tests do not call real OpenAI API.

### Test requirements
- Add service-level test for full pipeline on a mock-provider audit.
- Add test confirming scheduling is reused or not duplicated on re-run.
- Add test confirming pending jobs are executed through `execute_audit_jobs`.
- Add test confirming post-processing service is called after execution.
- Add test confirming final `completed` status when all expected runs are terminal and usable.
- Add test confirming brand-not-found does not mark audit as failed.
- Add test confirming `partial` status when some runs/errors are terminal but usable results exist.
- Add test confirming `failed` status only for fatal/no-usable-data cases.
- Add idempotency test for re-running the full pipeline.
- Add test confirming summary/results reflect parsed/scored data after pipeline run.
- Add assertion or mock guard confirming no real OpenAI API call is made in automated tests.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/api/...pipeline...`
- `apps/api/...services...`
- `apps/api/...orchestrator...`
- `apps/api/...execution...`
- `apps/api/...post_processing...`
- `tests/...pipeline...`
- `tests/...execution...`
- `tests/...post_processing...`

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run:
- backend pipeline service tests
- backend execution service tests
- backend post-processing tests
- backend audit API tests affected by audit status/summary behavior
- backend lint/typecheck commands if available

### Dependencies
- TASK-135 — Add audit result post-processing service
- TASK-140 — Extract reusable audit job execution service

### Escalate if
- Existing scheduling logic cannot be called idempotently.
- Existing job model cannot distinguish scheduled/pending/terminal jobs reliably.
- Pipeline status transitions conflict with existing audit state rules.
- Summary/results endpoints cannot reflect processed data without contract changes.
- Full pipeline orchestration requires a queue/background worker system.
- Idempotency cannot be implemented without schema or uniqueness changes.
- Implementing this task requires changing parser, scoring, provider, raw response, or aggregation contracts.

### Done means
Inherits project defaults from `/AGENTS.md`.

Additional completion requirements:
- PR summary explains the pipeline order: schedule → execute → post-process → final status.
- PR summary explains idempotency behavior.
- PR summary confirms no real OpenAI API calls are made in automated tests.

---

## TASK-142 — Add CLI command to run full audit pipeline

### Status
Ready

### Goal
Add a local CLI command that runs the full backend audit pipeline for one audit by id.

### Why
Developers need a single safe command to complete an audit end-to-end from scheduled jobs through execution, post-processing, final status, and UI-ready results without manually running separate dry-run and post-processing commands.

### Context
TASK-141 added a reusable full audit pipeline service. This task must add only a thin CLI wrapper around that service. Business logic must remain in the pipeline service, not in the CLI script.

Expected local usage example:

```powershell
.\venv\Scripts\python.exe scripts\run_audit_pipeline.py --audit-id 8
```

Expected flow:

```text
parse audit id
→ initialize config/database session
→ call run_audit_pipeline(session, audit_id)
→ print safe pipeline summary
→ exit with correct code
```

### Scope
- Add a CLI script or project-equivalent command for running the full pipeline for one audit.
- Accept required `--audit-id` argument.
- Initialize backend config/database session using the existing project pattern.
- Call the full pipeline service from TASK-141.
- Print a safe structured summary to stdout, including:
  - audit id
  - scheduling summary
  - execution summary
  - post-processing summary
  - final audit status
  - fatal error, if any
- Return successful process exit code when the pipeline completes without fatal error.
- Return non-zero process exit code for invalid arguments, missing audit, or fatal pipeline failure.
- Ensure CLI output does not print raw answers, prompts, API keys, provider secrets, auth cookies, or sensitive config.
- Add tests for CLI behavior with mocked service/database where practical.
- Document the command in developer docs or pilot notes.

### Out of scope
- Do not implement pipeline business logic inside the CLI.
- Do not call parser/scoring directly from the CLI.
- Do not call provider adapters directly from the CLI.
- Do not add frontend UI.
- Do not add public user-facing endpoint.
- Do not process all audits globally.
- Do not introduce background worker/queue infrastructure.
- Do not change parser logic.
- Do not change scoring formulas.
- Do not change provider adapter behavior.
- Do not change raw response storage contract.
- Do not increase real-provider pilot caps.
- Do not call real OpenAI API in automated tests.

### Acceptance criteria
- CLI can be run with `--audit-id`.
- CLI can be executed from the repository root on Windows PowerShell, for example:
  - `.\venv\Scripts\python.exe scripts\run_audit_pipeline.py --audit-id 8`
- CLI calls the full pipeline service from TASK-141.
- CLI prints a safe structured pipeline summary.
- CLI exits non-zero for missing or invalid `--audit-id`.
- CLI exits non-zero for missing audit or fatal pipeline failure.
- CLI output does not include raw answers, prompts, API keys, provider secrets, auth cookies, or sensitive config.
- CLI command is documented.
- Existing backend tests still pass.
- Automated tests do not call real OpenAI API.

### Test requirements
- Add test for CLI argument parsing with valid `--audit-id`.
- Add test or smoke check confirming the script import path works when executed from the repository root.
- Add test confirming CLI calls the full pipeline service.
- Add test for missing `--audit-id`.
- Add test for invalid `--audit-id`.
- Add test for service success summary output.
- Add test for fatal service error producing non-zero exit code.
- Add test or assertion confirming CLI output does not include raw answers, prompts, API keys, provider secrets, or auth cookies.
- Add assertion or mock guard confirming no real OpenAI API call is made in automated tests.

### Files likely affected
Optional hint, not a hard boundary.
- `scripts/run_audit_pipeline.py`
- `apps/api/...pipeline...`
- `apps/api/...database...`
- `tests/...cli...`
- `tests/...pipeline...`
- `docs/...`
- `docs/REAL_PROVIDER_PILOT_NOTES.md`

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run:
- backend CLI tests
- backend pipeline service tests
- backend execution/post-processing tests if touched
- backend lint/typecheck commands if available

### Dependencies
- TASK-141 — Add full audit pipeline service

### Escalate if
- The project has no clear way to initialize config/database sessions from scripts.
- The CLI cannot be executed from the repository root without import path hacks.
- CLI execution would require duplicating pipeline service logic.
- The pipeline service cannot distinguish fatal errors from recoverable per-run errors.
- Missing audit behavior is unclear.
- Running CLI tests would require real OpenAI API calls.
- Safe output cannot be guaranteed without exposing raw response content.

### Done means
Inherits project defaults from `/AGENTS.md`.

Additional completion requirements:
- Document the exact command for Windows PowerShell local usage.
- PR summary confirms the CLI is a thin wrapper around the full pipeline service.
- PR summary confirms no raw answers, prompts, or secrets are printed.

---

## TASK-143 — Stabilize audit status transitions

### Status
Ready

### Goal
Stabilize and document audit status transitions for scheduled, running, completed, partial, and failed audits across scheduling, execution, post-processing, and full pipeline runs.

### Why
The backend pipeline now has multiple stages that can succeed, partially fail, or fail fatally. Audit status must be predictable so the UI, CLI, and future workers can correctly represent audit progress and final results.

### Context
TASK-140 added reusable job execution. TASK-141 added full audit pipeline orchestration. TASK-142 added a CLI wrapper for the full pipeline. Earlier tasks established that provider success with brand not found is a valid completed audit result, not a failed audit.

Expected audit status meaning:

```text
created   — audit exists, jobs not yet running
running   — scheduling/execution/post-processing is in progress
completed — all expected runs are terminal and processed/accounted for; brand may or may not be found
partial   — some usable results exist, but some runs or processing steps failed/skipped
failed    — no usable data can be produced, or a fatal pipeline error prevents completion
```

### Scope
- Review current audit status transitions across:
  - audit creation
  - job scheduling
  - job execution
  - post-processing
  - full pipeline service
  - CLI pipeline command
- Centralize or document status transition rules in one backend helper/service if the project structure supports it.
- Ensure status behavior follows these rules:
  - audit starts as `created` or the existing equivalent after creation
  - audit becomes `running` when pipeline execution starts
  - audit becomes `completed` when all expected runs are terminal and processed/accounted for
  - audit becomes `partial` when usable results exist but some runs or processing steps failed/skipped
  - audit becomes `failed` only for fatal/no-usable-data cases
  - parser brand-not-found result does not make audit `failed`
- Ensure summary/results endpoints remain inspectable for `partial` and `failed` audits where data exists.
- Add or update tests covering status transitions.
- Document the status rules in backend docs or code comments.

### Out of scope
- Do not add new audit statuses.
- Do not redesign the audit state machine.
- Do not add frontend UI changes.
- Do not add background workers or queue infrastructure.
- Do not change parser logic.
- Do not change scoring formulas.
- Do not change provider adapter behavior.
- Do not change raw response storage contract.
- Do not call real OpenAI API in automated tests.

### Acceptance criteria
- Status transitions are implemented or documented in one clear backend location.
- Audit creation starts with `created` or the project-approved equivalent.
- Pipeline execution sets status to `running`.
- Successful full pipeline sets status to `completed`.
- Brand-not-found parsed result can still produce `completed`.
- Mixed success/error with usable results produces `partial`.
- Fatal/no-usable-data case produces `failed`.
- `partial` audits remain inspectable through results/summary endpoints where data exists.
- Existing mock-provider behavior remains compatible.
- Existing OpenAI real-provider guardrails remain compatible.
- Existing backend tests still pass.
- Automated tests do not call real OpenAI API.

### Test requirements
- Add test for created audit initial status.
- Add test for status becoming `running` when pipeline starts.
- Add test for `completed` after all expected runs are terminal and processed.
- Add test confirming brand-not-found does not mark audit as `failed`.
- Add test for `partial` when one or more runs/processes fail but usable results exist.
- Add test for `failed` when no usable data can be produced or a fatal pipeline error occurs.
- Add test confirming `partial` audit data remains inspectable through results/summary where available.
- Add regression test confirming full pipeline status summary matches persisted audit status.
- Add assertion or mock guard confirming no real OpenAI API call is made in automated tests.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/api/...pipeline...`
- `apps/api/...status...`
- `apps/api/...models/audit...`
- `apps/api/...routes/audits...`
- `apps/api/...post_processing...`
- `tests/...pipeline...`
- `tests/...audits...`
- `tests/...status...`
- `docs/...`

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run:
- backend pipeline tests
- backend audit API tests
- backend post-processing tests
- backend status transition tests
- backend lint/typecheck commands if available

### Dependencies
- TASK-135 — Add audit result post-processing service
- TASK-140 — Extract reusable audit job execution service
- TASK-141 — Add full audit pipeline service
- TASK-142 — Add CLI command to run full audit pipeline

### Escalate if
- Existing persisted statuses differ from the documented status model.
- Existing frontend depends on different status meanings.
- Status transition rules require adding new statuses.
- Results/summary endpoints cannot safely display partial/failed audits.
- Fatal versus recoverable error classification is ambiguous.
- Implementing this task requires changing parser, scoring, provider, raw response, or aggregation contracts.

### Done means
Inherits project defaults from `/AGENTS.md`.

Additional completion requirements:
- PR summary describes the final status transition rules.
- PR summary confirms brand-not-found is not treated as audit failure.
- PR summary confirms no real OpenAI API calls are made in automated tests.

---

## TASK-144 — Verify full backend pipeline on mock and OpenAI audits

### Status
Ready

### Goal
Verify that the full backend audit pipeline works end-to-end for both mock-provider audits and small OpenAI real-provider pilot audits.

### Why
After extracting execution, adding full pipeline orchestration, adding CLI support, and stabilizing statuses, the project needs a controlled verification pass proving that the backend pipeline can complete audits without manual intermediate steps.

### Context
TASK-140 added reusable audit job execution. TASK-141 added full pipeline orchestration. TASK-142 added a CLI command for running the full pipeline. TASK-143 stabilized audit status transitions.

Expected backend flow:

```text
create audit
→ schedule jobs
→ execute jobs
→ store raw responses
→ post-process raw responses
→ save parsed results and scores
→ expose updated summary/results/sources
→ final audit status is completed/partial/failed
```

This task verifies the flow first with mock data, then with a small OpenAI pilot audit if real provider config is available.

### Scope
- Run the full pipeline CLI or service for at least one mock-provider audit.
- Verify mock audit reaches expected final status.
- Verify mock audit produces raw responses where applicable.
- Verify mock audit produces parsed results.
- Verify mock audit produces scores.
- Verify mock audit summary/results endpoints reflect processed data.
- Run the full pipeline CLI or service for one small OpenAI `L1` audit if real provider config is available.
- Run the full pipeline CLI or service for one small OpenAI `L2` audit if real provider config is available and L2 web search is supported.
- Keep OpenAI audits within pilot caps:
  - OpenAI only
  - max 3–5 queries
  - max 1 run per query unless explicitly approved
- Verify OpenAI audit raw responses are stored.
- Verify OpenAI audit parsed results and scores are created.
- Verify OpenAI audit summary/results endpoints reflect processed data.
- Verify source/citation behavior for L2 where available.
- Verify frontend can refresh and display completed/partial pipeline output without needing manual post-processing.
- Record findings in `docs/REAL_PROVIDER_PILOT_NOTES.md` or a project-equivalent verification document.
- Record any issues as follow-up bugs/tasks.

### Out of scope
- Do not add new pipeline features in this task.
- Do not change parser logic.
- Do not change scoring formulas.
- Do not change provider adapter behavior.
- Do not redesign frontend UI.
- Do not increase real-provider caps.
- Do not run large real-provider audits.
- Do not add providers other than OpenAI.
- Do not add production worker/queue infrastructure.
- Do not commit API keys, secrets, raw sensitive data, or local `.env` files.

### Acceptance criteria
- Full pipeline completes for a mock-provider audit.
- Mock-provider audit final status is correct according to TASK-143 rules.
- Mock-provider audit results and summary reflect parsed/scored data.
- Full pipeline completes or fails with a controlled documented provider/config error for OpenAI `L1`.
- OpenAI `L1` audit respects real-provider caps.
- OpenAI `L1` audit raw responses, parsed results, scores, summary, and results are verified when execution succeeds.
- OpenAI `L2` audit is verified when supported by current config/API.
- OpenAI `L2` source/citation behavior is documented.
- UI can display refreshed summary/results after full pipeline execution without a separate post-processing command.
- Any discovered issues are recorded as follow-up bugs/tasks.
- No secrets or API keys are committed.

### Test requirements
- No automated test is required to call the real OpenAI API.
- Run existing backend pipeline service tests.
- Run existing backend execution service tests.
- Run existing backend post-processing tests.
- Run existing audit status tests.
- Manually run full pipeline CLI for mock audit.
- Manually verify mock audit results/summary/status.
- Manually run full pipeline CLI for OpenAI L1 audit if config is available.
- Manually run full pipeline CLI for OpenAI L2 audit if config is available and supported.
- Manually verify OpenAI raw response storage, parsed results, scores, summary, and results.
- Manually verify no API keys or secrets appear in logs, UI, notes, or committed files.
- If code changes are made, run affected backend/frontend tests.

### Files likely affected
Optional hint, not a hard boundary.
- `docs/REAL_PROVIDER_PILOT_NOTES.md`
- `docs/PIPELINE_VERIFICATION.md`
- local `.env` file, not committed
- small backend/frontend fix files only if required to complete verification

### Commands
Use project commands from `/AGENTS.md`.

Expected local command example:

```powershell
.\venv\Scripts\python.exe scripts\run_audit_pipeline.py --audit-id <AUDIT_ID>
```

If code changes are made, run:
- relevant backend pipeline tests
- relevant backend execution tests
- relevant backend post-processing tests
- relevant backend audit API/status tests
- relevant frontend tests/build if UI was touched

### Dependencies
- TASK-140 — Extract reusable audit job execution service
- TASK-141 — Add full audit pipeline service
- TASK-142 — Add CLI command to run full audit pipeline
- TASK-143 — Stabilize audit status transitions

### Escalate if
- Full pipeline cannot run without manually invoking hidden intermediate commands.
- Mock pipeline does not produce parsed/scored data.
- OpenAI real-provider execution requires increasing pilot caps.
- OpenAI L2 web search is unsupported or cannot be verified.
- Results/summary endpoints do not reflect processed data after full pipeline completion.
- UI requires raw answer exposure to show results.
- Any secret or API key appears in logs, UI, notes, or committed files.
- Verification requires changing parser, scoring, provider, raw response, or aggregation contracts.

### Done means
Inherits project defaults from `/AGENTS.md`.

Additional completion requirements:
- Verification notes include:
  - mock audit id and result
  - OpenAI L1 audit id and result, if run
  - OpenAI L2 audit id and result, if run
  - final statuses
  - whether parsed results were created
  - whether scores were created
  - whether summary/results endpoints updated
  - UI verification result
  - follow-up bugs/tasks
- PR summary confirms no secrets or API keys were committed.

---

## TASK-145 — Add dev/admin endpoint to run full audit pipeline

### Status
Planned

### Goal
Add a safe dev/admin-only backend endpoint that can run the full audit pipeline for one audit from the API layer.

### Why
After the full backend pipeline is stable through services and CLI, the next step toward UI integration is an API-accessible execution path. This allows controlled testing from the app without putting pipeline business logic into frontend code or exposing unsafe public execution behavior.

### Context
TASK-141 added the reusable full audit pipeline service. TASK-142 added a CLI wrapper. TASK-144 verified the full backend pipeline on mock and OpenAI audits. This task adds an API endpoint only after the service and CLI path are stable.

This endpoint is not intended as the final public production execution API unless explicitly approved later.

Expected flow:

```text
POST /dev/audits/{id}/run-pipeline
or project-equivalent admin/dev route
→ auth/admin/dev guard
→ call run_audit_pipeline(session, audit_id)
→ return safe pipeline summary
```

### Scope
- Add a dev/admin-only endpoint or project-equivalent protected API route for running the full pipeline for one audit.
- Require authentication.
- Require admin role or explicit local/dev mode guard.
- Reuse the full pipeline service from TASK-141.
- Return a safe structured pipeline summary:
  - audit id
  - scheduling summary
  - execution summary
  - post-processing summary
  - final audit status
  - fatal error, if any
- Enforce existing audit ownership/admin access rules.
- Enforce real-provider guardrails and pilot caps.
- Ensure endpoint does not return raw answers, prompts, API keys, provider secrets, auth cookies, or sensitive config.
- Add tests for access control and endpoint behavior with mocked pipeline service/provider execution.
- Document that this endpoint is dev/admin-only and not a public production execution contract.

### Out of scope
- Do not add frontend UI.
- Do not replace the existing public `POST /audits/{id}/run` behavior unless explicitly approved.
- Do not expose this endpoint to regular users.
- Do not add background workers or queue infrastructure.
- Do not add billing, quotas, or production execution policy.
- Do not call real OpenAI API in automated tests.
- Do not change parser logic.
- Do not change scoring formulas.
- Do not change provider adapter behavior.
- Do not change raw response storage contract.
- Do not expose raw provider answers in the endpoint response.

### Acceptance criteria
- Endpoint exists under a clearly dev/admin-only route or project-equivalent protected route.
- Unauthenticated requests are rejected.
- Non-admin/non-dev unauthorized requests are rejected.
- Cross-user access is rejected unless simple admin access is explicitly used.
- Endpoint calls the full pipeline service from TASK-141.
- Endpoint returns safe pipeline summary.
- Endpoint does not expose raw answers or secrets.
- Mock-provider audit can be executed through the endpoint in tests using mocked provider/pipeline behavior.
- Real-provider guardrails remain enforced.
- Existing CLI path remains available.
- Existing backend tests still pass.
- Automated tests do not call real OpenAI API.

### Test requirements
- Add API test for unauthenticated rejection.
- Add API test for non-admin/non-dev rejection.
- Add API test for authorized dev/admin success path with mocked pipeline service.
- Add API test confirming endpoint calls full pipeline service.
- Add API test for missing audit behavior.
- Add API test for cross-user access behavior if ownership applies.
- Add test confirming response does not include raw answers, prompts, API keys, provider secrets, or auth cookies.
- Add test confirming real-provider disabled/guardrail behavior is respected if endpoint can trigger real provider mode.
- Add assertion or mock guard confirming no real OpenAI API call is made in automated tests.

### Files likely affected
Optional hint, not a hard boundary.
- `apps/api/...routes/dev...`
- `apps/api/...routes/admin...`
- `apps/api/...routes/audits...`
- `apps/api/...pipeline...`
- `apps/api/...dependencies...`
- `tests/...api...`
- `tests/...pipeline...`
- `docs/...`

### Commands
Use project commands from `/AGENTS.md`.

At minimum, run:
- backend API tests for the new endpoint
- backend auth/access-control tests
- backend pipeline tests affected by endpoint integration
- backend lint/typecheck commands if available

### Dependencies
- TASK-141 — Add full audit pipeline service
- TASK-142 — Add CLI command to run full audit pipeline
- TASK-143 — Stabilize audit status transitions
- TASK-144 — Verify full backend pipeline on mock and OpenAI audits

### Escalate if
- The project has no admin/dev route convention.
- The project has no safe way to restrict endpoint to admin/dev usage.
- Product requires this to be a public user-facing endpoint.
- Endpoint execution would block request/response too long and require background workers.
- Running the endpoint would require bypassing real-provider guardrails.
- Returning a useful response would require exposing raw provider answers or secrets.
- Implementing this task requires changing parser, scoring, provider, raw response, or aggregation contracts.

### Done means
Inherits project defaults from `/AGENTS.md`.

Additional completion requirements:
- PR summary explains why the endpoint is dev/admin-only.
- PR summary confirms endpoint reuses the full pipeline service.
- PR summary confirms no raw answers or secrets are returned.
- PR summary confirms no real OpenAI API calls are made in automated tests.

---

## Phase H — Frontend pipeline integration

Tasks in this phase must be written only after TASK-144 and TASK-145 are complete.

Potential areas:
- connect Start Audit button to backend pipeline endpoint
- add audit status polling
- add progress/loading state
- add user-facing execution limits
- add background worker/queue if request-time execution is too slow
- improve error display for completed/partial/failed audits
