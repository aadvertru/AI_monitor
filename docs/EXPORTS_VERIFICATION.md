# Exports Verification Checklist

Manual QA checklist for DOCX/Excel exports and Repeat Audit.

## Result Statuses

Use one status per scenario:

- Not run
- Pass
- Fail
- Blocked
- Partial

## Result Table

| ID | Scenario | Status | Issue ID | Notes |
| --- | --- | --- | --- | --- |
| X-S01 | Excel export for completed audit | Pass |  | Automated regression: `test_export_data.py` |
| X-S02 | Excel export for partial audit | Pass |  | Automated regression: `test_export_data.py` |
| X-S03 | DOCX export for completed audit | Pass |  | Automated regression: `test_export_data.py` |
| X-S04 | DOCX export for partial audit | Pass |  | Automated regression: `test_export_data.py` |
| X-S05 | Export with no evaluation | Pass |  | Automated regression: `test_export_data.py` |
| X-S06 | Export with no sources | Pass |  | Automated regression: `test_export_data.py` |
| X-S07 | Export includes model summary | Pass |  | Automated regression: `test_export_data.py` |
| X-S08 | Export includes answer matrix/report section | Pass |  | Automated regression: `test_export_data.py` |
| X-S09 | Export includes source domains | Pass |  | Automated regression: `test_export_data.py` |
| X-S10 | Export includes concepts/competitors | Pass |  | Automated regression: `test_export_data.py` |
| X-S11 | Export does not include raw provider data | Pass |  | Automated safety regression |
| X-S12 | Non-owner cannot download export | Pass |  | Automated endpoint auth regression |
| X-S13 | Repeat audit copies configuration only | Pass |  | Automated backend/frontend regression |
| X-S14 | Repeat audit does not copy results | Pass |  | Automated backend regression |

## Final Verification Results

Date: 2026-05-06

Verification scope: automated Phase X regression coverage for export generation, download endpoints,
frontend download buttons, and Repeat Audit behavior.

Commands:

```bash
.\venv\Scripts\python.exe -m pytest tests\api\test_export_data.py tests\api\test_duplicate_audit.py
.\venv\Scripts\python.exe -m ruff check apps\api\export_data.py apps\api\export_excel.py apps\api\export_docx.py apps\api\export_openxml.py apps\api\main.py tests\api\test_export_data.py tests\api\test_duplicate_audit.py
cd apps/web && npm test -- src/features/audits/AuditSummaryPage.test.tsx
cd apps/web && npm run typecheck
```

Result:

```text
Backend export + repeat tests: 14 passed
Frontend export + repeat tests: 27 passed
Backend ruff: passed
Frontend typecheck: passed
Known warning: pytest cache warning from existing .pytest_cache filesystem state
```

## Scenarios

### X-S01 - Excel Export For Completed Audit

Purpose: verify that a completed audit can be exported as `.xlsx`.

Preconditions: authenticated owner has a completed audit with at least one successful run.

Steps:
1. Open the audit summary page.
2. Click `Export Excel`.
3. Open the downloaded workbook.

Expected result: workbook opens successfully and includes the required sheets.

Actual result:

Status: Not run

Issue ID:

### X-S02 - Excel Export For Partial Audit

Purpose: verify that a partial audit can be exported without crashing.

Preconditions: authenticated owner has a partial audit with at least one failed or missing run.

Steps:
1. Open the partial audit summary page.
2. Click `Export Excel`.
3. Open the downloaded workbook.

Expected result: workbook opens successfully and partial/failure data is represented safely.

Actual result:

Status: Not run

Issue ID:

### X-S03 - DOCX Export For Completed Audit

Purpose: verify that a completed audit can be exported as `.docx`.

Preconditions: authenticated owner has a completed audit with at least one successful run.

Steps:
1. Open the audit summary page.
2. Click `Export DOCX`.
3. Open the downloaded document.

Expected result: document opens successfully and contains the audit report sections.

Actual result:

Status: Not run

Issue ID:

### X-S04 - DOCX Export For Partial Audit

Purpose: verify that a partial audit can be exported without crashing.

Preconditions: authenticated owner has a partial audit with at least one failed or missing run.

Steps:
1. Open the partial audit summary page.
2. Click `Export DOCX`.
3. Open the downloaded document.

Expected result: document opens successfully and partial/failure data is represented safely.

Actual result:

Status: Not run

Issue ID:

### X-S05 - Export With No Evaluation

Purpose: verify exports remain usable when answer evaluation data is absent.

