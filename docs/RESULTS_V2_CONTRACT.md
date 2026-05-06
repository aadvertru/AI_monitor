# Results Data Contracts v2

Results v2 defines backend-owned DTOs for the next summary and matrix UI. The frontend must render these DTOs as provided and must not reconstruct scores, matrix cells, model summaries, source-domain groups, concepts, or competitor candidates from raw runs.

Existing results and summary endpoints remain backward compatible.

## Endpoints

### `GET /audits/{id}/summary-v2`

Returns summary-ready data for the Web5-style results overview.

Response shape:

```json
{
  "audit_id": 1,
  "status": "completed",
  "totals": {
    "query_count": 20,
    "target_count": 6,
    "run_count": 120,
    "completed_runs": 116,
    "failed_runs": 4,
    "partial_runs": 0,
    "levels": ["L1", "L2"]
  },
  "overall": {
    "mentionability_l1": { "percentage": 25, "found": 15, "total": 60 },
    "mentionability_l2": { "percentage": 9, "found": 4, "total": 44 },
    "accuracy_l1": null,
    "accuracy_l2": null,
    "tone": { "positive": 0, "neutral": 0, "negative": 0, "unknown": 116 }
  },
  "model_summaries": [
    {
      "target_group_label": "OpenAI o3",
      "ai_family": "chatgpt",
      "execution_provider": "openrouter",
      "model_provider": "openai",
      "model_id": "openai/o3",
      "mr_l1": 20,
      "mr_l2": null,
      "delta_mr": null,
      "accuracy_l1": null,
      "accuracy_l2": null,
      "delta_accuracy": null,
      "tone_l1": "unknown",
      "tone_l2": null,
      "concepts": [],
      "competitor_candidates": []
    }
  ],
  "concepts": [],
  "competitor_candidates": [],
  "provider_diagnostics": []
}
```

Metric rules:

- Mentionability is computed backend-side from processed parser/scoring data: `found / total`, where `found` is the count of processed runs with brand visibility and `total` is the count of processed runs for that level or model/level group.
- `percentage` is nullable when `total = 0`.
- `accuracy_l1`, `accuracy_l2`, and `delta_accuracy` are nullable until Phase S evaluation exists. Do not infer accuracy from visibility score.
- Tone may be `positive`, `neutral`, `negative`, or `unknown`; if no tone layer exists, return `unknown` counts and nullable per-level tone labels.
- Missing L1 or L2 data uses `null`, not `"N/A"`, in API DTOs.

### `GET /audits/{id}/answer-matrix`

Returns matrix-ready data for Web6/Web7-style results.

Response shape:

```json
{
  "audit_id": 1,
  "columns": [
    {
      "target_id": "1",
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
      "query_id": "1",
      "query_text": "In what year was Harmony Ballet Studio opened?",
      "query_type": "brand_direct",
      "cells": [
        {
          "target_id": "1",
          "run_id": 123,
          "status": "completed",
          "answer_excerpt": "Harmony Ballet Studio opened in 2014...",
          "brand_mentioned": true,
          "score": 0.72,
          "evaluation": null,
          "sources_count": 0,
          "provider_error": null,
          "concepts": [],
          "competitor_candidates": []
        }
      ]
    }
  ],
  "provider_diagnostics": []
}
```

Cell statuses:

- `completed`: run completed and parsed/scored data is available.
- `failed`: run completed with provider or processing error.
- `partial`: run has some usable data but incomplete processing.
- `not_run`: expected query-target cell has no run yet.
- `processing`: run exists but is still pending/running.
- `missing`: data is inconsistent or unavailable but should not crash the client.

Answer excerpts are backend-generated and capped at 500 characters. Raw provider responses, raw prompts, request headers, and secrets must never be returned.

`evaluation` is `null` until Phase S. Phase S may replace `null` with:

```json
{
  "verdict": "unknown",
  "rationale": null,
  "confidence": null,
  "evaluation_version": null
}
```

### `GET /audits/{id}/source-domains`

Returns a strict placeholder until Phase T implements real source-domain aggregation.

Response shape:

```json
{
  "audit_id": 1,
  "domains": [],
  "warnings": []
}
```

No grouping, hostname extraction, or source intelligence calculation is implemented in Phase R.

## Concept and Competitor Placeholders

Concepts are descriptive terms or phrases found in answers.

```json
{
  "text": "SEO automation",
  "type": "concept",
  "count": 5,
  "evidence_count": 5
}
```

Competitor candidates are brand-like entities with evidence suggesting a competitive relationship.

```json
{
  "name": "Ahrefs",
  "domain": "ahrefs.com",
  "confidence": 0.82,
  "evidence_type": "comparison_context",
  "evidence_count": 3
}
```

Phase R returns empty arrays for `concepts` and `competitor_candidates`. Generic phrases must not be reclassified as competitors in this phase.

## Backward Compatibility

- Existing `/audits/{id}/summary`, `/audits/{id}/results`, and `/audits/{id}/sources` behavior remains unchanged.
- Legacy audits without `audit_targets` must produce safe fallback columns based on existing provider/level data.
- Old `seed_queries` and new `seed_query_items` must both work.
- Partial, failed, missing, and not-yet-run cells must return safe placeholders.
- Provider diagnostics remain normalized and secret-free.

## Safety Rules

Do not expose:

- raw provider responses
- raw prompts
- request headers
- API keys or secrets
- stack traces
- raw source/provider payloads

## Future Test Plan

Backend tests should cover:

- summary v2 for no results, completed audits, and partial audits
- summary v2 auth and ownership
- mentionability L1/L2 calculation
- model summaries grouped by model and level
- accuracy fields remain null before Phase S
- answer matrix columns match audit targets
- answer matrix rows match seed queries
- cells map query to target correctly
- completed cells include capped answer excerpts
- failed cells include safe provider errors
- missing/not-run cells are safe
- legacy audit compatibility
- OpenRouter gateway metadata appears safely
- source domains return strict empty placeholder
- concepts and competitor candidates return safe empty arrays
- no raw provider payloads are exposed
