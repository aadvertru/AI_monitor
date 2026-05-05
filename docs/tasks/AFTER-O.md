# AFTER-O — Testing Checklist After i18n Foundation

## Phase covered

Phase O — i18n Foundation.

## Primary goal to verify

The UI supports English and Russian now, while remaining ready for future languages.

---

## Frontend tests

### i18n framework

Verify:

```text
i18next/react-i18next initialized
fallback locale works
known key renders in en
known key renders in ru
missing key behavior safe
locale config can be extended beyond en/ru
no binary-only en/ru logic in implementation
```

### Language switcher

Verify:

```text
language switcher renders
switch to ru updates UI labels
switch to en updates UI labels
selected locale persists after reload
invalid stored locale falls back safely
```

### Core UI translation

Verify labels in existing surfaces:

```text
app shell
navigation
auth pages
audit list
audit create/edit
audit detail/status
results labels that already exist
sources labels that already exist
common buttons
empty/loading/error states
provider diagnostic labels
```

Profile/account labels:

```text
translated only if Profile UI already exists
if Profile UI does not exist yet, profile namespace keys may exist but no runtime UI is required
```

### Formatting

Verify locale-aware formatting:

```text
dates
times
numbers
percentages
token counts
run counts
source counts
```

### Raw content protection

Verify these are not translated:

```text
raw AI answers
seed queries
brand descriptions
source titles/snippets
user-entered content
model ids
provider ids
email/name values
```

---

## Backend/API checks

Verify:

```text
backend still returns stable codes
status/error/verdict codes are not localized by backend
business logic does not depend on frontend locale
```

---

## Manual QA

Run:

```text
switch EN → RU → EN
reload page and verify locale persists
open audit list/detail/create/results/profile if available
verify labels are translated
verify raw answers remain unchanged
verify dates/percentages format according to locale
try invalid localStorage locale and verify fallback
```

---

## Safety checks

Ensure translations do not accidentally include:

```text
raw provider payloads
API keys
debug strings
internal config
```

---

## Exit criteria

Phase O is stable when:

```text
i18next/react-i18next works
en/ru UI works
locale persists
fallback works
future locale architecture is not hardcoded to two languages
raw AI/user content is not translated
profile labels are translated only when profile UI exists
```
