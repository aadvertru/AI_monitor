# TASK-T209 — Verify and Stabilize Source Intelligence v2

## Goal

Run the Source Intelligence v2 verification checklist and fix only issues captured during verification.

This task closes Phase T.

---

## Required input

Read:

```text
docs/SOURCE_INTELLIGENCE_V2_CONTRACT.md
docs/SOURCE_INTELLIGENCE_V2_VERIFICATION.md
```

Use captured issues from verification.

---

## Scope

Allowed fixes:

```text
URL normalization bugs
registrable-domain extraction bugs
source aggregation bugs
source-domain endpoint bugs
source-domain UI bugs
count/dedup bugs
OpenRouter L2 no-source state bugs
legacy source compatibility bugs
unsafe source rendering bugs
```

Not allowed:

```text
provider adapter redesign
parser/scoring changes
evaluation changes
competitor extraction
exports
unrelated legacy fixes
```

---

## Verification expectations

Run scenarios:

```text
T-S01 through T-S11
```

Every non-pass scenario must have a captured issue.

---

## Tests to add/update

Add task-scoped tests based on actual issues.

Likely tests:

```text
URL normalization
registrable-domain extraction
domain grouping
URL dedup
counts
endpoint auth/ownership
frontend expand/collapse
empty/no-source states
unsafe raw payload not exposed
```

---

## Acceptance criteria

- Verification document updated with final results.
- Blocker/major source intelligence issues fixed or deferred with rationale.
- Source domains group correctly.
- Expandable URL evidence works.
- L1/no-source state works.
- OpenRouter L2 missing citations handled safely.
- Raw provider/tool payloads not exposed.
- Task-scoped backend/frontend tests pass.
- Touched-file ruff/typecheck pass.

---

## Non-goals

- Do not implement new provider source extraction.
- Do not change parser/scoring.
- Do not fix unrelated bugs.
