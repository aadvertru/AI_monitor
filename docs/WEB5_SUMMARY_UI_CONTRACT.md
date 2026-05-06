# Web5 Summary UI Contract

This contract defines the Web5-style audit summary page. The page is a frontend
presentation layer over existing backend result and evaluation contracts.

## Data Sources

Primary endpoints:

- `GET /audits/{id}/summary-v2`
- `POST /audits/{id}/rerun-evaluation`

Related cache surfaces:

- `GET /audits/{id}/answer-matrix`
- `GET /audits/{id}`
- `GET /audits/{id}/status`

Future endpoints:

- DOCX export
- Excel export
- repeat audit / repeat with same setup

## Frontend Responsibility

The frontend displays backend-provided values only. It may format numbers,
percentages, dates, and empty states, but it must not calculate:

- mentionability
- accuracy
- scoring
- parsing results
- source classification
- competitor/concept extraction
- evaluation verdicts

## Sections

### Audit Header

Shows audit title/brand, status, audit number, dates when available, and the
action area.

Raw audit title, brand name, model IDs, query text, and snippets are user/system
content and must not be translated.

### Tested Scope

Collapsible section showing:

- query count
- target/model count
- run count
- tested levels
- model summaries/families when provided
- OpenRouter L2 experimental marker when present

The section must be usable without hover-only behavior.

### General Summary Cards

Display from `summary-v2.overall` and `summary-v2.totals`:

- `mentionability_l1`
- `mentionability_l2`
- `accuracy_l1`
- `accuracy_l2`
- `tone`

Accuracy depends on `AnswerEvaluation` records. If evaluation data is missing,
show `N/A` / `Not evaluated`; do not substitute visibility or score.

### Model Summary

Display `summary-v2.model_summaries` rows/cards:

- model/group label
- MR L1 / MR L2
- delta MR
- accuracy L1 / accuracy L2
- delta accuracy
- tone L1 / tone L2
- gateway/OpenRouter metadata if available
- concepts / competitor candidates only if already returned by backend

Missing values must render safely as `N/A`, not as `0`.

### Actions

MVP behavior:

- Rerun fact-checking: real action wired to `POST /audits/{id}/rerun-evaluation`.
- DOCX export: disabled placeholder unless a stable export endpoint exists.
- Excel export: disabled placeholder unless a stable export endpoint exists.
- Repeat audit: disabled placeholder unless a stable repeat/duplicate action exists.

Disabled placeholders must explain that the action will be available later.

## Diagnostics and Empty States

Provider diagnostics returned by the backend should be shown with safe text only.

The UI must handle:

- completed audit
- partial audit
- failed audit
- no run data
- missing evaluation
- provider diagnostics
- L1-only audit
- L2-only audit
- OpenRouter L2 experimental target

## i18n

All static labels must use translation keys.

Do not translate:

- brand names
- model names / model IDs
- query text
- AI answers/snippets
- source snippets
- user-provided descriptions

Locale support should remain data-driven so future locales can be added without
rewriting the page.

## Safety

The Web5 summary must not display:

- raw provider response
- raw prompt
- headers
- API keys
- stack traces
- raw evaluator payload

## Test Plan

Frontend tests should cover:

- summary-v2 hook/client integration
- loading/error/empty states
- header rendering
- tested scope collapse/expand
- summary cards
- null accuracy / not evaluated state
- partial and failed audit states
- provider diagnostics
- model summary rows
- OpenRouter L2 experimental marker
- rerun fact-checking action
- disabled DOCX/Excel/repeat placeholders
- i18n labels
- raw content not translated
- no unsafe payload strings rendered
- responsive/accessibility basics where supported
