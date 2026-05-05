# AFTER-W — Testing Checklist After Web6/Web7 Answer Matrix UI

## Phase covered

Phase W — Web6/Web7 Answer Matrix UI.

## Primary goal to verify

The answer matrix renders questions × model/level targets with safe cell states, evaluation verdicts, rationale previews, expand details, and filters.

---

## Frontend tests

### Data and shell

Verify:

```text
matrix hook calls endpoint
loading state renders
safe error state renders
empty matrix state renders
page shell renders
provider diagnostics placeholder safe
```

### Matrix layout

Verify:

```text
columns render from matrix columns
rows render from matrix rows
cells align by target_id
missing cells render placeholder
horizontal scroll container exists
long question text safe
OpenRouter gateway metadata does not break layout
```

### Cell rendering

Verify:

```text
completed cell shows excerpt
correct verdict badge renders
partial verdict badge renders
incorrect verdict badge renders
unknown/null evaluation safe
rationale preview renders
source count renders
failed cell shows provider error
missing/not_run cell safe
verdict labels i18n-ready
unsafe raw fields not rendered
```

### Expand details

Safe full-answer source is mandatory.

Verify:

```text
full answer is shown only from safe normalized field or safe result detail endpoint
if no safe full-answer source exists, UI shows excerpt-only or task escalates
details never use raw provider response
details never use raw prompt
details never use raw tool result
details never use raw annotations
```

Also verify:

```text
expand opens details
details show query/model/level
details show safe answer/evaluation
failed details show provider diagnostic
close works
keyboard accessible if supported
```

Mandatory unsafe-field tests:

```text
raw_response not rendered
raw_prompt not rendered
raw_tool_result not rendered
raw_annotations not rendered
headers/authorization/api_key not rendered
```

### Filters

Verify:

```text
level filter works
AI family filter works
model filter works
verdict filter works
query type filter works
status filter works
clear filters resets
empty filtered state renders
row/column alignment preserved
```

### Edge states

Verify:

```text
running/processing state
partial audit warning
failed audit state
provider diagnostics
missing cells
OpenRouter L2 experimental notice
```

### Responsive/accessibility

Verify:

```text
many columns usable
question column readable
no hover-only controls
expand buttons accessible by role/name
filters have labels
color not sole indicator
mobile smoke test
```

---

## Manual QA

Run:

```text
matrix for completed audit
multi-model L1/L2 audit
correct/partial/incorrect badges
expand several cells
verify full answer source is safe or excerpt-only
failed cell diagnostics
missing/not-run cells
filter by L1
filter by model
filter by verdict
horizontal scroll
mobile smoke test
switch EN/RU
```

---

## Safety checks

UI must not display:

```text
raw provider response
raw prompt
request headers
API keys
raw tool payloads
raw annotations
stack traces
```

---

## Exit criteria

Phase W is stable when:

```text
matrix is usable for multi-model L1/L2 audits
cells show verdict/excerpt/rationale/status safely
expand details use only safe normalized answer source
filters work
responsive/accessibility basics pass
no raw provider data exposed
```
