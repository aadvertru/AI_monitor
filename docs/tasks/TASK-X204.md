# TASK-X204 — Implement DOCX Export Backend

## Goal

Implement DOCX report generation for audit reports using the shared export data builder.

---

## Scope

Implement:

```text
DOCX report generation
audit metadata section
general summary section
model summary table
answer matrix summary section
source domains section
concepts/competitors section
provider diagnostics section
task-scoped backend tests
```

Do not implement Excel export in this task.

---

## Required report sections

### 1. Header

Include:

```text
audit name
audit id
status
generated_at
tested levels
query count
target count
```

### 2. General Summary

Include:

```text
mentionability L1/L2
accuracy L1/L2
tone/sentiment
```

### 3. Model Summary

Table with:

```text
model
MR L1
MR L2
delta MR
accuracy L1
accuracy L2
delta accuracy
tone L1
tone L2
```

### 4. Answer Matrix Summary

DOCX does not need to reproduce full wide matrix perfectly.

Recommended:

```text
one section per query
within each query: compact table of model/level answers/verdicts
```

### 5. Source Domains

Include domain-level summary and optional top URLs.

### 6. Concepts / Competitors

Include concept list and competitor candidates.

### 7. Diagnostics and Methodology Notes

Include safe provider diagnostics and note that OpenRouter L2 is experimental where relevant.

---

## Formatting

Keep formatting simple and robust:

```text
headings
tables
short paragraphs
page breaks if useful
```

Do not overbuild styling.

---

## i18n

If export locale is available, use translated labels.

Raw answers/user content must not be translated.

---

## Safety

DOCX must not include:

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
DOCX generated for completed audit
DOCX generated for partial audit
DOCX handles no evaluation
DOCX handles no sources
key section headings exist
document can be opened/read by test library if available
no raw provider data/secrets in document text
legacy audit safe
```

---

## Acceptance criteria

- DOCX export generator exists.
- Report includes required sections.
- Uses ExportReportData.
- Handles partial/missing sections safely.
- DOCX contains no raw provider payloads/secrets.
- Task-scoped backend tests pass.
- Touched-file ruff passes.

---

## Non-goals

- Do not implement Excel export.
- Do not implement advanced design/styling.
- Do not change result aggregation.
- Do not implement PDF.
