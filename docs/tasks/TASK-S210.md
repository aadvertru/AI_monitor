# TASK-S210 — Verify and Stabilize Answer Evaluation Foundation

## Goal

Run the answer evaluation verification checklist and fix only issues captured during verification.

This task closes Phase S.

---

## Required input

Read:

```text
docs/ANSWER_EVALUATION_CONTRACT.md
docs/ANSWER_EVALUATION_VERIFICATION.md
```

Use captured issues from verification.

---

## Scope

Allowed fixes:

```text
brand facts bugs
evaluation model bugs
mock evaluator bugs
rerun endpoint bugs
summary/matrix evaluation field bugs
accuracy aggregation bugs
frontend API type bugs
safety/no raw data bugs
auth/ownership bugs for rerun endpoint
```

Not allowed:

```text
real LLM evaluator
Web5/Web6/Web7 final UI
parser/scoring redesign
source aggregation
competitor extraction
exports
unrelated legacy fixes
```

---

## Verification expectations

Run scenarios:

```text
S-S01 through S-S12
```

Every non-pass scenario must have captured issue.

---

## Tests to add/update

Add task-scoped tests based on actual issues.

Likely tests:

```text
brand facts creation
evaluation creation/update
rerun endpoint auth/ownership
failed/no-answer skipped
raw answers unchanged
parsed/scored results unchanged
summary accuracy aggregation
matrix cell evaluation
unknown/missing evaluation safe
no raw prompt/response/secrets exposed
frontend evaluation type parsing
```

---

## Acceptance criteria

- Verification document updated with final results.
- Blocker/major evaluation issues fixed or deferred with rationale.
- Brand facts exist and are conservative.
- Evaluation records can be created/updated.
- Rerun evaluation endpoint works safely.
- Summary/matrix expose evaluation data.
- Accuracy calculated according to documented formula.
- Parser/scoring and raw answers remain unchanged.
- No raw evaluator/provider data exposed.
- Task-scoped backend/frontend tests pass.
- Touched-file ruff/typecheck pass.

---

## Non-goals

- Do not implement real LLM-as-judge provider.
- Do not implement final Web5/Web6/Web7 UI.
- Do not change visibility scoring.
- Do not fix unrelated bugs.
