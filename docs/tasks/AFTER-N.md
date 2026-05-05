# AFTER-N — Testing Checklist After OpenRouter Model Catalog and Audit Target Selector

## Phase covered

Phase N — OpenRouter Model Catalog + Audit Target Selector.

## Primary goal to verify

Users can select AI families, models, and L1/L2 levels from an authenticated backend-controlled OpenRouter catalog without manually typing model IDs.

---

## Backend tests

### Model catalog service

Verify:

```text
OpenRouter catalog fetch is mocked in tests
no real OpenRouter calls in CI
service uses /api/v1/models/user or escalates if unavailable
OPENROUTER_CATALOG_ENABLED=false does not call OpenRouter and returns safe diagnostic
missing OPENROUTER_API_KEY does not call OpenRouter and returns safe diagnostic
missing/empty OPENROUTER_ALLOWED_MODELS returns CONFIGURATION_ERROR
catalog normalizes model_id/display_name/model_provider/ai_family
unknown model provider prefix is not assigned to supported AI family
models grouped by AI family
```

### Cache behavior

Verify mandatory behavior:

```text
catalog cache TTL = 24h
cache hit avoids repeated fetch
cache expires and refreshes
fetch failure with existing cache returns stale cache + safe warning
fetch failure with no cache returns safe diagnostic/error
warnings do not expose raw OpenRouter payloads
```

### Allowlist/product policy

Verify final semantics:

```text
frontend-facing service output returns only allowed models
disallowed models are not included
normal frontend DTO does not include is_allowed
backend allowlist controls what product allows
frontend cannot execute arbitrary model ids
L1 capability flags returned
OpenRouter L2 marked experimental
```

### Catalog endpoint

Verify:

```text
GET /model-catalog requires login
unauthenticated request rejected
authenticated request returns families
only allowed models returned
is_allowed not present in response
cache metadata returned
stale-cache warning returned when applicable
safe no-cache failure behavior works
OpenRouter API key not exposed
raw OpenRouter response not exposed
```

---

## Frontend tests

### Catalog hook/client

Verify:

```text
client calls authenticated /model-catalog
families parsed
models parsed
empty catalog handled
warning/error handled
loading state handled
no isAllowed/is_allowed dependency in normal UI model
```

### Target selector

Verify:

```text
default AI family block visible
plus button adds family block
family can be selected
model multiselect works
selected model with L1 creates one target
selected model with L1+L2 creates two targets
unsupported L2 toggle disabled
OpenRouter L2 experimental marker visible
duplicate target prevented
remove model/family updates targets
```

### Create/Edit integration

Verify:

```text
create audit sends wire model_targets
actual request body does not contain modelTargets
edit audit loads backend model_targets into selector
edit audit saves updated model_targets
legacy audit loads into selector or safe fallback
empty target selection blocks save
backend validation error shown safely
```

### Run estimate

Verify final contract:

```text
frontend calls POST /audits/estimate
estimate request body uses model_targets
estimate request body does not contain modelTargets
estimate updates when queries change
estimate updates when selected targets change
same model L1+L2 counts two targets
over-cap warning shown from backend response
backend remains source of truth
```

---

## Manual QA

Run these checks:

```text
login
open create audit
confirm model catalog loads
confirm first ChatGPT block is visible
select one ChatGPT model L1
add Gemini block
select Gemini model L1+L2
confirm OpenRouter L2 experimental marker
confirm run estimate updates via backend
save audit
reload audit
verify selected targets persist
start mock audit
verify expected number of runs
```

---

## Safety checks

Ensure frontend/backend do not expose:

```text
OPENROUTER_API_KEY
raw OpenRouter catalog response
headers
internal config dump
disallowed model list in normal frontend response
```

---

## Exit criteria

Phase N is stable when:

```text
/model-catalog is authenticated
catalog loads from backend
catalog returns allowed-only models
stale cache behavior is deterministic
selector creates canonical model_targets
create/edit persists targets using wire model_targets
legacy audits remain safe
run estimate uses POST /audits/estimate
no arbitrary model id can execute
```
