# TASK-Q209 — Verify and Stabilize Domain Check + PAA Query Enrichment

## Goal

Run the domain/PAA verification checklist and fix only issues captured during verification.

This task closes Phase Q.

---

## Required input

Read:

```text
docs/DOMAIN_PAA_VERIFICATION.md
docs/QUERY_ENRICHMENT_CONTRACT.md
```

Use captured issues from the verification document.

---

## Scope

Allowed fixes:

```text
domain normalization bugs
domain validation bugs
domain check SSRF safety bugs
domain status UI bugs
domain generation soft-block bugs
PAA provider/config bugs
PAA suggestion source/type bugs
PAA dedup/limit bugs
language/country bugs
PAA UI bugs
safe diagnostics bugs
```

Not allowed:

```text
full website crawling
content extraction from domain
new search providers beyond SerpApi/mock
audit pipeline redesign
parser/scoring changes
broad frontend redesign
unrelated legacy fixes
```

---

## Verification expectations

Run all scenarios:

```text
Q-S01 through Q-S12
```

Every non-pass scenario must have a captured issue.

---

## Tests to add/update

Add task-scoped tests based on actual issues.

Likely backend tests:

```text
domain normalization
SSRF blocking
DNS/HTTP mocked statuses
cache behavior
PAA adapter mocked success/error
PAA dedup/limit
source=paa persistence after save
language/country passthrough
```

Likely frontend tests:

```text
domain status badge
generation soft block
PAA toggle/payload
PAA append/edit/delete
warnings/errors
safe rendering
```

Safety tests:

```text
no API keys
no raw SerpApi response
no raw HTTP response bodies
no stack traces
```

---

## Acceptance criteria

- Verification document updated with final results.
- Blocker/major domain/PAA issues fixed or deferred with rationale.
- Domain check is safe and SSRF-protected.
- Domain unavailable soft-blocks only domain-based generation.
- Manual seed queries remain available.
- PAA suggestions can be generated, deduped, edited, deleted, and saved after confirmation.
- PAA suggestions preserve `source=paa`.
- Language/country behavior works.
- No SerpApi/API keys/raw responses exposed.
- Task-scoped backend/frontend tests pass.
- Touched-file ruff/typecheck pass.

---

## Non-goals

- Do not implement new external providers.
- Do not add website crawling.
- Do not change audit scoring/parser.
- Do not fix unrelated legacy failures.
