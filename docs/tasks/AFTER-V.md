# AFTER-V — Testing Checklist After Web5 Summary UI

## Phase covered

Phase V — Web5 Summary UI.

## Primary goal to verify

The Web5-style summary page renders audit summary, tested scope, general metrics, model summary, diagnostics, and actions using backend data only.

---

## Frontend tests

### Page shell and data

Verify:

```text
summary v2 hook calls endpoint
loading state renders
safe error state renders
empty summary state renders
page shell renders
provider diagnostics placeholder renders
```

### Header and tested scope

Verify:

```text
audit title/status renders
date/number formatting used
query/target/level counts render
tested scope expands/collapses
action area renders
OpenRouter L2 experimental marker renders when present
```

### Summary cards

Verify:

```text
mentionability L1/L2 values render
accuracy L1/L2 values render when evaluation exists
accuracy shows N/A when evaluation missing
tone/sentiment card renders
partial data safe
zero denominator safe
no frontend score calculation
```

### Model summary

Verify:

```text
model summary rows render
MR L1/MR L2 render
missing L2 safe
missing accuracy safe
delta values render if backend provides them
tone values render
partial/failed model rows safe
responsive scroll/card fallback works
```

### Rerun fact-checking action

Final contract:

```text
POST /audits/{id}/rerun-evaluation backend endpoint is required
frontend client/hook is required
if endpoint/client missing, this is blocker/escalation, not acceptable disabled state
```

Verify:

```text
rerun fact-checking button renders enabled when audit state allows it
click calls rerun endpoint
loading state works
success invalidates summary/matrix queries
warnings shown
safe error shown
does not rerun provider calls
```

### Export/repeat actions

DOCX/Excel:

```text
may be disabled placeholders until Phase X
disabled placeholders must have clear copy/tooltip
```

Repeat audit:

```text
may be disabled placeholder until Phase X207A/B
```

### Responsive/accessibility

Verify:

```text
summary cards wrap on mobile
model summary accessible on mobile
actions accessible without hover
collapsible state accessible
buttons have accessible names
color is not sole indicator
```

### i18n

Verify:

```text
all static labels translated
raw audit title/user content not translated
```

---

## Backend/API checks

Verify:

```text
summary v2 DTO contains all fields used by UI
frontend does not calculate metrics
provider diagnostics safe
rerun evaluation endpoint exists before V206 action is considered complete
```

---

## Manual QA

Run:

```text
completed audit summary
partial audit summary
failed/no-data audit
audit without evaluation
audit with OpenRouter L2 experimental target
rerun fact-checking action
switch EN/RU
mobile layout
```

---

## Safety checks

UI must not display:

```text
raw provider response
raw prompt
headers
API keys
stack traces
raw evaluator payload
```

---

## Exit criteria

Phase V is stable when:

```text
Web5 summary is usable for completed/partial/failed audits
metrics come from backend
accuracy handles missing evaluation
model summary works
rerun fact-checking endpoint/action works
DOCX/Excel placeholders are safe until Phase X
i18n/mobile basics pass
```
