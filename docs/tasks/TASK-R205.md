# TASK-R205 — Add Concepts and Competitor Placeholder DTOs

## Goal

Add placeholder DTO fields/endpoints for concepts and competitor candidates in results v2 contracts.

This task prepares contracts for Phase U but does not implement the full extraction logic.

---

## Scope

Implement:

```text
Concept DTO
CompetitorCandidate DTO
placeholder fields in summary/matrix/detail responses where appropriate
safe empty states
task-scoped backend tests
```

Do not implement full competitor extraction in this task.

---

## Required DTOs

### Concept

```json
{
  "text": "SEO automation",
  "type": "concept",
  "count": 5,
  "evidence_count": 5
}
```

### CompetitorCandidate

```json
{
  "name": "Ahrefs",
  "domain": "ahrefs.com",
  "confidence": 0.82,
  "evidence_type": "comparison_context",
  "evidence_count": 3
}
```

For this task, these may be empty arrays.

---

## Required semantic distinction

Document or encode:

```text
concepts/phrases are descriptive terms found in answers
competitor_candidates are brand-like entities with evidence suggesting competitive relationship
```

Do not label generic phrases as competitors.

If current UI/API currently exposes misleading `competitors`, keep backward compatibility but add new fields:

```text
concepts
competitor_candidates
```

---

## Tests

Backend tests:

```text
summary/matrix/detail returns concepts field
summary/matrix/detail returns competitor_candidates field
empty arrays safe
legacy competitors field not broken if still used
no generic phrase is reclassified in this task
no raw answer payload exposed
```

---

## Acceptance criteria

- Concept DTO exists.
- CompetitorCandidate DTO exists.
- Results v2 responses can include concepts and competitor_candidates.
- Empty states are safe.
- Existing legacy competitor field remains backward compatible if present.
- No extraction logic is implemented beyond placeholder/minimal mapping.
- Task-scoped backend tests pass.
- Touched-file ruff passes.

---

## Non-goals

- Do not implement competitor extraction.
- Do not rename UI labels yet unless required for contract.
- Do not change parser/scoring.
- Do not run LLM classifier.
- Do not fix unrelated legacy failures.
