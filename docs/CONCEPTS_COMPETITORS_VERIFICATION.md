# Concepts and Competitor Candidates Verification

Use this checklist after Phase U changes are deployed locally or in a QA
environment. The goal is to verify that generic extracted phrases are treated as
concepts, while real competitor candidates appear only when the deterministic
extractor has competitive-context evidence.

Allowed statuses: `Not run`, `Pass`, `Fail`, `Blocked`, `Partial`.

## Result Table

| Scenario | Status | Notes | Issue ID |
|---|---|---|---|
| U-S01 | Pass | Covered by backend/API and frontend fixture tests. |  |
| U-S02 | Pass | Generic phrases are asserted under concepts, not candidates. |  |
| U-S03 | Pass | Deterministic extractor comparison-context tests pass. |  |
| U-S04 | Pass | Known competitor fixture/extractor path covered. |  |
| U-S05 | Pass | Evidence counts/types are covered; raw evidence is not exposed. |  |
| U-S06 | Pass | Results details empty concepts state covered. |  |
| U-S07 | Pass | Results details empty competitors state covered. |  |
| U-S08 | Pass | Legacy competitors fallback to concepts is covered. |  |
| U-S09 | Pass | Results details labels are covered by frontend tests. |  |
| U-S10 | Pass | Backend/frontend contract tests assert unsafe payloads are absent. |  |

## Scenarios

### U-S01 - Generic Phrases Appear as Concepts

Purpose: Confirm legacy/generic extracted phrases are displayed as concepts.

Preconditions: An audit has a successful parsed result with generic phrases such
as `brand visibility`, `answer monitoring`, or category/service phrases.

Steps:
1. Open the audit Results page.
2. Expand a successful result row.
3. Inspect the `Concepts / Phrases` section.

Expected result: Generic phrases appear under `Concepts / Phrases` with count
and evidence count.

Actual result: Pass via task-scoped backend/API and frontend fixture tests.

Status: Pass

Issue ID:

### U-S02 - Generic Phrases Do Not Appear as Competitors

Purpose: Confirm generic concepts are not mislabeled as competitors.

Preconditions: Same audit/result row as U-S01.

Steps:
1. Open the expanded result details.
2. Inspect the `Competitor Candidates` section.

Expected result: Generic phrases such as `brand visibility` or `children's
ballet classes` do not appear in `Competitor Candidates`.

Actual result: Pass. Generic phrases are not rendered in the competitor
candidate section.

Status: Pass

Issue ID:

### U-S03 - Competitor Candidate Appears With Comparison Context

Purpose: Verify deterministic competitor extraction for comparison contexts.

Preconditions: A successful answer contains a comparison/alternative context such
as `alternatives to <brand>` or `<brand> vs <competitor>`, and mentions a
brand-like competitor.

Steps:
1. Run post-processing for the audit.
2. Open the audit Results page.
3. Expand the relevant successful result row.

Expected result: The competitor appears under `Competitor Candidates` with
confidence, evidence type, and evidence count.

Actual result: Pass via deterministic extractor tests.

Status: Pass

Issue ID:

### U-S04 - Known Competitor List Match If Available

Purpose: Verify known competitor matches are treated as stronger candidates when
that input is available.

Preconditions: A test/fixture or future flow provides a known competitor list and
the answer mentions one of those competitors in a comparison context.

Steps:
1. Process the audit or fixture.
2. Inspect API response for `competitor_candidates`.
3. Inspect the UI result details if available.

Expected result: The known competitor is present with high confidence and safe
evidence summary.

Actual result: Pass via known competitor list extractor test and contract
fixtures.

Status: Pass

Issue ID:

### U-S05 - Competitor Evidence Is Displayed or Summarized

Purpose: Confirm evidence is summarized without exposing raw provider payloads.

Preconditions: An audit has at least one competitor candidate with evidence.

Steps:
1. Open the audit Results page.
2. Expand the relevant row.
3. Inspect the `Competitor Candidates` metadata.
4. Optionally inspect `/summary-v2` or `/answer-matrix` JSON response.

Expected result: UI/API shows evidence count, confidence, and evidence type. It
does not show full raw answer text, request snapshots, headers, API keys, or
tracebacks.

Actual result: Pass. API/UI expose evidence counts/types only; safety tests
assert raw provider payloads and secrets are absent.

Status: Pass

Issue ID:

### U-S06 - Empty Concepts State

Purpose: Verify empty concepts state is clear and stable.

Preconditions: A result row has no `concepts` and no legacy `competitors`.

Steps:
1. Open the audit Results page.
2. Expand that result row.

Expected result: `No concepts extracted yet.` is displayed.

Actual result: Pass via Results Details empty-state test.

Status: Pass

Issue ID:

### U-S07 - Empty Competitors State

Purpose: Verify empty competitor candidates state is clear and stable.

Preconditions: A result row has no `competitor_candidates`.

Steps:
1. Open the audit Results page.
2. Expand that result row.

Expected result: `No competitor candidates found.` is displayed.

Actual result: Pass via Results Details empty-state test.

Status: Pass

Issue ID:

### U-S08 - Legacy Audit Compatibility

Purpose: Verify old audits without persisted concepts/candidates still render.

Preconditions: A legacy audit has `ParsedResult.competitors` but no rows in the
new `concepts` or `competitor_candidates` tables.

Steps:
1. Open the legacy audit Results page.
2. Expand a row with legacy competitors.
3. Inspect details.

Expected result: Legacy competitor strings are shown under `Concepts / Phrases`.
`Competitor Candidates` remains empty unless real candidate data exists.

Actual result: Pass. Legacy competitors fallback renders under Concepts /
Phrases and not Competitor Candidates.

Status: Pass

Issue ID:

### U-S09 - Results Details Labels Are Correct

Purpose: Confirm UI terminology matches the semantic split.

Preconditions: Any audit with result rows.

Steps:
1. Open the Results page.
2. Expand a result row.
3. Inspect section headings.

Expected result: Details show `Concepts / Phrases` and `Competitor Candidates`.
Generic phrases are not labeled as competitors.

Actual result: Pass via Results Details UI test.

Status: Pass

Issue ID:

### U-S10 - Raw Provider Data Not Exposed

Purpose: Verify safety boundaries on result detail fields.

Preconditions: An audit contains raw responses and provider metadata in storage.

Steps:
1. Open Results, Summary v2, and Answer Matrix responses/UI.
2. Search the UI/API payload for unsafe strings.

Expected result: No full raw provider answer, `raw_answer`, `request_snapshot`,
headers, authorization values, API keys, `sk-` tokens, or tracebacks are exposed
through concepts/competitor candidates.

Actual result: Pass via backend/frontend contract safety tests.

Status: Pass

Issue ID:

## Captured Issues

Use this template for each issue found during verification:

```markdown
### ISSUE-U-XXX - Short title

Scenario:

Severity: low | medium | high | critical

Observed:

Expected:

Steps to reproduce:

Evidence:

Owner:

Status:
```
