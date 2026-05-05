# TASK-Q206 — Extend Seed Query Generation with PAA Suggestions

## Status

Ready for implementation.

## Goal

Extend seed query generation so it can include People Also Ask questions as seed query suggestions.

Generated PAA suggestions remain suggestions only and are not persisted until user confirms/saves the final seed query list.

## Dependencies

Requires:

```text
TASK-Q204 — PAA provider abstraction
TASK-Q205 — SerpApi PAA adapter
typed seed query source/type contract
```

## Scope

Implement:

```text
PAA mode in seed query suggestion endpoint/service
source=paa schema/enum support
language/country parameters
deduplication against existing queries
max total seed query limit
safe warning behavior
task-scoped backend tests
```

## Schema rule

Update seed query source enum/DTO to include:

```text
paa
```

Accepted source values should include at least:

```text
user
ai
paa
```

If project already has more sources (`domain`, `description`, `combined`), keep them.

## Request extension

```json
{
  "use_domain": true,
  "use_description": true,
  "use_paa": true,
  "language": "ru",
  "country": "ru",
  "existing_queries": []
}
```

## Response

```json
{
  "suggestions": [
    {
      "text": "Какие программы предлагает Студия балета Гармония?",
      "type": "problem_solution",
      "source": "paa",
      "metadata": {
        "paa_provider": "serpapi"
      }
    }
  ],
  "warnings": []
}
```

## Disabled/key-missing behavior

Decision:

```text
If use_paa=true but PAA is disabled, return 200 with warning and no PAA suggestions.
If use_paa=true but provider key is missing, return 200 with warning and no PAA suggestions.
If other generation modes are enabled, they may still return suggestions.
If only PAA is requested, return suggestions=[] with warning.
```

Warnings must be safe and must not expose raw provider errors.

## Deduplication

Deduplicate:

```text
PAA vs existing user queries
PAA vs existing AI queries
PAA vs other PAA queries
PAA vs newly generated AI suggestions if same request combines both
```

Respect max total seed query limit.

## Tests

Backend tests:

```text
source enum/DTO accepts paa
source enum/DTO rejects unknown source
use_paa=false does not call PAA provider
use_paa=true calls PAA provider
PAA suggestions have source=paa
PAA suggestions get valid query type
language/country passed to provider
duplicates skipped
max total limit respected
PAA disabled returns warning and no PAA suggestions
missing SerpApi key returns warning and no PAA suggestions
PAA-only disabled request returns empty suggestions + warning
suggestions not persisted before save
AI/manual/PAA dedup works together
raw SerpApi error not exposed
```

## Acceptance criteria

- Seed query source schema includes `paa`.
- Seed query generation supports PAA mode.
- PAA suggestions return `source=paa`.
- Disabled/missing-key behavior returns safe warnings, not ambiguous diagnostics.
- Language/country supported.
- Deduplication works.
- Max total seed query limit respected.
- Suggestions are not persisted before user save.
- Task-scoped backend tests pass.
- Touched-file ruff passes.

## Escalate if

- Existing seed query source is not enum/schema-backed and cannot be extended safely.
- Product wants PAA disabled/missing-key to hard-fail the entire generation request.
- PAA suggestion typing requires an unavailable classifier.

## Commands

```bash
pytest <seed query PAA tests>
ruff check <touched backend files>
```

## Done means

PAA suggestions work as typed, source=paa, safe, deduplicated suggestions with deterministic warning behavior.
