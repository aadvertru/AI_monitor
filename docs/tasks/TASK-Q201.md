# TASK-Q201 — Define Domain Check and PAA Query Enrichment Contract

## Goal

Define the backend/frontend contract for brand domain availability checks and People Also Ask (PAA) seed query enrichment.

This task is documentation/contract only. Do not change runtime code.

---

## Files to update/create

Preferred new file:

```text
docs/QUERY_ENRICHMENT_CONTRACT.md
```

Also update if relevant:

```text
docs/PRODUCT_SPEC.md
docs/ARCHITECTURE.md
docs/TASKS.md
```

---

## Required decisions

### 1. Domain check policy

Document:

```text
Domain check is a soft gate.
Unavailable domain blocks or warns domain-based query generation.
Unavailable domain does not block audit creation.
Unavailable domain does not block manual seed query input.
Brand description can still be used when domain is unavailable.
```

### 2. Domain check endpoint

Define:

```http
POST /brand-domain/check
```

Suggested request:

```json
{
  "domain": "example.com"
}
```

Suggested response:

```json
{
  "input": "https://example.com/path",
  "normalized_domain": "example.com",
  "status": "reachable",
  "http_status": 200,
  "checked_at": "2026-01-01T00:00:00Z",
  "query_generation_allowed": true,
  "reason": null,
  "cache_ttl_seconds": 21600
}
```

Statuses:

```text
reachable
dns_failed
http_failed
timeout
invalid_domain
blocked_private_network
unknown
```

### 3. SSRF / safety policy

Document that backend domain checks must protect against SSRF:

```text
reject localhost
reject private IP ranges
reject link-local IPs
reject loopback
reject direct IP literals unless explicitly allowed
use short timeouts
do not follow unsafe redirects to private networks
limit response body reading
```

### 4. PAA provider policy

Document provider abstraction:

```text
PeopleAlsoAskProvider
  - SerpApiPaaProvider
  - MockPaaProvider for tests
  - DataForSEO future candidate
```

Do not let frontend call SerpApi directly.

### 5. PAA generation contract

Extend seed query suggestions to support:

```json
{
  "use_paa": true,
  "language": "ru",
  "country": "ru",
  "paa_seed_query": "..."
}
```

PAA suggestions should return:

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

### 6. Deduplication

Document:

```text
deduplicate user/ai/paa suggestions by normalized text
respect max total seed query limit
do not persist suggestions before user confirmation/save
```

### 7. Language/country

Document:

```text
PAA supports language and country parameters.
UI locale is not automatically the search locale unless product decides so.
User/search settings may explicitly choose language/country.
```

---

## Acceptance criteria

- Contract for domain check is documented.
- Soft-gate policy is documented.
- SSRF/domain safety requirements are documented.
- PAA provider abstraction is documented.
- Seed query generation PAA extension is documented.
- Language/country behavior is documented.
- Deduplication/persistence rules are documented.
- No runtime code is changed.

---

## Non-goals

- Do not implement domain check.
- Do not implement PAA provider.
- Do not change seed query generation runtime.
- Do not call SerpApi.
