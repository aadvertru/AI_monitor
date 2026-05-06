# Source Intelligence v2 Contract

Source Intelligence v2 groups URL-level citations into domain-level source rows while preserving the evidence needed to inspect each concrete source.

## Goals

- Replace flat source URL lists with registrable-domain groups.
- Keep backend as the source of truth for grouping and counts.
- Preserve concrete URL evidence for expandable UI rows.
- Keep L1 and no-citation audits safe and understandable.

## Non-Goals

- No URL crawling or availability checks.
- No provider adapter redesign.
- No parser, scoring, or answer-evaluation changes.
- No exposure of raw provider payloads, tool outputs, annotations, headers, or secrets.

## Grouping Rule

Sources must be grouped by registrable domain, not raw hostname.

Examples:

| Input host | Group domain |
|---|---|
| `news.bbc.co.uk` | `bbc.co.uk` |
| `sub.example.com` | `example.com` |
| `www.wikipedia.org` | `wikipedia.org` |
| `m.example.com` | `example.com` |

Use a Public Suffix List compatible library where available. If a fallback extractor is used locally, it must be safe, deterministic, and documented as less accurate for multi-part public suffixes.

## Endpoint

Preferred endpoint:

```http
GET /audits/{id}/source-domains
```

The endpoint requires authentication and audit ownership, following existing audit read endpoint rules. It returns a safe empty state for audits with no citations.

## Response Shape

Field naming follows existing backend DTO conventions.

```json
{
  "audit_id": 42,
  "domains": [
    {
      "domain": "wikipedia.org",
      "source_count": 10,
      "unique_url_count": 7,
      "query_count": 4,
      "target_count": 3,
      "levels": ["L2"],
      "models": ["openai/gpt-4o-mini", "anthropic/claude-3.5-sonnet"],
      "providers": ["openrouter"],
      "urls": [
        {
          "url": "https://www.wikipedia.org/wiki/Example",
          "normalized_url": "https://www.wikipedia.org/wiki/Example",
          "title": "Example - Wikipedia",
          "snippet": "Short cited evidence text.",
          "query_id": "q1",
          "query_text": "What programs does Harmony Ballet Studio offer?",
          "target_id": "t1",
          "model_id": "openai/gpt-4o-mini",
          "model_provider": "openai",
          "execution_provider": "openrouter",
          "level": "L2",
          "source_type": "web",
          "gateway": true,
          "gateway_l2_experimental": true
        }
      ]
    }
  ],
  "warnings": []
}
```

## DTO Semantics

`domain`: registrable domain used for grouping.

`source_count`: number of source evidence items contributing to the group before URL deduplication.

`unique_url_count`: number of distinct normalized URLs in the group.

`query_count`: number of distinct queries represented by the group.

`target_count`: number of distinct audit targets represented by the group.

`levels`: distinct SCDL levels represented by the group.

`models`: distinct model IDs represented by the group.

`providers`: distinct execution providers represented by the group.

`urls`: URL-level evidence items suitable for expanding a domain row.

## URL Normalization

Normalize source URLs before grouping and deduplication:

- Trim surrounding whitespace.
- Parse safely without network calls.
- Accept only `http` and `https`.
- Lowercase scheme and host.
- Remove default ports: `:80` for HTTP, `:443` for HTTPS.
- Remove fragments.
- Normalize trailing slash consistently.
- Preserve path and meaningful query parameters.
- Remove common tracking parameters:
  - `utm_source`
  - `utm_medium`
  - `utm_campaign`
  - `utm_term`
  - `utm_content`
  - `fbclid`
  - `gclid`
  - `yclid`

Do not over-normalize in a way that merges different real pages incorrectly.

## Evidence Preservation

Domain grouping must not discard concrete URL evidence. Each URL evidence item should preserve:

- Original display URL.
- Normalized URL.
- Title when available.
- Snippet or cited text when available.
- Query ID and query text when available.
- Target ID when available.
- Model ID and model provider when available.
- Execution provider when available.
- SCDL level.
- Source type.
- Gateway metadata when available.

## L1 Behavior

L1 normally has no web sources. L1 audits should return `domains=[]` unless source records unexpectedly exist. Unexpected source records must still be normalized and rendered safely rather than crashing.

## OpenRouter L2 Behavior

OpenRouter L2 sources are best-effort gateway sources. They may be absent even when answer text exists. Missing citations for OpenRouter L2 must produce a safe empty state, not a failed source view.

When available, OpenRouter L2 source rows should preserve gateway metadata such as `gateway=true` and `gateway_l2_experimental=true`.

## Safety

The source-domains contract must not expose:

- Raw provider responses.
- Raw tool results.
- Raw annotations.
- Raw prompts.
- Request headers.
- API keys or secrets.
- Stack traces.

URLs must be sanitized before display. Frontend external links must use safe attributes such as `rel="noopener noreferrer"` when opened in a new tab.

## Testing Plan

Backend tests should cover:

- Registrable domain extraction.
- URL normalization.
- Tracking parameter removal.
- Same-domain grouping.
- Subdomain grouping by registrable domain.
- Duplicate URL deduplication.
- Query, target, level, model, and provider counts.
- Invalid URLs handled safely.
- L1 empty state.
- OpenRouter L2 missing sources safe state.
- Legacy source records.
- Unsafe raw fields excluded.

Frontend tests should cover:

- Domain rows render.
- Expand/collapse works.
- URL evidence renders.
- Counts render correctly.
- Empty, loading, and error states render.
- Long URLs and snippets render safely.
- Unsafe raw fields are not rendered.
