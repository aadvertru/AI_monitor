# Anthropic Claude L2 Web Search Mapping

This document designs Anthropic/Claude L2 behavior before runtime implementation.
No runtime code is implemented by this document.

## Anthropic Docs Checked

Checked on: 2026-05-04

Official docs:

- `https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/web-search-tool`
- `https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview`

Observed:

- Current latest web search tool version: `web_search_20260209`.
- Previous/basic web search tool version: `web_search_20250305`.
- Server tool name: `web_search`.
- Web search is a server-side tool. The backend specifies the tool; no client-side
  implementation is required.
- Tool config may include `max_uses`, domain filters, and user location.
- Web search responses can include `server_tool_use`, `web_search_tool_result`,
  final text blocks with `citations`, and `usage.server_tool_use.web_search_requests`.
- Citation shape includes `type=web_search_result_location`, `url`, `title`,
  `encrypted_index`, and `cited_text`.
- Search result shape includes `url`, `title`, `page_age`, and `encrypted_content`.
- Tool errors may appear inside HTTP 200 responses as
  `web_search_tool_result_error`.
- Documented tool error codes include `too_many_requests`, `invalid_input`,
  `max_uses_exceeded`, `query_too_long`, and `unavailable`.

## L2 Scope

Claude L2 means Anthropic Messages API with server-side web search enabled.

Claude L2 must:

- use normalized backend-owned audit prompts
- enable web search only for SCDL L2
- normalize answer text, sources, usage, and errors
- expose only frontend-safe diagnostics and source DTOs

Claude L2 must not:

- silently downgrade to Claude L1
- fallback to OpenAI
- fallback to mock
- expose raw provider responses, raw prompts, request headers, stack traces, API
  keys, encrypted search fields, or secrets
- require parser/scoring changes

Out of scope for the first L2 implementation:

- dynamic filtering customization
- multi-turn search result reuse
- custom search result injection
- domain allow/block lists unless separately required
- user-facing cost estimates
- frontend redesign
- parser/scoring changes

## Web Search Tool Version Strategy

Use config-driven tool version:

```text
ANTHROPIC_WEB_SEARCH_TOOL_VERSION
```

Recommended initial default:

```text
web_search_20250305
```

Rationale:

- `web_search_20260209` is the latest version and adds dynamic filtering.
- Dynamic filtering requires extra design and may require code execution/tool
  support that is out of first L2 scope.
- `web_search_20250305` remains documented as available and is simpler for MVP.

Implementation rule:

- Do not hardcode a permanent tool version in adapter logic.
- Default may live in config.
- Re-check official Anthropic docs immediately before coding L2.

## Planned L2 Config Keys

```text
ANTHROPIC_API_KEY
ANTHROPIC_L2_MODEL
ANTHROPIC_WEB_SEARCH_TOOL_VERSION
ANTHROPIC_WEB_SEARCH_MAX_USES
ANTHROPIC_REQUEST_TIMEOUT_SECONDS
ANTHROPIC_MAX_OUTPUT_TOKENS
```

Notes:

- `ANTHROPIC_API_KEY` is reused from L1.
- `ANTHROPIC_L2_MODEL` should be separate from `ANTHROPIC_L1_MODEL`.
- `ANTHROPIC_WEB_SEARCH_MAX_USES` maps to the web search tool `max_uses`.
- Backend owns all tool config. Frontend must not provide Anthropic tool config.

## Request Construction

Claude L2 request shape:

```python
{
    "model": ANTHROPIC_L2_MODEL,
    "max_tokens": ANTHROPIC_MAX_OUTPUT_TOKENS,
    "messages": [{"role": "user", "content": final_audit_prompt}],
    "tools": [
        {
            "type": ANTHROPIC_WEB_SEARCH_TOOL_VERSION,
            "name": "web_search",
            "max_uses": ANTHROPIC_WEB_SEARCH_MAX_USES,
        }
    ],
}
```

Rules:

- Include `tools` only for L2.
- L1 must not include tools.
- If tool config is invalid or unavailable, return safe normalized diagnostic.
- Do not fallback to L1 or another provider.

## Answer Text Extraction

Recommended algorithm:

1. Read final assistant `content` blocks.
2. Collect text from blocks with `type == "text"`.
3. Ignore `server_tool_use` and `web_search_tool_result` blocks for answer text.
4. Join text blocks in order with newline.
5. Trim final text.
6. If no non-empty text remains, return `EMPTY_RESPONSE`.

