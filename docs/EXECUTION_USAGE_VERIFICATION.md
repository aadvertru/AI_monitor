# Execution and Usage Verification

Manual QA checklist for audit execution, usage accounting, progress polling, cancel, and retry.

Use a local authenticated user and a safe provider configuration. Do not use production credentials unless the run is explicitly approved.

## Environment

- API server is running.
- Web app is running.
- User can sign in.
- Database is migrated to the current Alembic head.
- Real-provider checks use low caps and non-sensitive prompts.

## Scenarios

### Y-S01 - Run Estimate for Small Audit

Steps:
1. Open the create audit page.
2. Add one valid brand, one seed query, and one model target.
3. Confirm the estimate request completes.

Expected:
- Estimate shows the expected run count.
- No billing limit is enforced.
- No provider call is made during estimate.

### Y-S02 - Over-Cap Audit Rejected

Steps:
1. Create or edit a draft with queries and targets above the configured run cap.
2. Submit the draft or trigger estimate.

Expected:
- Backend returns a controlled validation/policy error.
- UI shows a safe error message.
- No jobs are scheduled.

### Y-S03 - Start Audit Enqueues Background Job

Steps:
1. Open a created audit.
2. Click Start audit.

Expected:
- API returns an enqueue response with `job_id`.
- Audit status moves to running.
- Pipeline does not execute synchronously in the request.

### Y-S04 - Progress Endpoint Updates During Run

Steps:
1. Start an audit with more than one expected run.
2. Poll `GET /audits/{id}/progress`.

Expected:
- `total_runs`, queued/running/completed/failed counts, and `percent_complete` update safely.
- Provider diagnostics are present only as normalized safe fields.
- Raw prompts, raw answers, headers, and secrets are absent.

### Y-S05 - UI Progress Polling Works

Steps:
1. Start an audit from the UI.
2. Stay on the audit detail page while it runs.

Expected:
- Progress panel appears.
- Counts update without page reload.
- Polling stops when the audit reaches a terminal state.

### Y-S06 - Completed Audit Reaches Terminal State

Steps:
1. Run a small audit that should fully succeed.
2. Refresh the audit detail and results pages.

Expected:
- Audit status is completed.
- Summary, results, answer matrix, and usage views remain readable.
- Start button is available only according to current product rules.

### Y-S07 - Cancel Running Audit

Steps:
1. Start a multi-run audit.
2. Click Cancel run while it is running.
3. Confirm the dialog.

Expected:
- Pending jobs are marked cancelled.
- Completed successful runs remain preserved.
- Audit reaches a controlled partial or failed state.
- UI stops showing the audit as actively running.

### Y-S08 - Retry Failed Runs

Steps:
1. Use an audit with failed, timeout, rate-limited, or cancelled runs.
2. Click Retry failed.

Expected:
- Only failed/cancelled work is rescheduled.
- Successful runs are not duplicated.
- New background job is enqueued.

### Y-S09 - Successful Runs Not Duplicated on Retry

Steps:
1. Inspect run rows before retry.
2. Retry failed runs.
3. Inspect run rows after retry.

Expected:
- Successful source runs remain single successful records.
- Retry creates new jobs only for failed/cancelled identities.
- Idempotency keys do not collide unexpectedly.

### Y-S10 - Usage Aggregation Shown

Steps:
1. Complete at least one provider run with usage metadata.
2. Open Profile.

Expected:
- Demo token quota is still marked demo.
- Actual provider usage is shown separately.
- Real usage does not decrement demo quota.

### Y-S11 - Provider Diagnostics Safe

Steps:
1. Trigger a controlled provider error, timeout, or rate limit.
2. Open audit summary/progress/results.

Expected:
- UI shows normalized provider diagnostics.
- Retryable state is visible when applicable.
- No API keys, auth headers, raw prompts, stack traces, or raw responses appear.

### Y-S12 - No Raw Provider Data Exposed

Steps:
1. Inspect audit summary, progress, results, source domains, answer matrix, and profile responses.
2. Search visible UI and JSON responses for raw provider fields.

Expected:
- Raw answers are not shown except through admin-only raw inspection endpoints.
- `request_snapshot`, `raw_prompt`, `authorization`, `api_key`, secrets, and tokens are absent.
- Public UI remains safe even when backend has raw data stored.

## Result Table

| Scenario | Result | Evidence | Notes |
| --- | --- | --- | --- |
| Y-S01 | Pass | `tests/api/test_create_audit.py`, `apps/web/src/lib/api/client.test.ts` | Estimate endpoint and frontend client covered. |
| Y-S02 | Pass | `tests/api/test_create_audit.py` | Caps and invalid target payloads rejected before execution. |
| Y-S03 | Pass | `tests/api/test_audit_read_run_results.py`, `tests/control/test_background_jobs.py` | Owner run endpoint returns enqueue response and creates background job. |
| Y-S04 | Pass | `tests/api/test_audit_read_run_results.py` | Progress counts and safe diagnostics covered. |
| Y-S05 | Pass | `apps/web/src/features/audits/AuditDetailPage.test.tsx` | Progress panel, polling path, and running UI covered. |
| Y-S06 | Pass | `tests/control/test_background_jobs.py`, `apps/web/src/test/authenticatedSmokeFlow.test.tsx` | Pipeline completion and UI smoke flow covered. |
| Y-S07 | Pass | `tests/api/test_audit_read_run_results.py`, `apps/web/src/features/audits/AuditDetailPage.test.tsx` | Cancel endpoint and UI confirmation/action covered. |
| Y-S08 | Pass | `tests/api/test_audit_read_run_results.py`, `apps/web/src/features/audits/AuditDetailPage.test.tsx` | Retry failed/cancelled endpoint and UI action covered. |
| Y-S09 | Pass | `tests/api/test_audit_read_run_results.py`, `tests/control/test_background_jobs.py` | Retry creates new failed/cancelled jobs without duplicating successful runs. |
| Y-S10 | Pass | `tests/execution/test_usage_aggregation.py`, `tests/api/test_profile.py`, `apps/web/src/features/profile/ProfilePage.test.tsx` | Profile shows actual usage separately from demo quota. |
| Y-S11 | Pass | `tests/api/test_audit_read_run_results.py`, `apps/web/src/features/audits/AuditDetailPage.test.tsx` | Provider diagnostics remain normalized and safe. |
| Y-S12 | Pass | `tests/execution/test_usage_aggregation.py`, `tests/api/test_profile.py`, `apps/web/src/lib/api/client.test.ts` | Raw prompts, raw answers, auth headers, and secrets not exposed. |

## Captured Issues

Use this template for every non-pass result.

```text
Issue ID:
Scenario:
Severity:
Observed:
Expected:
Reproduction:
Evidence:
Decision:
```
