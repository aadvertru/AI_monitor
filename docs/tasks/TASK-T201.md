# TASK-T201 — Define Source Intelligence v2 Contract

## Goal

Define the Source Intelligence v2 contract for domain-level source aggregation.

This task is documentation/contract only. Do not change runtime code.

The goal is to replace a flat source URL list with domain-level source intelligence:

```text
domain row
  → expandable list of concrete URLs/citations/evidence
```

---

## Context

The current sources view can show many rows from the same website/domain, for example:

```text
wikipedia.org/page-1
wikipedia.org/page-2
wikipedia.org/page-3
```

The new behavior should group them into one domain row:

```text
wikipedia.org
  - page-1
  - page-2
  - page-3
```

This grouping must be done by backend, not frontend.

---

## Files to update/create

Preferred new file:

```text
docs/SOURCE_INTELLIGENCE_V2_CONTRACT.md
```

If the project centralizes contracts elsewhere, update:

```text
docs/PRODUCT_SPEC.md
docs/ARCHITECTURE.md
docs/TASKS.md
```

---

## Required decisions

### 1. Grouping level

Document:

```text
Sources must be grouped by registrable domain, not raw hostname.
```

Examples:

```text
news.bbc.co.uk        → bbc.co.uk
sub.example.com       → example.com
www.wikipedia.org     → wikipedia.org
m.example.com         → example.com
```

Use a Public Suffix List compatible library if available.

### 2. SourceDomainGroup DTO

Define a DTO equivalent to:

```json
{
  "domain": "wikipedia.org",
  "source_count": 10,
  "unique_url_count": 7,
  "query_count": 4,
  "target_count": 3,
  "levels": ["L2"],
  "models": ["openai/gpt-4o-mini", "anthropic/claude-..."],
  "providers": ["openai", "openrouter"],
  "urls": [
    {
      "url": "https://wikipedia.org/...",
      "normalized_url": "https://wikipedia.org/...",
      "title": "...",
      "snippet": "...",
      "query_id": "q1",
      "query_text": "What programs does Harmony Ballet Studio offer?",
      "target_id": "t1",
      "model_id": "openai/gpt-4o-mini",
      "model_provider": "openai",
      "execution_provider": "openrouter",
      "level": "L2",
      "source_type": "web"
    }
  ]
}
```

Adapt field names to project conventions.

### 3. URL normalization rules

Document:

```text
trim URL
lowercase scheme/host
remove default ports
remove fragments
normalize trailing slash consistently
optionally remove common tracking parameters
preserve path and meaningful query params unless product decides otherwise
```

Tracking parameters that may be removed:

```text
utm_source
utm_medium
utm_campaign
utm_term
utm_content
fbclid
gclid
```

Do not over-normalize in a way that merges different real pages incorrectly.

### 4. Evidence preservation

Grouped domain rows must preserve URL-level evidence:

```text
concrete URL
title
snippet/cited_text
query
model/target
level
provider
source type
```

### 5. L1 behavior

Document:

```text
L1 normally has no sources.
L1 audits should return empty source domain groups or safe no-source state.
```

### 6. OpenRouter L2 behavior

Document:

```text
OpenRouter L2 sources are best-effort gateway sources.
They may be absent even when answer text exists.
OpenRouter L2 source rows should include gateway metadata where available.
```

### 7. Safety

Document:

```text
Do not expose raw provider response.
Do not expose raw tool results.
Do not expose raw annotations.
Do not expose API keys/secrets/headers.
URLs must be sanitized before display.
```

---

## Suggested endpoint

Preferred:

```http
GET /audits/{id}/source-domains
```

This may replace or extend the placeholder from Results v2.

---

## Testing plan to document

Backend:

```text
registrable domain extraction
URL normalization
tracking parameter removal
same domain grouped
different subdomains grouped by registrable domain
invalid URLs handled safely
duplicate URLs deduplicated
URL-level evidence preserved
L1 returns empty state
OpenRouter L2 missing sources safe
legacy sources compatible
```

Frontend:

```text
domain rows render
expand/collapse works
URL list renders
counts correct
filters by model/level/query work if implemented
safe empty state works
long URLs truncate safely
```

---

## Acceptance criteria

- Source Intelligence v2 contract is documented.
- Registrable-domain grouping is specified.
- URL normalization rules are specified.
- SourceDomainGroup DTO is defined.
- URL-level evidence preservation is defined.
- L1 and OpenRouter L2 edge cases are documented.
- Safety rules are documented.
- Testing plan is documented.
- No runtime code is changed.

---

## Non-goals

- Do not implement URL normalization.
- Do not implement source aggregation.
- Do not implement frontend UI.
- Do not change provider adapters.
- Do not change parser/scoring.
