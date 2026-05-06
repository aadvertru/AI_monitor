# Answer Matrix UI Verification

Phase W validation for the Web6/Web7 answer matrix UI.

## Automated checks

- `npm test -- src/features/audits/AnswerMatrixShell.test.tsx src/features/audits/AuditDetailPage.test.tsx src/features/audits/AuditSummaryPage.test.tsx src/test/i18nRegression.test.tsx src/lib/api/client.test.ts src/test/fixtures.test.ts`
  - Result: passed, 100 tests.
- `npm run typecheck`
  - Result: passed.

## Scenario checklist

| Scenario | Status | Coverage |
| --- | --- | --- |
| Matrix fetches `GET /audits/{id}/answer-matrix` and renders inside the audit detail/summary route | Passed | `AnswerMatrixShell.test.tsx`, detail/summary integration tests |
| Rows use backend questions and columns use backend model targets | Passed | Matrix alignment test |
| Cells align by `target_id`, including missing-cell placeholders | Passed | Matrix alignment test |
| Cell states render success, error, timeout, rate-limited, pending, skipped, and missing safely | Passed | Cell rendering and edge-state tests |
| Verdict badges render visible/not visible/partial/unknown/not applicable without recalculating scores | Passed | Cell rendering test |
| Provider diagnostics render without exposing raw response, prompt, headers, stack traces, or secrets | Passed | Safe expansion and diagnostic tests |
| Expand panel shows normalized fields only and falls back to excerpt-only answer text | Passed | Safe expansion test |
| Filters support level, AI family, model, verdict, query type, and run status | Passed | Filter test |
| Empty, partial, failed, running, and OpenRouter L2 experimental states are understandable | Passed | Edge-state tests |
| Horizontal scroll and sticky question column preserve matrix usability | Passed | DOM/CSS-class regression test |
| English/Russian UI translations do not translate raw user content | Passed | i18n regression tests |

## Manual QA notes

Browser QA was run against local audit `/audits/45`, a partial OpenRouter audit with two model targets and one rate-limited cell.

Verified:

- answer matrix renders on the audit detail route;
- backend questions render as rows and model targets render as columns;
- completed and failed/rate-limited cells render safely;
- provider diagnostics render without exposing raw payload fields;
- details panel opens from a matrix cell and shows normalized/excerpt data;
- no `raw_response`, `raw_prompt`, `raw_tool_result`, `raw_annotations`, `api_key`, `authorization`, or `stack_trace` strings were visible in the inspected DOM;
- EN/RU language switch renders translated matrix labels while preserving user/query text.

Still useful for future manual QA:

- one completed L1 audit with at least two model targets;
- one L2 OpenRouter audit with citations;
- one audit containing legacy rows or missing target cells.

## Non-goals Verified

- No parser, scoring, provider, or aggregation logic was changed.
- The UI does not fetch raw provider responses.
- The UI does not recompute scores or verdicts.
- The UI does not expose raw prompt, raw answer, headers, API keys, or stack traces.
