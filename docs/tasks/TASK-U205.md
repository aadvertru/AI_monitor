# TASK-U205 — Persist Concepts and Competitor Candidates During Post-Processing

## Goal

Persist concepts and competitor candidates as part of audit result post-processing.

This should use the concept mapping and competitor candidate extractor implemented in previous tasks.

---

## Scope

Implement:

```text
post-processing integration
concept persistence
competitor candidate persistence
deduplication
evidence linking
task-scoped backend tests
```

---

## Rules

### Concepts

- Persist concept/phrase records from current extractor output.
- Deduplicate by normalized text per audit.
- Increment counts/evidence counts where appropriate.
- Preserve evidence where feasible.

### Competitor candidates

- Run deterministic competitor candidate extractor on normalized answer text.
- Persist candidates with confidence/evidence.
- Deduplicate by normalized name/domain per audit.
- Merge evidence across runs.

### Idempotency

Post-processing may be rerun.

It must not create duplicate concepts/candidates endlessly.

Use upsert/replace strategy according to project convention.

---

## Tests

Backend tests:

```text
successful post-processing creates concepts
successful post-processing creates competitor candidate when evidence exists
rerun post-processing is idempotent
concept counts update correctly
competitor evidence merges
generic phrases remain concepts
failed/no-answer runs skipped
legacy audits safe
```

---

## Acceptance criteria

- Concepts persisted during post-processing.
- Competitor candidates persisted when deterministic evidence exists.
- Idempotency handled.
- Failed/no-answer runs skipped safely.
- Parser/scoring behavior unchanged.
- Task-scoped backend tests pass.
- Touched-file ruff passes.

---

## Non-goals

- Do not update frontend UI.
- Do not use LLM classifier.
- Do not change visibility scoring.
- Do not re-run provider calls.
