# AFTER-Y — Testing Checklist After Usage, Background Execution, Cancel, and Retry

## Phase covered

Phase Y — Usage / Background / Retry / Cancel.

## Primary goal to verify

The system supports run estimates, usage aggregation, DB-backed background audit execution, progress polling, cancellation, and retry of failed runs.

---

## Backend tests

### Usage aggregation

Verify:

```text
audit-level usage aggregation
target-level usage aggregation
user-level usage if implemented
missing usage safe
OpenRouter web_search_requests included if present
legacy runs safe
no raw provider data included
no billing/token decrementing
```

### Run estimate and caps

Verify:

```text
POST /audits/estimate requires auth
estimate empty draft
estimate one query × one target
estimate multiple queries/targets
over cap flagged/rejected according to endpoint/create semantics
legacy payload estimate
invalid target payload safe
no provider calls made
```

### DB-backed background job table

Verify mandatory architecture:

```text
background_jobs table/model exists
job can be enqueued
job has persistent job_id
job status transitions queued/running/completed/failed
job status transitions running -> cancel_requested -> cancelled
safe error metadata stored
job metadata does not expose secrets
worker/service can fetch next queued job if implemented
```

### Background execution

Verify:

```text
run-pipeline endpoint enqueues DB-backed job
request returns quickly with job/audit status
duplicate active jobs prevented
background job executes mocked pipeline
audit status becomes running
terminal status set after job completes
```

### Progress endpoint

Verify:

```text
auth required
ownership enforced
progress for created audit
progress for queued audit
progress for running audit
progress for completed audit
progress for partial/failed/cancelled audit
percent calculation safe
zero total safe
provider diagnostics safe
```

### Cancel

Final status semantics:

```text
cancel_requested is transient
cancelled is terminal
```

Verify:

```text
owner can cancel running audit
non-owner rejected
cannot cancel completed audit
active job becomes cancel_requested
pending runs skipped/cancelled
completed results preserved
final audit/job status becomes cancelled
running provider call not necessarily interrupted immediately, but cancellation is applied safely
```

### Retry failed

Verify:

```text
owner can retry failed runs
non-owner rejected
successful runs not retried
failed/skipped/cancelled runs retried according to policy
new DB-backed job created
target/query identity preserved
no duplicate successful results
provider diagnostics safe
```

---

## Frontend tests

Verify:

```text
progress display renders
polling updates progress
cancel button visible when running/queued
cancel confirmation/action works
cancelled terminal state renders
retry button visible when failed/skipped runs exist
retry action works
loading/error states safe
profile usage summary renders if integrated
demo tokens still marked demo
```

---

## Manual QA

Run:

```text
small audit estimate
over-cap audit rejected
start audit and observe DB-backed background job
watch progress update
cancel running audit
verify completed results preserved
verify final status cancelled
retry failed runs
verify successful runs not duplicated
check usage aggregation/profile usage
```

---

## Safety checks

Must not expose:

```text
raw provider responses
raw prompts
headers
API keys
stack traces
raw job payloads containing secrets
```

---

## Exit criteria

Phase Y is stable when:

```text
DB-backed background execution works
progress API/UI works
cancel_requested/cancelled semantics work
cancel preserves completed results
retry failed works without duplicates
usage aggregation safe
caps/estimates work
no real billing accidentally implemented
```
