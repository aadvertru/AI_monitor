# AFTER-T — Testing Checklist After Source Intelligence v2

## Phase covered

Phase T — Source Intelligence v2: Domain Aggregation.

## Primary goal to verify

Sources are grouped by registrable domain, with expandable URL-level evidence, and no raw provider/source payloads exposed.

---

## Backend tests

### URL normalization

Verify:

```text
lowercase scheme/host
remove default ports
remove fragment
preserve path
remove tracking params
preserve meaningful query params
reject unsupported schemes
invalid URL safe
no network calls
```

### Registrable domain extraction

Verify:

```text
news.bbc.co.uk → bbc.co.uk
sub.example.com → example.com
www.wikipedia.org → wikipedia.org
localhost/private/IP behavior safe
```

### Aggregation service

Verify:

```text
same registrable domain grouped
different pages listed under domain
duplicate URLs deduped
source_count correct
unique_url_count correct
query_count correct
target_count correct
levels/models/providers aggregated
invalid URLs handled safely
L1 no-source audit returns empty
OpenRouter L2 no-source success returns empty
legacy source records safe
raw fields not exposed
```

### Endpoint

Verify:

```text
GET /audits/{id}/source-domains requires auth
ownership enforced
empty audit returns domains=[]
L2 sources grouped
partial audit sources grouped
OpenRouter gateway metadata included where available
no filters/query params implemented in T204 unless later task added them
unsafe fields absent
```

---

## Frontend tests

Verify:

```text
source-domain client parses empty response
domain rows render
counts render
expand/collapse works
URL evidence renders
long URLs/snippets safe
loading/error states
L1/no-source empty state
OpenRouter L2 no-citations empty state
unsafe mocked fields not rendered
external links use rel=noopener noreferrer if new tab
```

---

## Manual QA

Run:

```text
L1 audit → no-source empty state
L2 audit → domain groups visible
same domain with multiple URLs → one row
expand row → URL evidence visible
duplicate URLs not repeated
OpenRouter L2 answer without citations → safe empty state
partial audit → available sources still visible
mobile sources view smoke test
```

---

## Safety checks

Must not expose:

```text
raw provider response
raw tool results
raw annotations
raw citations payload
headers
API keys
raw prompts
```

---

## Exit criteria

Phase T is stable when:

```text
source domains group correctly
URL-level evidence is preserved
sources UI expandable
L1/no-source and OpenRouter no-citation states safe
no raw provider/tool data exposed
no undocumented filters are required
```
