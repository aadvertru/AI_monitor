# Exports and Reporting Contract

This contract defines the MVP export/reporting behavior for audit results.

## Export Types

MVP export types:

- `excel`
- `docx`

Future export types, out of scope for Phase X:

- `pdf`
- `csv`
- `json`

## Data Sources

Exports must use the same backend DTOs/services as the UI:

- `GET /audits/{id}/summary-v2`
- `GET /audits/{id}/answer-matrix`
- `GET /audits/{id}/source-domains`
- concepts and competitor candidates exposed through result/summary DTOs
- audit metadata/detail DTOs
- provider diagnostics DTOs

Exports must not implement hidden aggregation, scoring, parsing, evaluation, or source-domain logic. If a value is shown in an export, it must come from the same backend contract used by the UI or from audit metadata.

## Shared Report Sections

Excel and DOCX reports should cover the same report concepts, with format-specific layout:

- audit metadata
- tested scope
- general summary
- model summary
- answer matrix
- source domains
- concepts
- competitor candidates
- provider diagnostics
- methodology notes

Missing optional sections must render safely as empty or "not available" sections instead of failing the export.

## Safety Rules

Exports must not include:

- raw provider responses
- raw prompts
- API keys
- request headers
- raw tool results
- raw annotations
- stack traces
- internal secrets

Raw AI answers and user-provided content may be included only when they are already exposed through safe normalized DTO fields used by the UI, such as answer excerpts or safe answer text. Exports must not read from raw response storage directly to fill report sections.

## Endpoints

Recommended MVP direct download endpoints:

```http
GET /audits/{id}/exports/excel
GET /audits/{id}/exports/docx
```

These endpoints:

- require authentication;
- enforce audit ownership/admin access through the existing audit access guard;
- return a generated file synchronously for small MVP exports;
- return a safe controlled error if an export cannot be generated.

Future direction for large exports:

```http
POST /audits/{id}/exports
GET /exports/{export_id}/download
```

Large exports should move to background jobs with export status tracking.

## File Naming

Use safe generated filenames:

- `audit-{audit_id}-summary-{timestamp}.xlsx`
- `audit-{audit_id}-report-{timestamp}.docx`

Avoid brand names, user emails, or other user-controlled strings in filenames unless a future task introduces explicit sanitization and tests.

The timestamp should be filesystem-safe, for example `YYYYMMDD-HHMMSS`.

## Internationalization

Export labels should use the selected locale if the endpoint or frontend passes a supported locale.

Raw AI answers, query text, brand names, and other user content must not be translated.

If locale is not supplied, exports may use English labels by default.

## Testing Plan

Backend tests:

- export uses summary/matrix/source DTO services;
- completed audit export;
- partial audit export;
- audit with missing evaluation;
- audit with no sources;
- legacy audit export;
- safe filename;
- no raw provider data or secrets;
- auth/ownership enforced on download endpoints.

Frontend tests:

- download button calls the correct endpoint;
- loading state;
- safe error state;
- disabled/export-unavailable state if applicable;
- raw backend/provider errors are not displayed.

## Non-Goals

Phase X does not implement:

- PDF export;
- CSV/JSON export;
- async export queue;
- export history;
- new scoring, parser, source, or evaluation aggregation;
- translation of raw user or AI content.
