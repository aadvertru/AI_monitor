# TASK-U210 — Verify and Stabilize Concepts and Competitors Split

## Goal

Run the Concepts/Competitors verification checklist and fix only issues captured during verification.

This task closes Phase U.

---

## Required input

Read:

```text
docs/CONCEPTS_COMPETITORS_CONTRACT.md
docs/CONCEPTS_COMPETITORS_VERIFICATION.md
```

Use captured issues from verification.

---

## Scope

Allowed fixes:

```text
concept persistence bugs
competitor candidate extraction bugs
evidence/confidence bugs
API serialization bugs
legacy compatibility bugs
Results Details UI label bugs
empty state bugs
safety/no raw data bugs
```

Not allowed:

```text
LLM classifier
parser/scoring redesign
full results UI redesign
evaluation changes
source aggregation changes
unrelated legacy fixes
```

---

## Verification expectations

Run scenarios:

```text
U-S01 through U-S10
```

Every non-pass scenario must have captured issue.

---

## Tests to add/update

Add task-scoped tests based on actual issues.

Likely tests:

```text
generic phrase -> concept
generic phrase not competitor
comparison context -> competitor candidate
evidence captured
confidence calculated
legacy competitors compatibility
UI sections render correct data
raw provider payload not exposed
```

---

## Acceptance criteria

- Verification document updated with final results.
- Blocker/major issues fixed or deferred with rationale.
- Concepts and competitors are semantically separated.
- Results Details no longer mislabels generic phrases as competitors.
- Competitor candidates require evidence/confidence.
- Legacy audits safe.
- No raw provider responses/prompts/secrets exposed.
- Task-scoped backend/frontend tests pass.
- Touched-file ruff/typecheck pass.

---

## Non-goals

- Do not add LLM classifier.
- Do not change visibility scoring.
- Do not redesign entire results page.
- Do not fix unrelated bugs.
