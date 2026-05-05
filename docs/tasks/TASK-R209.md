# TASK-R209 — Verify and Stabilize Results v2 Contracts

## Goal

Run the Results v2 verification checklist and fix only issues captured during verification.

This task closes Phase R.

---

## Required input

Read:

```text
docs/RESULTS_V2_CONTRACT.md
docs/RESULTS_V2_VERIFICATION.md
```

Use captured issues from verification.

---

## Scope

Allowed fixes:

```text
summary v2 DTO bugs
answer matrix mapping bugs
source-domain placeholder bugs
concept/competitor placeholder bugs
legacy compatibility bugs
OpenRouter gateway metadata bugs
provider diagnostic safety bugs
frontend API type/client bugs
```

Not allowed:

```text
Web5/Web6/Web7 UI implementation
evaluation/fact-check implementation
full source domain aggregation
competitor extraction
parser/scoring redesign
unrelated legacy fixes
```

---

## Verification expectations

Run scenarios:

```text
R-S01 through R-S12
```

Every non-pass scenario must have a captured issue.

---

## Tests to add/update

Add task-scoped tests based on actual issues.

Likely tests:

```text
summary v2 aggregation
matrix row/column/cell mapping
partial/failed cell safety
legacy audit compatibility
gateway metadata
safe provider diagnostics
no raw provider payloads
frontend API type parsing
```

---

## Acceptance criteria

- Verification document updated with final results.
- Blocker/major Results v2 issues fixed or deferred with rationale.
- Summary v2 stable.
- Answer matrix stable.
- Source-domain placeholder stable.
- Concepts/competitor placeholders stable.
- Legacy audits safe.
- No raw provider responses/prompts/secrets exposed.
- Task-scoped backend/frontend tests pass.
- Touched-file ruff/typecheck pass.

---

## Non-goals

- Do not implement Web5/Web6/Web7 UI.
- Do not implement evaluation.
- Do not implement full source aggregation.
- Do not implement competitor extraction.
- Do not fix unrelated bugs.
