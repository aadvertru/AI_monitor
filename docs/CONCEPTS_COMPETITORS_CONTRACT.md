# Concepts and Competitor Candidates Contract

This contract separates descriptive concepts/phrases from real competitor candidates.

## Goal

Audit answers often contain useful extracted terms that are not companies or competitive alternatives. These should remain visible as concepts, while competitor candidates must require conservative evidence.

## Definitions

### Concept / Phrase

A concept is a descriptive term, phrase, category, capability, product type, location, or theme used in answers about the audited brand.

A concept is not necessarily a company, product, or competitor.

Examples:

- SEO automation
- children's ballet classes
- dance studio
- web search visibility
- Moscow locations

### CompetitorCandidate

A competitor candidate is a brand-like organization, product, or entity that appears with evidence suggesting it competes with the audited brand.

Competitor candidates require both:

- A competitive context.
- A brand-like signal.

Generic phrases must not be marked as competitors.

## Competitive Signals

Supported initial signals include:

- Appears in comparison context.
- Appears as an alternative.
- Appears in a "best X" or "top X" category list alongside the audited brand.
- Has brand-like capitalization/entity pattern.
- Has a domain or known brand signal.
- Matches a user-provided competitor list if available.

## DTOs

### Concept

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

### CompetitorCandidate

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
      "model_id": "openai/gpt-4o-mini",
      "execution_provider": "openrouter"
    }
  ]
}
```

## Evidence

Evidence must be safe and summarized. It may include:

- Query ID.
- Run ID.
- Target ID.
- Short answer excerpt.
- Matched phrase.
- Evidence type.
- SCDL level.
- Model ID.
- Execution provider.
- Language or pattern family.

Evidence must not include raw provider responses, raw prompts, headers, API keys, stack traces, or full tool payloads.

## Initial Extraction Strategy

The initial strategy is hybrid deterministic:

- Current extracted legacy `competitors` become concepts/phrases.
- Competitor candidates require brand-like signal plus competitive context.
- No LLM classifier is used inside parser/scoring for the first version.
- Evidence and confidence are stored for competitor candidates.

## Confidence

The first deterministic confidence model should be simple and auditable:

- `0.9`: known competitor list match with comparison context.
- `0.8`: domain signal with comparison context.
- `0.7`: brand-like name with comparison context.
- `0.5`: brand-like name in weak category list context.

Default threshold: `confidence >= 0.6`.

Candidates below threshold are discarded.

## Backward Compatibility

Legacy `competitors` fields may remain temporarily for older frontend surfaces and fixtures.

New canonical fields:

- `concepts`
- `competitor_candidates`

Frontend should stop labeling generic legacy phrases as competitors. If only legacy data exists, it should be displayed under Concepts rather than Competitor Candidates.

## Testing Plan

Backend tests should cover:

- Generic phrase classified as concept.
- Generic phrase not classified as competitor.
- Brand-like alternative classified as competitor candidate.
- English comparison context creates competitor evidence.
- Russian comparison/alternative context creates competitor evidence.
- Known competitor list match boosts confidence.
- No evidence means no competitor candidate.
- Confidence threshold filters weak candidates.
- Legacy data handled safely.
- Raw provider payloads are not exposed.

Frontend tests should cover:

- Concepts section renders generic phrases.
- Competitor Candidates section renders real candidates.
- Generic phrases do not appear under competitors.
- Empty states render.
- Legacy competitors fallback appears under Concepts.
- Unsafe fields are not rendered.

## Non-Goals

- No LLM classifier in this phase.
- No parser/scoring redesign.
- No removal of legacy fields yet.
- No full results UI redesign.
