# TASK-W207 — Add Matrix Empty, Partial, Failed, and Diagnostics States

## Goal

Polish the answer matrix for edge states and provider diagnostics.

---

## Scope

Implement:

```text
empty matrix state
partial audit state
failed audit state
provider diagnostics display
missing cell states
OpenRouter experimental L2 note
task-scoped frontend tests
```

---

## States

Handle:

```text
audit has no results
audit is running
audit is partial
audit failed
some cells failed
some cells missing/not_run
provider diagnostics exist
OpenRouter L2 experimental target present
```

---

## UI behavior

- Show clear no-results message.
- Show partial audit warning if applicable.
- Show provider diagnostics safely.
- Show OpenRouter L2 experimental notice when relevant.
- Do not show raw errors.

---

## Tests

Frontend tests:

```text
empty matrix state renders
running/processing state renders
partial audit warning renders
failed audit state renders
provider diagnostics render
missing cells render safely
OpenRouter experimental notice renders
unsafe diagnostic fields not rendered
```

---

## Acceptance criteria

- Edge states handled.
- Provider diagnostics visible and safe.
- OpenRouter L2 experimental note visible when relevant.
- No raw provider data exposed.
- Task-scoped frontend tests pass.
- TypeScript passes.

---

## Non-goals

- Do not change backend status semantics.
- Do not implement retry/cancel.
- Do not change provider diagnostics API.
