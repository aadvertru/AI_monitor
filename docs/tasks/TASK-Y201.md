# TASK-Y201 — Define Usage, Cost, Background Execution, Retry, and Cancel Contract

## Status

Ready. Documentation-only task.

## Goal

Define the contract for usage accounting, run estimates, background execution, cancel, and retry.

This task is documentation/contract only. Do not change runtime code.

## Dependencies

Requires Phase M target/run model to be accepted.

## Required decisions

### Status semantics

Decision:

```text
Add cancelled as a terminal audit/job status.
Use cancel_requested as a transient job/run state.
```

Status set:

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

```text
cancel_requested is not terminal
cancelled is terminal
completed results are preserved after cancellation
if some runs completed and user cancels remaining work, final audit status = cancelled with completed results preserved
partial remains for provider/processing failures with usable data
failed remains for no usable data/fatal failure
```

### Background queue architecture

Decision:

```text
Use DB-backed job table for MVP.
```

Reason:

```text
progress polling, persistent job IDs, cancel, retry, and recovery require persisted job state.
```

In-process execution may be used by a worker loop, but job state must be persisted in DB.

### Run estimate

```text
estimated_runs = query_count × target_count
```

### Usage aggregation

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

Fields:

```text
input_tokens
output_tokens
total_tokens
web_search_requests
duration_ms
```

### Progress DTO

Expose:

```text
total_runs
completed_runs
failed_runs
skipped_runs
running_runs
queued_runs
percent_complete
current_status
```

### Cancel behavior

```text
stop pending runs
mark active job cancel_requested
preserve completed results
mark terminal status cancelled when cancellation is applied
```

### Retry failed behavior

```text
retry failed/skipped/cancelled runs only
do not duplicate successful runs
preserve target/query identity
```

## Test requirements

No automated tests for this doc-only task.

Later tasks must test:

```text
cancel_requested -> cancelled transitions
cancelled terminal status
DB job persistence
progress endpoint from persisted job/run state
retry failed without duplicating successful runs
usage aggregation by audit/target/user
```

## Acceptance criteria

- Contract doc exists.
- cancelled/cancel_requested decision documented.
- DB-backed job table decision documented.
- Usage aggregation fields documented.
- Progress DTO documented.
- Cancel behavior documented.
- Retry behavior documented.
- No runtime code changed.

## Escalate if

- Existing status enum cannot add cancelled without migration risk.
- Product wants partial-with-cancel-reason instead of cancelled.
- Project already has a queue architecture that conflicts with DB-backed job table.

## Commands

Documentation-only.

## Done means

Y204/Y205/Y207/Y208 can implement against clear status and queue decisions without re-deciding architecture.
