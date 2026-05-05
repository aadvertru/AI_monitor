# TASK-R201 — Define Results Data Contracts v2

## Goal

Define the backend API contracts required for Web5/Web6/Web7-style results.

This task is documentation/contract only. Do not change runtime code.

The goal is to define stable DTOs before implementing summary cards, model summary, answer matrix, source-domain intelligence, concepts, competitors, and evaluation fields.

---

## Context

The current results UI is not yet shaped like the target screens.

The target UI requires:

- overall summary cards
- L1/L2 mentionability
- L1/L2 accuracy from evaluation layer
- sentiment/tone
- model-level summary table
- matrix view: questions × model/level targets
- cell-level answer excerpt, verdict, rationale, expand action
- source-domain groups
- concepts and competitor candidates

Frontend must not assemble these structures from raw results. Backend must provide matrix-ready and summary-ready DTOs.

---

## Files to update/create

Preferred new file:

```text
docs/RESULTS_V2_CONTRACT.md
```

If the project centralizes contracts elsewhere, update:

```text
docs/PRODUCT_SPEC.md
docs/ARCHITECTURE.md
docs/TASKS.md
```

---

## Required contract decisions

### 1. Summary v2 endpoint

Define either a new endpoint:

```http
GET /audits/{id}/summary-v2
```

or an additive extension to the current summary endpoint.

Recommended: new endpoint first, to avoid breaking existing UI.

### 2. Answer matrix endpoint

Define:

```http
GET /audits/{id}/answer-matrix
```

Purpose:

```text
Return rows = seed queries.
Return columns = audit targets.
Return cells = query × target result/evaluation.
```

### 3. Source domain endpoint placeholder

Define:

```http
GET /audits/{id}/source-domains
```

This endpoint may return placeholder/empty data until Phase T implements real domain aggregation.

### 4. Concepts/competitors placeholders

Define DTO fields for:

```text
concepts
competitor_candidates
```

These may be empty placeholders until Phase U.

### 5. Evaluation placeholders

Define evaluation fields as nullable until Phase S is implemented.

Example:

```json
"evaluation": null
```

or:

```json
"evaluation": {
  "verdict": "unknown",
  "rationale": null,
  "confidence": null,
  "evaluation_version": null
}
```

Choose one convention and document it.

---

## Suggested summary v2 response shape

```json
{
  "audit_id": 1,
  "status": "completed",
  "totals": {
    "query_count": 20,
    "target_count": 6,
    "run_count": 120,
    "levels": ["L1", "L2"]
  },
  "overall": {
    "mentionability_l1": {
      "percentage": 25,
      "found": 15,
      "total": 60
    },
    "mentionability_l2": {
      "percentage": 9,
      "found": 4,
      "total": 44
    },
    "accuracy_l1": null,
    "accuracy_l2": null,
    "tone": {
      "positive": 27,
      "neutral": 32,
      "negative": 7
    }
  },
  "model_summaries": [
    {
      "target_group_label": "OpenAI o3",
      "ai_family": "chatgpt",
      "model_id": "openai/o3",
      "mr_l1": 20,
      "mr_l2": 0,
      "delta_mr": -20,
      "accuracy_l1": null,
      "accuracy_l2": null,
      "delta_accuracy": null,
      "tone_l1": "neutral",
      "tone_l2": "positive"
    }
  ],
  "provider_diagnostics": []
}
```

Adapt field names to project conventions.

---

## Suggested answer matrix response shape

```json
{
  "audit_id": 1,
  "columns": [
    {
      "target_id": "t1",
      "label": "OpenAI o3 / L1",
      "ai_family": "chatgpt",
      "execution_provider": "openrouter",
      "model_provider": "openai",
      "model_id": "openai/o3",
      "level": "L1",
      "gateway": true,
      "gateway_l2_experimental": false
    }
  ],
  "rows": [
    {
      "query_id": "q1",
      "query_text": "In what year was Harmony Ballet Studio opened?",
      "query_type": "brand_direct",
      "cells": [
        {
          "target_id": "t1",
          "run_id": 123,
          "status": "completed",
          "answer_excerpt": "Harmony Ballet Studio opened in 2014...",
          "brand_mentioned": true,
          "score": 0.72,
          "evaluation": null,
          "sources_count": 0,
          "provider_error": null
        }
      ]
    }
  ]
}
```

---

## Required rules

- Backend builds matrix rows/columns/cells.
- Frontend must not calculate scores or aggregate matrix cells.
- Existing results endpoints remain backward compatible.
- Legacy audits without audit targets must still return safe results.
- Partial/failed runs must render as cells with safe statuses.
- Raw provider responses are not exposed.
- Raw prompts are not exposed.
- Provider diagnostics remain safe.

---

## Testing plan to document

Document backend tests required for future tasks:

```text
summary v2 works for no results
summary v2 works for completed audit
summary v2 works for partial audit
matrix columns match audit targets
matrix rows match seed queries
matrix cells map query × target correctly
legacy audit compatibility
OpenRouter gateway metadata appears safely
failed runs include safe provider_error
evaluation null/unknown handled
```

---

## Acceptance criteria

- `docs/RESULTS_V2_CONTRACT.md` exists or equivalent docs are updated.
- Summary v2 contract is defined.
- Answer matrix contract is defined.
- Source-domain placeholder contract is defined.
- Concepts/competitors placeholder contract is defined.
- Evaluation placeholder convention is defined.
- Backward compatibility requirements are documented.
- Testing plan is documented.
- No runtime code is changed.

---

## Non-goals

- Do not implement endpoints.
- Do not implement UI.
- Do not implement evaluation/fact-checking.
- Do not implement source domain aggregation.
- Do not implement concepts/competitors extraction.
- Do not change parser/scoring.
