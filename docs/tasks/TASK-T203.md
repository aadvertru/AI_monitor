# TASK-T203 — Add Source Domain Aggregation Service

## Goal

Add a backend service that groups normalized sources by registrable domain and preserves URL-level evidence.

This service should consume existing normalized source/citation data and produce SourceDomainGroup DTOs.

---

## Scope

Implement:

```text
source domain aggregation service
domain-level grouping
URL-level evidence list
counts by domain
model/level/provider metadata
task-scoped backend tests
```

Do not implement frontend UI in this task.

---

## Input

Use existing source/citation records from provider runs/results.

The service should handle records with fields such as:

```text
url
title
snippet
source_type
query_id
target_id/run_id
model_id
execution_provider
level
```

Adapt to actual project models.

---

## Output

Return SourceDomainGroup DTOs equivalent to:

```json
{
  "domain": "wikipedia.org",
  "source_count": 10,
  "unique_url_count": 7,
  "query_count": 4,
  "target_count": 3,
  "levels": ["L2"],
  "models": ["openai/gpt-4o-mini"],
  "providers": ["openrouter"],
  "urls": [
    {
      "url": "https://wikipedia.org/...",
      "normalized_url": "https://wikipedia.org/...",
      "title": "...",
      "snippet": "...",
      "query_id": "q1",
      "target_id": "t1",
      "model_id": "openai/gpt-4o-mini",
      "execution_provider": "openrouter",
      "level": "L2",
      "source_type": "web"
    }
  ]
}
```

---

## Rules

### Grouping

- Group by registrable domain.
- Deduplicate URLs by normalized URL.
- Preserve all evidence needed to expand domain row.
- Sort domains by source_count or unique_url_count descending.
- Sort URLs within a domain deterministically.

### Missing/invalid URLs

- Invalid URLs should be skipped or grouped under a safe `unknown` bucket according to contract.
- Recommended: skip invalid URLs and count them in warnings/diagnostics if easy.
- Do not crash aggregation.

### L1 behavior

- L1-only audits should return empty groups unless sources exist unexpectedly.
- Unexpected sources should still be normalized safely.

### OpenRouter L2 behavior

- If answer has no sources, return empty groups.
- Do not treat missing sources as failure.

---

## Safety

Do not expose:

```text
raw provider response
raw tool results
raw annotations
request headers
API keys
raw prompts
```

Only expose normalized safe source fields.

---

## Tests

Backend tests:

```text
same registrable domain grouped
different pages under same domain listed
duplicate URL counted once in unique_url_count
source_count counts citations/evidence according to chosen convention
query_count correct
target_count correct
levels/models/providers aggregated
invalid URL handled safely
L1 no-source audit returns empty list
OpenRouter L2 no-source success returns empty list
legacy source records handled
unsafe raw fields not exposed
```

---

## Acceptance criteria

- Source domain aggregation service exists.
- Sources grouped by registrable domain.
- URL-level evidence preserved.
- Counts are calculated correctly.
- Invalid/missing URLs handled safely.
- L1/no-source audits return safe empty state.
- No raw provider/source payload exposed.
- Task-scoped backend tests pass.
- Touched-file ruff passes.

---

## Non-goals

- Do not implement frontend UI.
- Do not change provider adapters.
- Do not crawl/fetch source URLs.
- Do not change parser/scoring.
- Do not fix unrelated legacy failures.
