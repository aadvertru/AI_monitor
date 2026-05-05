# TASK-T206 — Add Source Domains Expandable UI

## Goal

Update the Sources tab/view to display grouped source domains with expandable URL-level evidence.

---

## Scope

Implement:

```text
domain-level source table/list
expand/collapse URL evidence
counts display
safe empty states
loading/error states
task-scoped frontend tests
```

---

## UI behavior

### Domain row

Show:

```text
domain
source_count
unique_url_count
query_count if available
model/level/provider indicators if available
expand button
```

### Expanded content

Show URL-level evidence:

```text
title
url
snippet/cited_text
query label/id if available
model/level/provider
```

Long URLs/snippets should truncate safely.

---

## Empty states

Handle:

```text
no sources
L1-only audit
OpenRouter L2 usable answer but no sources
partial/failed audit with no sources
```

Example copy:

```text
No sources were returned for this audit.
```

If OpenRouter L2 has missing sources metadata:

```text
This gateway L2 answer did not return citations.
```

Use i18n if available.

---

## Safety

Do not render:

```text
raw provider response
raw tool results
raw annotations
headers
API keys
raw prompts
```

URLs should be rendered safely.

External links should use safe attributes if opened in new tab:

```text
rel="noopener noreferrer"
```

---

## Tests

Frontend tests:

```text
domain rows render
counts render
expand shows URL evidence
collapse hides URL evidence
empty state renders
loading state renders
error state renders
long URL/snippet truncation or safe rendering
OpenRouter L2 no-sources message if metadata available
unsafe mocked fields not rendered
```

---

## Acceptance criteria

- Sources UI displays domain-level groups.
- Domain row expand/collapse works.
- URL evidence renders safely.
- Empty/loading/error states work.
- L1/no-source audits handled.
- Unsafe raw fields not rendered.
- Existing sources route remains accessible.
- Task-scoped frontend tests pass.
- TypeScript passes for touched files.

---

## Non-goals

- Do not implement backend aggregation.
- Do not add advanced filters unless trivial.
- Do not redesign all results UI.
- Do not change provider source extraction.
- Do not fix unrelated frontend bugs.