Preconditions: authenticated owner has an audit with runs but no evaluation rows.

Steps:
1. Open the audit summary page.
2. Export both Excel and DOCX.
3. Inspect accuracy/evaluation sections.

Expected result: missing evaluation is shown as `N/A`, empty, or explanatory text; export succeeds.

Actual result:

Status: Not run

Issue ID:

### X-S06 - Export With No Sources

Purpose: verify exports remain usable when source citations are absent.

Preconditions: authenticated owner has an audit with no source citations/source domains.

Steps:
1. Open the audit summary page.
2. Export both Excel and DOCX.
3. Inspect source sections.

Expected result: source sections show an empty-state message or empty rows; export succeeds.

Actual result:

Status: Not run

Issue ID:

### X-S07 - Export Includes Model Summary

Purpose: verify model-level metrics are included.

Preconditions: authenticated owner has an audit with one or more model targets and processed runs.

Steps:
1. Export Excel and DOCX.
2. Inspect the model summary section/sheet.

Expected result: model display names, model IDs, levels, and summary metrics are present.

Actual result:

Status: Not run

Issue ID:

### X-S08 - Export Includes Answer Matrix/Report Section

Purpose: verify per-query/per-target answer matrix data is included.

Preconditions: authenticated owner has an audit with multiple seed queries or model targets.

Steps:
1. Export Excel and DOCX.
2. Inspect the answer matrix/report section.

Expected result: queries and target/run status data are present without raw prompts or raw answers.

Actual result:

Status: Not run

Issue ID:

### X-S09 - Export Includes Source Domains

Purpose: verify source-domain aggregation is included.

Preconditions: authenticated owner has an L2/source-intelligence audit with citations.

Steps:
1. Export Excel and DOCX.
2. Inspect source domain and source URL sections.

Expected result: registrable domains, counts, URLs, and source metadata are present.

Actual result:

Status: Not run

Issue ID:

### X-S10 - Export Includes Concepts/Competitors

Purpose: verify concept and competitor candidate sections are included.

Preconditions: authenticated owner has an audit with extracted concepts or competitor candidates.

Steps:
1. Export Excel and DOCX.
2. Inspect concepts/competitors sections.

Expected result: concept text, categories, counts, competitor names, domains, and confidence values are present.

Actual result:

Status: Not run

Issue ID:

### X-S11 - Export Does Not Include Raw Provider Data

Purpose: verify export safety.

Preconditions: authenticated owner has an audit with raw responses, provider metadata, and diagnostics.

Steps:
1. Export Excel and DOCX.
2. Search exported content for raw provider fields and secret markers.

Expected result: exported content does not include raw prompts, raw answers, request headers, API keys, authorization headers, or `sk-` secrets.

Actual result:

Status: Not run

Issue ID:

### X-S12 - Non-owner Cannot Download Export

Purpose: verify export ownership enforcement.

Preconditions: two users exist; user B knows user A's audit ID.

Steps:
1. Log in as user B.
2. Request user A's Excel export URL.
3. Request user A's DOCX export URL.

Expected result: both requests are rejected with controlled auth/ownership errors and no file download.

Actual result:

Status: Not run

Issue ID:

### X-S13 - Repeat Audit Copies Configuration Only

Purpose: verify Repeat Audit creates a new audit from saved setup.

Preconditions: authenticated owner has an audit with seed queries, model targets, locale fields, providers, and SCDL settings.

Steps:
1. Open the audit summary page.
2. Click `Repeat audit`.
3. Open the newly created audit.
4. Inspect the audit setup.

Expected result: new audit has copied brand, domain, description, seed queries, model targets, provider/settings, and status `created`.

Actual result:

Status: Not run

Issue ID:

### X-S14 - Repeat Audit Does Not Copy Results

Purpose: verify repeated audits do not inherit result-owned data.

Preconditions: authenticated owner has a completed or partial source audit with runs/results/raw responses/scores/evaluations/sources.

Steps:
1. Click `Repeat audit`.
2. Open the new audit summary, results, and sources pages.

Expected result: new audit has no jobs, runs, raw responses, parsed results, scores, evaluations, source records, provider diagnostics, or completed result rows.

Actual result:

Status: Not run

Issue ID:

## Captured Issues

Use this template for any issue found during the checklist.

```text
Issue ID:
Scenario ID:
Severity: blocker | high | medium | low
Environment:
Steps to reproduce:
Expected:
Actual:
Evidence:
Owner:
Status:
```
