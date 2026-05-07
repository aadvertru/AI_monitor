# Longitudinal Analytics Contract

This contract defines how audits are compared over time.

## Grouping

Primary grouping key:

```text
same owner + same normalized_domain
```

Fallback grouping key:

```text
same owner + normalized brand name
```

The domain match is preferred. Brand-name fallback is only allowed when a
normalized domain is missing, and responses must include a warning. Audits from
different owners are never compared.

## Snapshots

Create immutable metric snapshots after a terminal audit status.

Eligible terminal statuses:

```text
completed
partial
cancelled, when usable results exist
failed, only when usable reportable data exists
```

Failed audits with no usable data do not get snapshots. Existing snapshots are
never mutated. If recalculation is needed, create a new `snapshot_version`.

## Snapshot Contents

Snapshots capture comparable, frontend-safe data:

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

Snapshots must not include raw provider responses, raw prompts, headers, stack
traces, or secrets.

## Analysis Versions

Snapshots include available version metadata:

```text
parser_version
scoring_version
evaluation_version
source_aggregation_version
competitor_extractor_version
```

Missing versions are stored as `null`.

## Missing Data

Comparison and trend endpoints must handle:

```text
missing models
missing queries
changed model sets
evaluation unavailable
legacy audits without snapshots
```

Missing values should be represented as `null` or warnings, not errors, unless
ownership or grouping rules are violated.

## Suggested Endpoints

```http
GET /audits/{id}/comparison-candidates
GET /audits/{id}/compare?previous_audit_id=...
GET /brands/{brand_id}/audit-trends
```

All endpoints require authentication and ownership checks.

