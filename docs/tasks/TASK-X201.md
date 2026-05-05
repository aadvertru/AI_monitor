# TASK-X201 — Define Export and Reporting Contract

## Goal

Define the export/reporting contract for audit results.

This task is documentation/contract only. Do not change runtime code.

Exports must use the same backend DTOs as the UI:

```text
summary v2
answer matrix
source domain groups
concepts
competitor candidates
evaluation data
```

Exports must not implement hidden or separate aggregation logic.

---

## Context

The Web5/Web6/Web7 UI is expected to support actions:

```text
DOCX
Excel
Repeat audit
```

This phase implements export/reporting only after the summary/matrix/source-domain contracts are stable.

---

## File to create

```text
docs/EXPORTS_CONTRACT.md
```

---

## Required decisions

### 1. Export types

Define initial export types:

```text
excel
docx
```

Optional future types:

```text
pdf
csv
json
```

Do not implement future types in this phase unless explicitly required.

### 2. Data sources

Document that exports use existing backend DTOs:

```text
GET /audits/{id}/summary-v2
GET /audits/{id}/answer-matrix
GET /audits/{id}/source-domains
concepts / competitor_candidates fields from results APIs
```

Exports must not recompute parser/scoring/evaluation/source aggregation independently.

### 3. Export sections

Define shared report sections:

```text
audit metadata
tested scope
general summary
model summary
answer matrix
source domains
concepts
competitor candidates
provider diagnostics
methodology notes
```

### 4. Safety

Exports must not include:

```text
raw provider responses
raw prompts
API keys
request headers
raw tool results
raw annotations
stack traces
internal secrets
```

### 5. Async vs sync

For MVP, exports may be synchronous if small.

Document future direction:

```text
large exports should move to background jobs
```

### 6. File naming

Define safe file naming:

```text
audit-{audit_id}-summary-{timestamp}.xlsx
audit-{audit_id}-report-{timestamp}.docx
```

Avoid brand/user names in filenames unless sanitized.

### 7. i18n

Document:

```text
export labels should use selected locale if supported
raw AI answers and user content are not translated
```

---

## Suggested endpoints

```http
GET /audits/{id}/exports/excel
GET /audits/{id}/exports/docx
```

or:

```http
POST /audits/{id}/exports
GET /exports/{export_id}/download
```

Recommended MVP:

```text
direct GET download endpoints for small exports
```

---

## Testing plan to document

Backend:

```text
export uses summary/matrix/source DTOs
completed audit export
partial audit export
audit with missing evaluation
audit with no sources
legacy audit export
safe filename
no raw provider data/secrets
auth/ownership enforced
```

Frontend:

```text
download button calls endpoint
loading state
error state
disabled state if export unavailable
no raw error displayed
```

---

## Acceptance criteria

- Export/reporting contract is documented.
- Export types are defined.
- Data sources are defined.
- Report sections are defined.
- Safety rules are defined.
- MVP sync/future async policy is documented.
- Filename policy documented.
- Testing plan documented.
- No runtime code changed.

---

## Non-goals

- Do not implement Excel export.
- Do not implement DOCX export.
- Do not implement frontend download buttons.
- Do not implement PDF.
- Do not change summary/matrix/source DTOs.
