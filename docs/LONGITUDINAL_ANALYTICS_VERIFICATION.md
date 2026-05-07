# Longitudinal Analytics Verification

Phase: Z - Longitudinal Analytics

Status values:

- Not run
- Pass
- Fail
- Blocked
- Partial

## Result Table

| Scenario | Focus | Result | Evidence | Notes |
| --- | --- | --- | --- | --- |
| Z-S01 | Comparison candidates list | Pass | `tests/api/test_audit_read_run_results.py::test_comparison_candidates_returns_owned_terminal_same_domain` | Owner-only, terminal, usable-data candidates covered. |
| Z-S02 | Compare two completed audits | Pass | `tests/api/test_audit_read_run_results.py::test_compare_audits_returns_deltas_and_safe_changes` | Overall/model/source/concept/competitor deltas covered. |
| Z-S03 | Compare audits with missing evaluation | Pass | `tests/analysis/test_longitudinal_snapshots.py`, frontend null fixtures | Null accuracy/evaluation values remain safe. |
| Z-S04 | Compare audits with changed model set | Pass | `libs/analysis/longitudinal_snapshots.py`, `apps/web/src/features/audits/AuditLongitudinalPanel.test.tsx` | Added/removed/persisted model states are represented in DTO/UI. |
| Z-S05 | Visibility trend chart/table | Pass | `get_brand_audit_trends` API test, `AuditLongitudinalPanel.test.tsx` | Trend table renders latest points. |
| Z-S06 | Accuracy trend null-safe | Pass | `auditTrendsFixture`, client fixture tests | Null accuracy values round-trip and render as `N/A`. |
| Z-S07 | Source domain changes | Pass | `tests/analysis/test_longitudinal_diffs.py`, comparison API test | Added/removed/increased/decreased source domains covered. |
| Z-S08 | Concept changes | Pass | `tests/analysis/test_longitudinal_diffs.py`, comparison API test | Case/whitespace normalized changes covered. |
| Z-S09 | Competitor changes | Pass | `tests/analysis/test_longitudinal_diffs.py`, comparison API test | Competitor change normalization covered. |
| Z-S10 | No previous audits empty state | Pass | `AuditLongitudinalPanel.test.tsx` | Empty state renders without comparison fetch failure. |
| Z-S11 | Legacy audit comparison | Pass | Existing API compatibility tests plus transient snapshot path | Legacy-safe behavior is implemented; manual legacy dataset QA remains recommended. |
| Z-S12 | No raw provider data exposed | Pass | `fixtures.test.ts`, API DTO tests, snapshot service tests | Raw answers, prompts, request snapshots, headers, and secrets are excluded. |

## Manual QA Checklist

Run these in the UI when a representative local dataset is available:

1. Run the same brand/domain audit twice.
2. Open the latest audit and load historical comparison.
3. Compare current audit with a previous audit.
4. Verify overall deltas.
5. Verify model deltas.
6. Verify source domain changes.
7. Verify concept and competitor changes.
8. View trend table.
9. Test a brand with no previous audits.
10. Test missing evaluation data.
11. Test domain-missing brand-name fallback warning.
12. Test cancelled-with-data snapshot if a cancelled audit with usable runs exists.

### Browser QA - 2026-05-07

Environment:

- Local API: `http://127.0.0.1:8000`
- Local UI: `http://127.0.0.1:5173`
- User: `user@example.com`

Results:

- Pass: created two audits with the same brand/domain (`QA Longitudinal 558125`, `qa-long-558125.com`).
- Pass: first audit completed as audit id `47`, UI audit `#36`.
- Pass: second audit completed as audit id `48`, UI audit `#37`.
- Pass: loading history on `/audits/48` shows candidate `Audit #36`.
- Pass: comparison renders overall deltas, including `MENTIONABILITY L1 -100.0 pts`.
- Pass: model delta table renders `Google: Gemini 2.0 Flash` as persisted.
- Pass: source domain, concept, and competitor change sections render.
- Pass: trend table includes both `#36` and `#37`.
- Pass: no-previous-audits empty state verified on `/audits/45`.
- Pass: visible safety scan did not expose `sk-`, `api_key`, `authorization`, `raw_prompt`, `raw_response`, `headers`, stack traces, or tracebacks.

## Captured Issues

Use this template for every non-pass manual result:

```text
Issue ID:
Scenario:
Severity:
Status:
Environment:
Steps:
Expected:
Actual:
Evidence:
Decision:
```

## Verification Commands

```powershell
.\venv\Scripts\python.exe -m pytest tests\analysis\test_longitudinal_snapshots.py tests\analysis\test_longitudinal_diffs.py tests\api\test_audit_read_run_results.py tests\api\test_alembic_migrations.py
.\venv\Scripts\python.exe -m ruff check apps\api\main.py apps\api\audit_schemas.py libs\storage\models.py libs\analysis\longitudinal_snapshots.py libs\analysis\longitudinal_diffs.py tests\analysis\test_longitudinal_snapshots.py tests\analysis\test_longitudinal_diffs.py tests\api\test_audit_read_run_results.py tests\api\test_alembic_migrations.py apps\api\alembic\versions\2b3c4d5e6f7a_add_audit_metrics_snapshots.py apps\api\alembic\versions\1a2b3c4d5e6f_add_cancelled_audit_status.py
npm test -- src/lib/api/client.test.ts src/test/fixtures.test.ts src/features/audits/AuditLongitudinalPanel.test.tsx src/features/audits/AuditDetailPage.test.tsx
npm run typecheck
```

## Exit Assessment

Automated Phase Z verification is passing. Browser QA confirms the primary same-brand/domain comparison flow and the no-previous-audits empty state. Legacy datasets, brand-name fallback without domain, and cancelled-with-data snapshots remain lower-frequency manual scenarios to verify when suitable local data is available.
