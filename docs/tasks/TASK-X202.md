# TASK-X202 — Add Shared Export Data Builder

## Goal

Add a backend export data builder that collects all report data from existing result DTO/services.

This shared builder will be used by Excel and DOCX exports.

---

## Scope

Implement:

```text
ExportReportData DTO
export data builder service
auth/ownership-safe data loading
safe missing-data handling
task-scoped backend tests
```

Do not generate Excel/DOCX files in this task.

---

## Data sources

The builder should use the same data as UI:

```text
summary v2 service
answer matrix service
source domains service
concepts / competitor candidates services
audit metadata/detail
provider diagnostics
```

Do not duplicate hidden aggregation logic.

---

## Suggested DTO

```python
ExportReportData(
    audit_id=...,
    audit_metadata=...,
    tested_scope=...,
    summary=...,
    model_summaries=...,
    answer_matrix=...,
    source_domains=...,
    concepts=...,
    competitor_candidates=...,
    provider_diagnostics=...,
    generated_at=...,
)
```

Adapt to project conventions.

---

## Missing data behavior

Handle safely:

```text
no evaluation
no sources
partial audit
failed audit
legacy audit
empty concepts
empty competitors
```

Do not fail export data building solely because optional sections are empty.

---

## Safety

The export data builder must not include:

```text
raw provider responses
raw prompts
API keys
headers
raw tool payloads
stack traces
```

---

## Tests

Backend tests:

```text
builds report data for completed audit
builds report data for partial audit
builds report data with no evaluation
builds report data with no sources
legacy audit safe
uses existing services/DTOs where possible
no raw provider payloads included
auth/ownership respected if builder checks access
```

---

## Acceptance criteria

- ExportReportData DTO/service exists.
- Data builder uses existing DTO/services.
- Optional sections handle empty/null safely.
- No raw provider data/secrets included.
- Task-scoped backend tests pass.
- Touched-file ruff passes.

---

## Non-goals

- Do not generate Excel/DOCX files.
- Do not add download endpoints.
- Do not implement frontend.
- Do not change result aggregation methodology.
- Do not fix unrelated legacy failures.
