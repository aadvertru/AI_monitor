# TASK-Z201 — Define Longitudinal Analytics Contract

## Status

Ready. Documentation-only task.

## Goal

Define the contract for comparing audits over time and showing visibility trends.

This task is documentation/contract only. Do not change runtime code.

## Required decisions

### Comparison grouping

Decision:

```text
Primary grouping key = same owner + same normalized_domain.
Secondary fallback = same owner + normalized brand name, only when normalized_domain is missing.
```

Rules:

```text
normalized_domain match is preferred
brand name fallback must be explicit and warning-producing
different owners are never compared
```

### Snapshot policy

Decision:

```text
Create immutable snapshot after terminal audit status.
```

Terminal statuses eligible:

```text
completed
partial
cancelled if usable results exist
```

Failed audits:

```text
snapshot only if usable reportable data exists; otherwise no snapshot
```

Snapshot must not mutate after creation. If recalculation is needed, create a new snapshot version.

### Snapshot contents

Capture:

```text
summary metrics
model summaries
source domain groups
concepts
competitor candidates
evaluation accuracy
run metadata
created/completed timestamp
analysis versions
```

### Analysis versions

Snapshot must include available:

```text
parser_version
scoring_version
evaluation_version
source_aggregation_version
competitor_extractor_version
```

### Missing data

Document:

```text
missing models handled
missing queries handled
changed model set handled
evaluation unavailable handled
legacy audits handled
```

## Suggested endpoints

```http
GET /audits/{id}/comparison-candidates
GET /audits/{id}/compare?previous_audit_id=...
GET /brands/{brand_id}/audit-trends
```

## Test requirements

No automated tests for this doc-only task.

Later tasks must test:

```text
normalized_domain primary matching
brand name fallback warning
immutable snapshot after terminal status
no snapshot for no-data failed audit
snapshot versioning if recalculated
legacy audits safe
no raw provider data in snapshots
```

## Acceptance criteria

- Longitudinal analytics contract documented.
- normalized_domain primary grouping selected.
- brand name fallback selected and warning-producing.
- immutable snapshot-after-terminal policy selected.
- eligible terminal statuses documented.
- snapshot contents and analysis versions documented.
- suggested endpoints documented.
- no runtime code changed.

## Escalate if

- Current audit/brand model does not store normalized_domain.
- Product wants cross-user/workspace comparisons.
- Product wants mutable snapshots instead of immutable versioned snapshots.

## Commands

Documentation-only.

## Done means

Z202+ can implement snapshots/comparisons without choosing grouping or mutability policies again.
