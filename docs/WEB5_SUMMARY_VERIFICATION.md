# Web5 Summary Verification

Manual QA checklist for the Web5 audit summary UI.

## Scope

Verify the authenticated audit summary page that reads:

- `GET /audits/{id}`
- `GET /audits/{id}/summary`
- `GET /audits/{id}/summary-v2`
- `POST /audits/{id}/rerun-evaluation`

Do not use this checklist to validate provider execution, parser logic, scoring formulas, billing, or export generation.

## Scenarios

| ID | Scenario | Expected result | Status | Notes |
| --- | --- | --- | --- | --- |
| V-S01 | Open a completed audit with summary-v2 data | Web5 summary shell renders with status, counts, cards, model summary, and tested scope | Not run |  |
| V-S02 | Open a newly created audit with no runs | Empty Web5 state renders without crashing; legacy setup remains visible | Not run |  |
| V-S03 | Open a partial audit | Partial warning renders; completed backend metrics remain visible | Not run |  |
| V-S04 | Open a failed audit | Failed/issue state renders safely with provider diagnostics if present | Not run |  |
| V-S05 | Open an audit with no answer evaluations | Accuracy cards show `N/A`; no-evaluations notice renders | Not run |  |
| V-S06 | Open an L1-only audit | Tested scope shows only L1; L2 metrics that are unavailable show `N/A` | Not run |  |
| V-S07 | Open an L1 + L2 audit | Tested scope shows `L1 / L2`; both levels are represented in summary cards/model rows | Not run |  |
| V-S08 | Open an OpenRouter L2 audit | Tested scope shows OpenRouter and L2 experimental markers | Not run |  |
| V-S09 | Expand/collapse “What was tested” | Details section toggles without navigation or data refetch errors | Not run |  |
| V-S10 | Rerun fact-checking | Button posts to rerun endpoint, shows evaluated/skipped counts, refreshes summary-v2 | Not run |  |
| V-S11 | Rerun fact-checking failure | Safe error copy renders; no raw backend details or secrets appear | Not run |  |
| V-S12 | Provider diagnostics present | Diagnostics render safely and do not show raw prompt, headers, API keys, or tracebacks | Not run |  |
| V-S13 | Export/repeat placeholders | DOCX, Excel, and Repeat controls are visible but disabled with placeholder titles | Not run |  |
| V-S14 | Mobile-width view | Cards, tested scope, actions, and model table remain usable without overlapping text | Not run |  |

## Automated Coverage

- `apps/web/src/features/audits/AuditSummaryPage.test.tsx`
- `apps/web/src/test/fixtures.test.ts`

## Result Log

| Date | Tester | Build/commit | Result | Notes |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |
