# TASK-U201 — Define Concepts and Competitors Split Contract

## Goal

Define the contract for separating descriptive concepts/phrases from real competitor candidates.

This task is documentation/contract only. Do not change runtime code.

---

## Context

The current Results Details section labels extracted items as “Competitors”, but many of them are actually:

```text
concepts
phrases
descriptive entities
category terms
```

These are useful and should be preserved, but they must not be mislabeled as competitors.

---

## File to create

```text
docs/CONCEPTS_COMPETITORS_CONTRACT.md
```

---

## Required definitions

### Concept / Phrase

Document:

```text
A concept is a descriptive term, phrase, category, capability, product type, location, or theme used in answers about the brand.
A concept is not necessarily a company or competitor.
```

Examples:

```text
SEO automation
children's ballet classes
dance studio
web search visibility
Moscow locations
```

### CompetitorCandidate

Document:

```text
A competitor candidate is a brand-like organization/product/entity that appears with evidence suggesting it competes with the audited brand.
```

Competitor signals:

```text
appears in comparison context
appears as alternative
appears in “best X” category list alongside audited brand
has brand-like capitalization/entity pattern
has domain or known brand signal
matches user-provided competitor list if available
```

Generic phrases must not be marked as competitors.

---

## DTOs

### Concept DTO

```json
{
  "id": "c1",
  "text": "children's ballet classes",
  "type": "concept",
  "category": "service",
  "count": 5,
  "evidence_count": 5,
  "evidence": []
}
```

### CompetitorCandidate DTO

```json
{
  "id": "cc1",
  "name": "Another Ballet Studio",
  "domain": "example.com",
  "confidence": 0.82,
  "evidence_type": "comparison_context",
  "evidence_count": 3,
  "evidence": [
    {
      "query_id": "q1",
      "run_id": 123,
      "target_id": "t1",
      "answer_excerpt": "...",
      "level": "L1",
      "model_id": "openai/gpt-4o-mini"
    }
  ]
}
```

---

## Extraction strategy

Initial strategy should be hybrid deterministic:

```text
current extracted “competitors” become concepts/phrases
competitor candidates require brand-like signal + competitive context
do not use LLM classifier inside parser/scoring for first version
store evidence and confidence
```

---

## Backward compatibility

Document:

```text
legacy competitors field may remain temporarily
new fields are concepts and competitor_candidates
UI should stop labeling generic phrases as competitors
```

---

## Testing plan

Document tests:

```text
generic phrase classified as concept
brand-like alternative classified as competitor candidate
known competitor list match boosts confidence
comparison context creates evidence
no evidence means no competitor candidate
legacy data handled safely
```

---

## Acceptance criteria

- Contract doc exists.
- Concept definition documented.
- CompetitorCandidate definition documented.
- DTOs documented.
- Evidence/confidence requirements documented.
- Backward compatibility documented.
- Testing plan documented.
- No runtime code changed.

---

## Non-goals

- Do not implement extraction.
- Do not change parser/scoring.
- Do not change UI.
