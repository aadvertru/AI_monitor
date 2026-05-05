# AFTER-X — Testing Checklist After Exports

## Phase covered

Phase X — Exports and Reporting.

## Primary goal to verify

Excel and DOCX exports are generated from the same backend DTOs as the UI, with safe content and correct auth/ownership. Repeat Audit is implemented as separate backend and frontend tasks.

---

## Backend tests

### Export data builder

Verify:

```text
builds report data for completed audit
builds report data for partial audit
handles no evaluation
handles no sources
handles legacy audit
uses existing summary/matrix/source services
does not include raw provider payloads
auth/ownership safe if builder checks access
```

### Excel export

Verify:

```text
workbook generated for completed audit
workbook generated for partial audit
handles no evaluation
handles no sources
required sheets exist
key headers exist
file is valid workbook
model summary included
answer matrix/report data included
source domains included
concepts/competitors included
diagnostics included if relevant
no raw provider data/secrets in workbook text
```

### DOCX export

Verify:

```text
DOCX generated for completed audit
DOCX generated for partial audit
handles no evaluation
handles no sources
required headings exist
model summary table included
answer matrix/report section included
source domains included
concepts/competitors included
diagnostics/methodology notes included
document can be read by test library if available
no raw provider data/secrets in document text
```

### Download endpoints

Verify:

```text
unauthenticated rejected
non-owner rejected
owner can download Excel
owner can download DOCX
content types correct
filenames safe
completed audit export works
partial audit export works
no-data audit behavior safe
```

### Repeat Audit backend — X207A

Verify:

```text
POST /audits/{id}/duplicate exists
unauthenticated rejected
non-owner rejected
owner can duplicate audit
new audit copies configuration only
model_targets copied
seed queries copied
status = created
jobs/runs/results/raw responses/evaluations/sources not copied
source audit unchanged
```

---

## Frontend tests

### Export buttons

Verify:

```text
Excel button calls export endpoint
DOCX button calls export endpoint
download handler invoked
loading state works
safe error state works
disabled state when endpoint unavailable
```

### Repeat Audit frontend — X207B

Verify:

```text
Repeat Audit button calls duplicate endpoint
loading state works
success navigates to new audit
new audit is not auto-started
safe error state works
button disabled while request active
```

---

## Manual QA

Run:

```text
download Excel for completed audit
download Excel for partial audit
download DOCX for completed audit
download DOCX for partial audit
inspect sheets/sections
export audit without evaluation
export audit without sources
try non-owner download
repeat audit
verify new audit has copied config
verify new audit has no results/runs/evaluations/raw responses
```

---

## Safety checks

Exports and Repeat Audit responses must not include:

```text
raw provider responses
raw prompts
API keys
headers
raw tool payloads
stack traces
internal secrets
```

---

## Exit criteria

Phase X is stable when:

```text
Excel export works
DOCX export works
downloads are auth/owner protected
exports match visible UI DTOs
Repeat Audit backend duplicate endpoint works
Repeat Audit frontend action works
Repeat Audit copies config only
no raw provider data or secrets exported/copied
```
