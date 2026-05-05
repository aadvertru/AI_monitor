# AFTER-R — Testing Checklist After Results Data Contracts v2

## Phase covered

Phase R — Results Data Contracts v2.

## Primary goal to verify

Backend provides stable summary/matrix/source/concept placeholder DTOs required for Web5/Web6/Web7 UI, without frontend-side aggregation.

---

## Backend/API tests

### Summary v2

Verify:

```text
GET /audits/{id}/summary-v2 exists
requires auth
enforces ownership
returns safe empty summary for no runs
returns completed audit summary
returns partial audit summary
returns provider diagnostics safely
groups model summaries by model/level
mentionability L1/L2 calculated backend-side
accuracy fields are null before Phase S evaluation exists
tone null if not available
legacy audits safe
OpenRouter gateway metadata safe
```

### Answer matrix

Verify:

```text
GET /audits/{id}/answer-matrix exists
requires auth
enforces ownership
columns match audit targets
rows match seed queries
cells map query × target correctly
completed cells include answer_excerpt
failed cells include safe provider_error
missing/not_run cells safe
partial audit safe
legacy audit safe
evaluation is null before Phase S
raw provider response not exposed
```

### Source domain strict placeholder

Until Phase T, verify strict placeholder behavior:

```text
GET /audits/{id}/source-domains exists
requires auth
enforces ownership
always returns domains=[]
returns warnings=[]
does not perform grouping
does not expose raw source/provider payload
stable for L1 audit
stable for L2 audit with sources
stable for legacy audit
```

### Concepts/competitors placeholders

Verify:

```text
concepts field exists
competitor_candidates field exists
empty arrays safe
legacy competitors field not broken if still present
generic phrases not reclassified as competitors in this phase
```

---

## Frontend/API tests

Verify:

```text
summary v2 client parses response
answer matrix client parses response
source domains client parses strict empty response
evaluation=null safe
empty arrays safe
provider_error typed
OpenRouter gateway metadata typed
existing results UI not broken
```

---

## Contract fixtures

Fixtures should cover:

```text
empty audit
single model L1
single model L1+L2
multi-model audit
partial audit with failed cells
OpenRouter gateway L1/L2
legacy audit
evaluation-null audit
source-domains strict placeholder
```

---

## Manual QA

Run:

```text
run mock multi-target audit
open summary-v2 API response
open answer-matrix API response
verify columns/rows/cells match expected
verify failed/partial cells safe
open source-domains response and verify domains=[]
verify legacy audit still works
verify no raw provider data
```

---

## Exit criteria

Phase R is stable when:

```text
summary v2 stable
answer matrix stable
evaluation is null until Phase S
source-domains endpoint is strict empty placeholder
concept/competitor placeholders stable
legacy safe
frontend can build Web5/Web6/Web7 without raw aggregation
```
