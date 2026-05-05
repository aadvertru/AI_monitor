# AFTER-Z — Testing Checklist After Longitudinal Analytics

## Phase covered

Phase Z — Longitudinal Analytics.

## Primary goal to verify

The product can compare audits over time and show trends for visibility, accuracy, sources, concepts, and competitor candidates.

---

## Backend tests

### Metrics snapshots

Verify final policy:

```text
snapshot created for completed audit
snapshot created for partial audit with usable data
snapshot created for cancelled audit with usable data
no-data failed audit creates no snapshot
snapshot is immutable after creation
new recalculation creates new snapshot_version, does not mutate old snapshot
snapshot includes normalized_domain
snapshot includes normalized_brand_name fallback key
snapshot includes analysis versions
snapshot excludes raw provider data
legacy audit safe
```

### Comparison grouping

Primary grouping:

```text
same owner + same normalized_domain
```

Fallback grouping:

```text
same owner + normalized_brand_name only when normalized_domain is missing
fallback produces warning
```

Verify:

```text
different owners never compared
same normalized_domain candidates returned
brand-name fallback candidates returned only when domain missing
fallback warning present
different normalized_domain excluded
current audit excluded
non-terminal audits excluded
no-usable-data audits excluded
sorted newest first
legacy audits safe
```

### Audit comparison endpoint

Verify:

```text
auth required
ownership for both audits
different normalized_domain warning/rejection according to contract
brand-name fallback warning when used
overall deltas calculated
model deltas calculated
missing model handled
missing evaluation handled
legacy audit handled
no raw provider data exposed
```

### Trend endpoint

Verify:

```text
auth required
ownership enforced
terminal audits only
chronological order
mentionability trend returned
accuracy trend null-safe
cancelled-with-data included if snapshot exists
no-data failed audit excluded
legacy audits safe
no raw data exposed
```

### Change detection

Verify:

```text
source domain added/removed/persisted
source count increased/decreased
concept added/removed
competitor added/removed
case/whitespace normalization
missing previous data safe
```

---

## Frontend tests

Verify:

```text
comparison candidate selector renders
no previous audits empty state
selecting candidate loads comparison
overall deltas render
model deltas render
normalized_domain grouping warnings render
brand-name fallback warning renders
missing data warnings render
trend points render
source changes render
concept changes render
competitor changes render
i18n labels
```

---

## Manual QA

Run:

```text
run same brand/domain audit twice
open comparison candidates
compare current with previous
verify overall deltas
verify model deltas
verify source domain changes
verify concept/competitor changes
view trend chart/table
test brand with no previous audits
test missing evaluation case
test domain-missing brand-name fallback warning
test cancelled-with-data snapshot if cancel exists
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
raw snapshots containing provider payloads
```

---

## Exit criteria

Phase Z is stable when:

```text
immutable snapshots exist after terminal audits
normalized_domain primary grouping works
brand-name fallback works only when domain missing and warns
audit comparison works
visibility/accuracy trends work
source/concept/competitor changes work
missing data safe
legacy audits safe
product supports monitoring over time
```
