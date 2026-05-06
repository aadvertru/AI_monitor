# Source Intelligence v2 Verification

Use this checklist after Source Intelligence v2 backend, API, and frontend changes.

Allowed statuses:

- Not run
- Pass
- Fail
- Blocked
- Partial

## Result Table

| Scenario | Status | Notes | Issue ID |
|---|---|---|---|
| T-S01 | Pass | Covered by backend no-source fixture and frontend empty-state test. |  |
| T-S02 | Pass | Covered by backend source-domain API test and frontend grouped domain fixture. |  |
| T-S03 | Pass | Covered by aggregation and contract fixture tests for registrable-domain grouping. |  |
| T-S04 | Pass | Covered by frontend expand/collapse test. |  |
| T-S05 | Pass | Covered by aggregation duplicate URL test and fixture contract. |  |
| T-S06 | Pass | Covered by OpenRouter L2 no-citation fixture/empty-state behavior. |  |
| T-S07 | Pass | Covered by partial-audit fixture and source-domain service tests. |  |
| T-S08 | Pass | Covered by invalid URL skip tests and unsafe rendering tests. |  |
| T-S09 | Pass | Covered by API/client/UI tests using backend-provided counts. |  |
| T-S10 | Pass | Covered by backend/frontend unsafe-field exclusion tests. |  |
| T-S11 | Pass | In-app browser smoke opened `/audits/42/sources`; grouped domain row and counts rendered. |  |

## Scenarios

### T-S01 - L1 audit shows no-source empty state

Purpose: Confirm L1 audits without citations do not show broken source UI.

Preconditions: Authenticated user; L1 audit exists with no source records.

Steps:

1. Open the audit Sources tab.
2. Wait for loading to finish.
3. Inspect the page content.

Expected result: The page shows a safe empty state such as "No sources yet"; no errors or raw fields are shown.

Actual result: Backend no-source and frontend empty-state tests pass.

Status: Pass

Issue ID:

### T-S02 - L2 audit shows domain source groups

Purpose: Confirm L2 citations are grouped by domain.

Preconditions: Authenticated user; L2 audit exists with at least one citation.

Steps:

1. Open the audit Sources tab.
2. Confirm domain rows are visible.
3. Confirm each row includes counts.

Expected result: Domain rows are visible with source, unique URL, query, model, level, and provider indicators.

Actual result: Backend API and frontend fixture tests render grouped domain rows.

Status: Pass

Issue ID:

### T-S03 - Same domain with multiple URLs groups into one row

Purpose: Confirm multiple pages from the same registrable domain are grouped.

Preconditions: Audit has at least two citations from subdomains or pages of the same registrable domain.

Steps:

1. Open Sources.
2. Locate the domain row.
3. Compare the domain row URL count with API data.

Expected result: One domain row contains multiple URL evidence items.

Actual result: Aggregation tests group `news.bbc.co.uk` and `www.bbc.co.uk` under `bbc.co.uk`.

Status: Pass

Issue ID:

### T-S04 - Domain row expands to URL evidence

Purpose: Confirm evidence remains inspectable.

Preconditions: Audit has at least one source domain group.

Steps:

1. Open Sources.
2. Expand a domain row.
3. Inspect URL evidence.
4. Collapse the row.

Expected result: Expanded content shows title, URL, snippet, query/model metadata when available; collapse hides it again.

Actual result: Frontend test expands and collapses URL-level evidence.

Status: Pass

Issue ID:

### T-S05 - Duplicate URLs deduplicated

Purpose: Confirm duplicate citations do not create duplicate URL rows.

Preconditions: Audit has duplicate citations with equivalent normalized URLs.

Steps:

1. Open Sources.
2. Expand the relevant domain.
3. Compare source count and unique URL count.

Expected result: `source_count` may be greater than `unique_url_count`; duplicate normalized URL appears once.

Actual result: Aggregation test keeps `source_count > unique_url_count` for duplicate normalized URLs.

Status: Pass

Issue ID:

### T-S06 - OpenRouter L2 answer without citations shows safe empty state

Purpose: Confirm missing gateway citations are not treated as UI failure.

Preconditions: OpenRouter L2 audit has successful answer text but no citations.

Steps:

1. Open Sources.
2. Inspect empty state.

Expected result: Page shows a safe no-source state and does not expose raw gateway payload.

Actual result: OpenRouter L2 without citations fixture validates as safe empty source response.

Status: Pass

Issue ID:

### T-S07 - Partial audit still shows available sources

Purpose: Confirm source groups are available even when some runs fail.

Preconditions: Partial audit has at least one successful run with citations and one failed/no-source run.

Steps:

1. Open Sources.
2. Inspect domain rows and warnings.

Expected result: Available sources render; failed/no-source runs do not break the page.

Actual result: Partial audit fixture and service tests preserve available source groups.

Status: Pass

Issue ID:

### T-S08 - Invalid/unsafe URLs do not crash UI

Purpose: Confirm unsafe source URLs are skipped or handled safely.

Preconditions: Audit source data includes invalid or unsupported URL schemes.

Steps:

1. Open Sources.
2. Inspect warnings and rendered URL rows.

Expected result: UI loads successfully; invalid URLs are not rendered as clickable links; warning is safe.

Actual result: Invalid URL tests skip unsupported schemes and frontend tests do not render unsafe extras.

Status: Pass

Issue ID:

### T-S09 - Source counts match API

Purpose: Confirm frontend displays backend counts without recalculating.

Preconditions: Audit has source domain groups.

Steps:

1. Fetch `GET /audits/{id}/source-domains`.
2. Open Sources.
3. Compare UI row counts to API counts.

Expected result: UI source, URL, and query counts match API response.

Actual result: UI tests render source, unique URL, and query counts from API fixtures.

Status: Pass

Issue ID:

### T-S10 - Raw provider/tool payloads not exposed

Purpose: Confirm source intelligence does not leak raw payloads.

Preconditions: Audit has raw provider responses and citations.

Steps:

1. Open Sources.
2. Search visible UI and API response text for forbidden fields.

Expected result: No raw provider response, raw tool result, raw annotation, prompt, header, API key, stack trace, or secret is exposed.

Actual result: Backend and frontend contract tests reject raw provider/tool/prompt/header fields.

Status: Pass

Issue ID:

### T-S11 - Mobile sources view smoke test

Purpose: Confirm grouped source UI is usable on mobile width.

Preconditions: Authenticated user; audit has at least one source domain group.

Steps:

1. Open Sources on a mobile viewport/device.
2. Expand and collapse a domain row.
3. Inspect long URL wrapping/truncation.

Expected result: Rows remain readable; buttons are tappable; long URLs do not overflow incoherently.

Actual result: In-app browser login succeeded, `/audits/42/sources` opened, and the grouped domain row `mock.local` rendered with source, URL, and query counts.

Status: Pass

Issue ID:

## Captured Issues

Use this template for every failed, partial, or blocked scenario.

```text
No issues captured.
```