Do not include raw tool blocks in `answer_text`.

## Source and Citation Normalization

Primary source path:

- Extract `citations` attached to final text blocks.

Fallback source path:

- If no citations exist, extract safe source rows from `web_search_tool_result`
  entries.

Deduplication:

- Deduplicate by normalized URL.
- Preserve first title/snippet encountered.

Map to `ProviderSource`:

```text
title -> title
url -> url
domain extracted from url -> domain
cited_text -> snippet
page_age -> metadata.page_age
source_type = "web"
provider_source_id -> safe provider id if available
```

Never expose:

```text
encrypted_content
encrypted_index
raw tool result objects
full raw response
```

For MVP, do not store encrypted continuation fields unless multi-turn
continuation becomes an explicit requirement.

## Usage Normalization

Use provider metadata for web-search-specific usage in the first L2
implementation.

Recommended metadata:

```json
{
  "usage": {
    "input_tokens": 100,
    "output_tokens": 50,
    "total_tokens": 150,
    "cache_read_input_tokens": 0,
    "cache_creation_input_tokens": 0,
    "server_tool_use": {
      "web_search_requests": 1
    }
  }
}
```

Reason:

- Existing `ProviderUsage` is not yet a first-class runtime DTO.
- Metadata storage already supports JSON-safe provider usage.
- This avoids schema churn for first L2 implementation.

Later, `web_search_requests` may be promoted to a typed usage field if usage or
billing becomes product-facing.

## Tool-Result Error Mapping

Anthropic web search tool errors can appear inside HTTP 200 responses. They must
not be ignored.

Map:

| Anthropic tool error | Normalized error |
|---|---|
| `too_many_requests` | `RATE_LIMIT` |
| `unavailable` | `PROVIDER_UNAVAILABLE` |
| `max_uses_exceeded` | `CONFIGURATION_ERROR` |
| `invalid_input` | `PROVIDER_REQUEST_FAILED` |
| `query_too_long` | `PROVIDER_REQUEST_FAILED` or preflight validation error |
| unknown tool error | `PROVIDER_REQUEST_FAILED` |

Decision:

- If final answer text is usable and a tool error is also present, keep the run
  successful and store a safe warning in provider metadata.
- If no usable answer text exists, return the normalized provider error.
- Warning-level diagnostics should be added later only if the API has a clear
  frontend-safe warning DTO. Do not overload error diagnostics for successful
  runs unless explicitly designed.

## Diagnostics

Claude L2 reuses Phase K provider diagnostics.

Expected normalized errors:

```text
NO_API_KEY
INVALID_API_KEY
INVALID_MODEL
CONFIGURATION_ERROR
TIMEOUT
RATE_LIMIT
PROVIDER_UNAVAILABLE
EMPTY_RESPONSE
INVALID_RESPONSE
PROVIDER_REQUEST_FAILED
UNKNOWN_PROVIDER_ERROR
```

For web-search-specific misconfiguration, use `CONFIGURATION_ERROR`.

Do not introduce Anthropic-specific frontend error types unless unavoidable.

## No Fallback

Claude L2 must not fallback to:

- Claude L1
- OpenAI L2
- mock

If web search is unavailable, disabled, or misconfigured, return safe normalized
diagnostic.

## Mocked Implementation Test Plan

Required tests for the future L2 implementation:

- Claude L2 success with citations.
- Claude L2 success without citations -> safe empty sources.
- Multiple citations deduped by URL.
- Text blocks extracted correctly.
- Tool-result entries used as fallback sources.
- Tool-result `too_many_requests` -> `RATE_LIMIT`.
- Tool-result `unavailable` -> `PROVIDER_UNAVAILABLE`.
- Tool-result `max_uses_exceeded` -> `CONFIGURATION_ERROR`.
- No answer text -> `EMPTY_RESPONSE`.
- No fallback to L1/OpenAI/mock.
- Usage metadata includes `server_tool_use.web_search_requests`.
- `encrypted_content` and `encrypted_index` are not exposed.
- No real Anthropic calls in CI.

## Manual Verification Plan

Future L2 manual scenarios:

- Claude L2 one-click audit with one query.
- Sources/citations render.
- Safe empty sources state if citations absent.
- Missing API key.
- Invalid model/config.
- Web search misconfiguration.
- Provider timeout/forced failure.
- Caps/guardrails.
- No raw response/prompt/header/key/secret leakage.

