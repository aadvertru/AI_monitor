# AFTER-Q — Testing Checklist After Domain Check + PAA Query Enrichment

## Phase covered

Phase Q — Domain Check + People Also Ask Query Enrichment.

## Primary goal to verify

The system can check brand domain availability safely and enrich seed query suggestions with PAA questions, while preserving manual query input and user confirmation.

---

## Backend tests

### Domain check

Verify:

```text
POST /brand-domain/check requires auth
unauthenticated request rejected
valid reachable domain returns reachable
invalid domain returns invalid_domain
DNS failure handled
HTTP failure handled
timeout handled
domain normalization works
cache TTL is 86400 seconds
cache hit avoids repeated network check
result includes query_generation_allowed
query_generation_allowed=true only for status=reachable
query_generation_allowed=false for dns_failed/http_failed/timeout/invalid_domain/blocked_private_network/unknown
raw HTML/body not returned
```

### SSRF safety

Verify blocked:

```text
localhost
127.0.0.0/8
10.0.0.0/8
172.16.0.0/12
192.168.0.0/16
169.254.0.0/16
::1
fc00::/7
fe80::/10
direct IP literals unless explicitly allowed
redirect to private network if redirects are followed
```

### PAA provider

Verify:

```text
PAA provider interface exists
mock PAA provider deterministic
SerpApi adapter mocked in tests
no real SerpApi calls in CI
missing SerpApi key safe
timeout safe
rate limit/quota safe
invalid response safe
language/country passed through
limit respected
```

### Seed query schema

Verify:

```text
seed query source enum/DTO accepts source=paa
seed query source enum/DTO rejects unknown source
source values user/ai/paa remain valid
```

### Seed query generation with PAA

Verify:

```text
use_paa=false does not call PAA provider
use_paa=true calls PAA provider
PAA suggestions source=paa
PAA suggestions have valid query type
PAA suggestions are not persisted before save
dedup works across user/ai/paa
max total query limit respected
PAA disabled returns 200 + warning + no PAA suggestions
missing SerpApi key returns 200 + warning + no PAA suggestions
PAA-only disabled request returns suggestions=[] + warning
raw SerpApi error not exposed
```

---

## Frontend tests

Verify:

```text
domain check client calls endpoint with auth
domain status badge renders reachable/unreachable/invalid/timeout
loading/error states work
domain unavailable soft-blocks domain-based generation only
manual seed query input remains available
audit save remains available
brand description generation remains available
PAA toggle appears
PAA payload includes usePaa/language/country
PAA suggestions append to seed query list
source=paa badge/metadata preserved
user can edit/delete PAA suggestion before save
removed PAA suggestion not saved
warnings/errors displayed safely
```

---

## Manual QA

Run:

```text
login
enter valid domain and check
enter invalid domain and check
enter unavailable domain and verify domain-based generation blocked/warned
manually enter seed queries despite bad domain
generate with PAA enabled
verify PAA suggestions append
edit/delete PAA suggestion
save/reload audit
verify source=paa preserved
switch language/country if available
```

---

## Safety checks

Must not expose:

```text
SerpApi API key
raw SerpApi response
raw HTTP body from domain check
request headers
stack traces
internal network details beyond safe reason code
```

---

## Exit criteria

Phase Q is stable when:

```text
domain checks require auth and are SSRF-safe
domain cache TTL is 86400
query_generation_allowed is true only for reachable
unavailable domain only soft-blocks domain-based generation
PAA suggestions work and dedup correctly
source=paa schema is valid
disabled/missing-key behavior is 200 + warning + no PAA suggestions
manual flow remains available
```
