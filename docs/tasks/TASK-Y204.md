# TASK-Y204 — Add DB-Backed Background Job Queue Foundation

## Status

Ready for implementation.

## Goal

Add a DB-backed background job foundation for audit pipeline execution.

## Dependencies

Requires:

```text
TASK-Y201
```

## Decision

Use DB-backed job table for MVP.

Do not implement purely in-process-only job tracking because progress/cancel/retry require persisted job IDs and statuses.

## Scope

Implement:

```text
BackgroundJob DB model/table
migration
job status enum
enqueue function
job status repository/service
lightweight worker entry point or service hook
task-scoped backend tests
```

Do not fully migrate audit pipeline in this task.

## Job fields

Suggested:

```text
id
job_type
audit_id
user_id
status
created_at
started_at
finished_at
error_code
error_message_safe
progress_metadata
cancel_requested_at
```

Statuses:

```text
queued
running
completed
failed
cancel_requested
cancelled
```

## Rules

- Job metadata must be JSON-safe.
- Do not store raw provider prompts/responses.
- Do not store API keys/headers.
- `cancel_requested` is transient.
- `cancelled` is terminal.
- Jobs are owner/audit scoped through audit/user.

## Tests

Backend tests:

```text
migration creates background_jobs table
job can be enqueued
queued -> running transition
running -> completed transition
running -> failed transition with safe error
running -> cancel_requested transition
cancel_requested -> cancelled transition
job metadata does not expose secrets
worker/service can fetch next queued job if implemented
legacy synchronous pipeline unaffected
```

## Acceptance criteria

- DB-backed BackgroundJob model exists.
- Job statuses include cancel_requested and cancelled.
- Jobs can be enqueued and status-updated.
- Safe error metadata stored.
- No external infra required.
- Full pipeline migration not done yet.
- Task-scoped backend tests pass.
- Touched-file ruff passes.

## Escalate if

- Migration/status enum changes conflict with existing DB status model.
- Existing job scheduler already exists and should be reused instead.
- Worker entry point requires deployment architecture decisions not yet made.

## Commands

```bash
pytest <background job model/service tests>
ruff check <touched backend files>
```

## Done means

The project has persisted job state sufficient for later run-pipeline background execution, progress, cancel, and retry.
