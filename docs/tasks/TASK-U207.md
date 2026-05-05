# TASK-U207 — Update Results Details UI: Concepts vs Competitors

## Goal

Update the Results Details UI so generic phrases/concepts are no longer mislabeled as competitors.

Display separate sections:

```text
Concepts / Phrases
Competitor Candidates
```

---

## Scope

Implement:

```text
frontend API type updates if not done
Results Details UI labels
Concepts section
Competitor Candidates section
empty states
task-scoped frontend tests
```

---

## UI behavior

### Concepts section

Show descriptive terms/phrases:

```text
text
category if available
count/evidence count
```

Label examples:

```text
Concepts
Key phrases
Descriptive terms
```

Use i18n keys if available.

### Competitor Candidates section

Show:

```text
name
domain if available
confidence
evidence type
evidence count
```

If evidence detail is available, optionally allow expand.

### Empty states

Concepts empty:

```text
No concepts extracted yet.
```

Competitors empty:

```text
No competitor candidates found.
```

Do not display generic phrases in competitor section.

---

## Backward compatibility

If backend still returns legacy `competitors`, do not show it as competitors unless it maps to competitor_candidates.

Prefer:

```text
concepts field for concepts
competitor_candidates field for competitors
```

If only legacy field exists, show it under Concepts with a compatibility note if needed.

---

## Tests

Frontend tests:

```text
concepts render under Concepts section
competitor_candidates render under Competitor Candidates section
generic phrase does not appear under competitors
empty states render
legacy competitors fallback goes to concepts if needed
confidence/evidence displayed
unsafe fields not rendered
```

---

## Acceptance criteria

- Results Details no longer labels concepts as competitors.
- Concepts section renders.
- Competitor Candidates section renders.
- Empty states work.
- Legacy fallback safe.
- i18n-ready labels if i18n exists.
- Task-scoped frontend tests pass.
- TypeScript passes for touched files.

---

## Non-goals

- Do not implement backend extraction.
- Do not remove legacy API fields.
- Do not redesign whole results page.
- Do not change parser/scoring.
