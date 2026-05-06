# Query Enrichment Contract

This document defines the contract for brand domain availability checks and
People Also Ask (PAA) seed query enrichment.

## Scope

Query enrichment helps users create better seed query lists before saving an
audit. Enrichment output is always a suggestion until the user confirms and
saves the final seed query list.

## Domain Check Policy

Domain checks are a soft gate.

- An unavailable domain may block or warn only domain-based query generation.
- An unavailable domain does not block audit creation.
- An unavailable domain does not block manual seed query input.
- Brand description based generation may still run when the domain is
  unavailable.
- Domain status is advisory and must not be treated as DNS ownership proof.

## Domain Check Endpoint

```http
POST /brand-domain/check
```

The endpoint requires authentication. It checks whether a normalized domain is
safe to request and reachable enough for domain-based query generation.

Request:

```json
{
  "domain": "https://example.com/path"
}
```

Response:

```json
{
  "input": "https://example.com/path",
  "normalized_domain": "example.com",
  "status": "reachable",
  "http_status": 200,
  "checked_at": "2026-01-01T00:00:00Z",
  "query_generation_allowed": true,
  "reason": null,
  "cache_ttl_seconds": 86400
}
```

Statuses:

- `reachable`
- `dns_failed`
- `http_failed`
- `timeout`
- `invalid_domain`
- `blocked_private_network`
- `unknown`

`query_generation_allowed` is true only when `status = reachable`.

## Domain Normalization

Backend normalization is the source of truth.

- Trim whitespace.
- Lowercase host names.
- Accept plain domains and URL-like input.
- Remove protocol, path, query string, fragment, and trailing slash.
- Reject empty values, malformed domains, unsupported schemes, localhost, and
  IP literals unless a future task explicitly allows IP literals.

## SSRF Safety

Domain checks must protect against SSRF.

The backend must reject or block:

- `localhost`
- loopback ranges, including `127.0.0.0/8` and `::1`
- private ranges, including `10.0.0.0/8`, `172.16.0.0/12`,
  `192.168.0.0/16`, and `fc00::/7`
- link-local ranges, including `169.254.0.0/16` and `fe80::/10`
- direct IP literals unless explicitly allowed
- redirects to private, loopback, or link-local addresses

Implementation requirements:

- Use short DNS and HTTP timeouts.
- Limit redirects.
- Re-check redirected hosts before following them.
- Do not read large response bodies.
- Do not return raw HTML, response bodies, request headers, stack traces, or
  internal network details.

## PAA Provider Policy

Frontend must never call PAA/search providers directly. All PAA access goes
through backend providers behind this abstraction:

```text
PeopleAlsoAskProvider
  - MockPaaProvider for tests/dev
  - SerpApiPaaProvider
  - DataForSEO provider as a future candidate
```

Provider implementations must not expose provider API keys, raw request payloads,
raw responses, or stack traces to API clients.

## Seed Query Generation Extension

Seed query generation may request PAA suggestions.

Request extension:

```json
{
  "use_domain": true,
  "use_description": true,
  "use_paa": true,
  "language": "ru",
  "country": "ru",
  "paa_seed_query": "studio ballet harmony classes",
  "existing_queries": []
}
```

Response suggestion:

```json
{
  "text": "Какие программы предлагает студия балета Гармония?",
  "source": "paa",
  "type": "problem_solution",
  "metadata": {
    "paa_provider": "serpapi"
  }
}
```

Accepted seed query sources include:

- `user`
- `ai`
- `paa`

## Deduplication And Persistence

- Deduplicate user, AI, and PAA suggestions by normalized text.
- Deduplicate within one generation response and against existing query rows.
- Respect the maximum total seed query limit.
- Do not persist suggestions before user confirmation/save.
- If the user edits a PAA suggestion, `source` remains `paa` because it records
  provenance.

## Language And Country

PAA supports language and country parameters.

- UI locale is not automatically the search locale.
- Search language/country come from explicit audit/query generation settings.
- If omitted, the backend may use provider defaults.
- Returned metadata may include normalized language/country and provider name.

## Disabled Or Missing-Key Behavior

If PAA is requested but unavailable:

- PAA disabled returns HTTP 200 with safe warning and no PAA suggestions.
- Missing provider key returns HTTP 200 with safe warning and no PAA suggestions.
- If other generation modes are enabled, they may still return suggestions.
- If only PAA is requested, response is `suggestions=[]` plus warning.

Warnings must be safe and must not expose raw provider errors or API keys.
