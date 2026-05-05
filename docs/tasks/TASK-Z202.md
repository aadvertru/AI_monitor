# TASK-Z202 — Add Immutable Audit Metrics Snapshot Model

## Status

Ready for implementation.

## Goal

Add a backend snapshot model/service for storing comparable audit metrics over time.

Snapshots make longitudinal analytics stable even if parser/scoring/evaluation logic changes later.

## Dependencies

Requires:

```text
TASK-Z201
summary v2 service
source domain service if available
concepts/competitors services if available
```

## Policy

Snapshots are immutable and created after terminal audit status.

Eligible terminal statuses:

```text
completed
partial
cancelled if usable results exist
```

No-data failed audit:

```text
do not create snapshot
```

If recalculation is required later:

```text
create a new snapshot_version
do not mutate old snapshot
```

## Scope

Implement:

```text
AuditMetricsSnapshot model/table
snapshot_version
snapshot DTO
snapshot creation service
analysis version fields
task-scoped backend tests
```

## Suggested fields

```text
id
audit_id
brand_id
user_id
normalized_domain
normalized_brand_name
snapshot_version
created_at
audit_completed_at
summary_metrics JSON
model_summaries JSON
source_domains_summary JSON
concepts_summary JSON
competitors_summary JSON
parser_version
scoring_version
evaluation_version
source_aggregation_version
competitor_extractor_version
```

## Rules

- Snapshot should not contain raw provider responses.
- Snapshot should not contain raw prompts.
- Snapshot should be owner-scoped through audit/user.
- normalized_domain is stored for comparison grouping.
- normalized_brand_name stored as fallback key.

## Tests

Backend tests:

```text
snapshot created for completed audit
snapshot created for partial audit with usable data
snapshot created for cancelled audit with usable data if status exists
snapshot not created for failed audit with no usable data
snapshot_version assigned
old snapshot not mutated when new snapshot created
normalized_domain stored
normalized_brand_name stored
analysis versions stored where available
snapshot excludes raw provider data
legacy audit safe
```

## Acceptance criteria

- Immutable AuditMetricsSnapshot model exists.
- Snapshot service exists.
- Snapshot stores normalized_domain primary grouping key.
- Snapshot stores normalized brand name fallback key.
- Snapshot versioning supported.
- No raw provider data stored.
- Task-scoped backend tests pass.
- Touched-file ruff passes.

## Escalate if

- normalized_domain is unavailable and cannot be derived safely.
- Existing status model lacks terminal states needed for snapshot trigger.
- JSON snapshot storage conflicts with project DB policy.

## Commands

```bash
pytest <snapshot model/service tests>
ruff check <touched backend files>
```

## Done means

Completed/partial/cancelled-with-data audits can produce immutable metric snapshots safe for comparison and trends.
