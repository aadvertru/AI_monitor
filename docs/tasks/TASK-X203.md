# TASK-X203 — Implement Excel Export Backend

## Goal

Implement Excel export generation for audit reports using the shared export data builder.

---

## Scope

Implement:

```text
Excel workbook generation
summary sheet
model summary sheet
answer matrix sheet
source domains sheet
concepts/competitors sheet
provider diagnostics sheet if relevant
task-scoped backend tests
```

Do not implement DOCX export in this task.

---

## Required sheets

### 1. Audit Summary

Include:

```text
audit metadata
status
query count
target count
run count
mentionability L1/L2
accuracy L1/L2
tone/sentiment
generated_at
```

### 2. Model Summary

Include:

```text
model
ai_family
execution_provider
model_provider
model_id
MR L1
MR L2
delta MR
accuracy L1
accuracy L2
delta accuracy
tone L1
tone L2
```

### 3. Answer Matrix

Rows = seed queries.

Columns/cell groups = model/level targets.

Include enough information to inspect:

```text
query
query_type
model/level
status
answer_excerpt
verdict
rationale
score
sources_count
provider_error
```

Exact layout may be flattened if easier.

### 4. Source Domains

Include:

```text
domain
source_count
unique_url_count
query_count
target_count
levels
models
providers
```

Optionally include URL-level evidence in separate sheet:

```text
domain
url
title
snippet
query
model
level
provider
```

### 5. Concepts / Competitors

Include concepts and competitor candidates with counts/confidence/evidence summaries.

### 6. Diagnostics

Include provider diagnostics if any.

---

## Formatting

Keep formatting simple.

Preferred:

```text
bold headers
frozen top row if easy
auto-width if easy
percent formatting where appropriate
```

Do not overbuild styling.

---

## Safety

Excel file must not include:

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
Excel file generated for completed audit
Excel file generated for partial audit
Excel handles no evaluation
Excel handles no sources
required sheets exist
key headers exist
file is valid workbook
no raw provider data/secrets in workbook text
legacy audit safe
```

Use project spreadsheet tooling convention. If openpyxl is already available, use it for tests.

---

## Acceptance criteria

- Excel export generator exists.
- Workbook includes required sheets.
- Uses ExportReportData.
- Handles partial/missing sections safely.
- Workbook contains no raw provider payloads/secrets.
- Task-scoped backend tests pass.
- Touched-file ruff passes.

---

## Non-goals

- Do not implement DOCX export.
- Do not implement download endpoint unless unavoidable.
- Do not implement complex styling.
- Do not change result aggregation.
