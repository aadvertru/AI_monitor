# TASK-U203 — Map Legacy Competitor Output to Concepts

## Goal

Stop treating the current extracted “competitors” as real competitors.

Map the existing output to `concepts` / `phrases` while preserving backward compatibility.

---

## Scope

Implement:

```text
legacy competitor output mapping
concept creation/persistence from current extractor output
backward-compatible response fields if needed
task-scoped backend tests
```

Do not implement real competitor candidate extraction yet.

---

## Required behavior

If current parser/extractor outputs:

```text
competitors = ["dance studio", "ballet classes", "children's programs"]
```

these should become:

```text
concepts = [...]
competitor_candidates = []
```

unless there is already strong brand-like evidence.

For this task, prefer conservative behavior:

```text
current legacy items → concepts
real competitors extraction deferred to U204/U205
```

---

## Backward compatibility

If existing frontend still reads `competitors`, either:

```text
keep legacy competitors field temporarily
```

or:

```text
return concepts under both fields with deprecation note
```

Preferred:

```text
add concepts field and keep legacy competitors unchanged until frontend update
```

Do not break current Results Details page.

---

## Tests

Backend tests:

```text
legacy extracted phrases become concepts
concepts persisted or returned
competitor_candidates empty
legacy response remains available if required
generic phrases not marked as competitors
parser/scoring unchanged
```

---

## Acceptance criteria

- Existing extracted “competitors” can be represented as concepts.
- Real competitor_candidates remain empty/conservative.
- Backward compatibility preserved.
- Current Results Details does not break.
- Parser/scoring behavior unchanged.
- Task-scoped backend tests pass.
- Touched-file ruff passes.

---

## Non-goals

- Do not implement competitor extraction.
- Do not update frontend labels yet.
- Do not remove legacy field.
- Do not use LLM classifier.
