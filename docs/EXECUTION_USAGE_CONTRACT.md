# Execution and Usage Contract

This document defines the MVP contract for usage accounting, run estimates, DB-backed
background execution, progress, cancellation, and retry.

## Status Semantics

Audit and background execution states use this shared vocabulary:

```text
created
queued
running
completed
partial
failed
cancel_requested
cancelled
```

Rules:

- `cancel_requested` is transient and not terminal.
- `cancelled` is terminal.
- Completed results are preserved after cancellation.
- If some runs completed and the user cancels remaining work, the final audit status is
  `cancelled` and completed results remain inspectable.
- `partial` is reserved for provider or processing failures where usable data exists.
- `failed` is reserved for fatal failure or no usable data.

## Background Queue Architecture

MVP uses a DB-backed job table.

Reason:

- progress polling needs persistent job IDs and persisted status;
- cancel/retry needs durable state;
- recovery after request/process interruption needs DB state as the source of truth.

An in-process worker loop may execute jobs, but enqueueing and status transitions must be
persisted in the database.

## Run Estimate

The canonical run estimate is:

```text
estimated_runs = query_count * target_count
```

`runs_per_query` is intentionally not part of the Phase Y canonical estimate because Phase M
model targets represent the execution matrix. Legacy compatibility can map older payloads into
target rows before estimate calculation.

## Usage Aggregation

Track usage by:

```text
audit
target
run
user
provider
model
level
```

Safe fields:

```text
input_tokens
output_tokens
total_tokens
cached_tokens
reasoning_tokens
web_search_requests
duration_ms
provider
model_id
level
target_id
run_id
audit_id
user_id
```

Rules:

- Missing usage must not fail aggregation.
- Usage aggregation must not expose raw provider responses, prompts, headers, API keys, tool
  payloads, stack traces, or secrets.
- Phase Y does not implement billing, token decrementing, or payment enforcement.
- If pricing data is absent, do not estimate monetary cost.

## Progress DTO

Expose progress in a polling-friendly DTO:

```text
audit_id
current_status
total_runs
completed_runs
failed_runs
skipped_runs
running_runs
queued_runs
percent_complete
provider_diagnostics
background_job_id
background_job_status
```

Rules:

- `percent_complete` is safe when `total_runs = 0`.
- Provider diagnostics must use the normalized safe diagnostic DTO.
- Progress must be auth-protected and ownership-enforced.

## Cancel Behavior

Cancel applies to active or queued audit execution.

Rules:

- Stop pending runs where possible.
- Mark active background job as `cancel_requested`.
- Preserve completed runs and their derived results.
- Mark remaining pending/skipped work as cancelled or skipped according to storage capability.
- When cancellation is applied, final audit/background job status becomes `cancelled`.
- The system does not guarantee immediate interruption of an in-flight provider HTTP call.

## Retry Failed Behavior

Retry applies only to failed, skipped, or cancelled work.

Rules:

- Do not duplicate successful runs.
- Preserve target/query identity.
- Create a new DB-backed background job for retry execution.
- Keep existing successful results inspectable.
- Retry does not rerun all successful runs.

## Test Expectations For Implementation Tasks

Later tasks must cover:

- `cancel_requested -> cancelled` transitions;
- `cancelled` as terminal state;
- DB job persistence and safe error metadata;
- progress endpoint from persisted job/run state;
- retry failed/skipped/cancelled without duplicating successful runs;
- usage aggregation by audit, target, and user;
- no raw provider data or secrets in usage/progress/job metadata.
