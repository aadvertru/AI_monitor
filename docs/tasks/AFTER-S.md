# AFTER-S — Testing Checklist After Answer Evaluation / Fact-Check Foundation

## Phase covered

Phase S — Answer Evaluation / Fact-Check Foundation.

## Primary goal to verify

The system can create and expose answer evaluation records with verdict/rationale/confidence without mutating raw answers, parser results, or visibility scoring.

---

## Backend tests

### Audit-scoped BrandFacts

Verify:

```text
BrandFact requires audit_id
facts can reference brand_id if available
facts created from brand name/domain/description
facts are audit-scoped immutable snapshot facts
old audit facts do not change when brand fields change later
facts preserve source/type
empty description handled
legacy audit handled
no unsupported facts invented
```

### AnswerEvaluation model

Verify:

```text
migration creates model/table
valid verdicts accepted
invalid verdict rejected
evaluation links to run/query/target
confidence bounds enforced if applicable
evaluation_version stored
evaluated_at stored
legacy runs without evaluation safe
raw prompt/response fields not exposed
```

### Mock evaluator

Verify:

```text
mock evaluator deterministic
correct marker -> correct
partial marker -> partial
incorrect marker -> incorrect
empty answer -> unknown/not_applicable according to evaluator contract
evaluation output JSON-safe
no real evaluator calls in CI
```

### Rerun evaluation endpoint

Verify:

```text
POST /audits/{id}/rerun-evaluation requires auth
ownership enforced
successful runs evaluated
failed/no-answer runs skipped
existing evaluations updated/replaced
raw answers unchanged
parsed results unchanged
scores unchanged
provider calls not rerun
safe response shape
```

### Summary/matrix evaluation exposure

Verify final decisions:

```text
matrix cell includes evaluation object when present
matrix cell evaluation=null when missing
summary accuracy L1 uses strict formula correct/evaluated
summary accuracy L2 uses strict formula correct/evaluated
partial is included in evaluated_count but not counted as correct
unknown is excluded from evaluated_count
not_applicable is excluded from evaluated_count
accuracy=null when evaluated_count=0
verdict_counts returned
model accuracy calculated
rerun evaluation updates summary/matrix
```

---

## Frontend/API tests

Verify:

```text
EvaluationVerdict type supports correct/partial/incorrect/unknown/not_applicable
evaluation object parsed
evaluation=null safe
summary accuracy fields parsed
verdict_counts parsed
matrix cell evaluation parsed
verdict codes map to translation keys
rerun evaluation client calls endpoint
success invalidates summary/matrix queries
safe error handling
```

---

## Manual QA

Run:

```text
run mock audit
trigger rerun fact-checking
verify evaluation records created
verify matrix cells get verdicts
verify summary accuracy updates
verify missing evaluation appears as null/no evaluation state
verify raw answers unchanged
verify parser/scoring unchanged
verify failed/no-answer runs skipped
```

---

## Safety checks

Must not expose:

```text
raw evaluator prompt
raw evaluator response
raw provider response
API keys
headers
stack traces
```

---

## Exit criteria

Phase S is stable when:

```text
audit-scoped immutable brand facts exist
evaluation records exist
rerun evaluation works
summary/matrix expose verdicts/accuracy
missing evaluation is null
strict accuracy formula works
raw answers and parser/scoring remain unchanged
no raw evaluator/provider data exposed
```
