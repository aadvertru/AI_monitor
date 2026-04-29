# TASK_AUTHORING_GUIDE.md

**Version:** 1.1  
**Last updated:** 2026-04-27  
**Status:** Living document

---

## 1. Purpose

This guide defines how tasks must be written before they are given to an AI coding agent.

A task is not a vague TODO item. A task is an execution contract between the planner, the implementation agent, the reviewer, and CI.

Every task must be small enough to fit into one pull request and precise enough to be implemented without reinterpreting product intent.

This guide is project-agnostic. Project-specific commands, conventions, completion rules, and global escalation rules should be defined in `/AGENTS.md`, `/docs/TEST_STRATEGY.md` (if available), or another project-specific control document.

---

## 2. Core Rule

Every task must answer:

1. What must be built?
2. Why is it needed?
3. What context matters?
4. What is included?
5. What is excluded?
6. How will success be verified?
7. What tests are mandatory?
8. When must the agent stop and escalate?

---

## 3. Required Task Format

```markdown
## TASK-000 — Short imperative title

### Status
Planned

### Goal
One clear sentence describing the expected outcome.

### Why
Explain the product or technical reason for this task.

### Context
Optional. Include only if the task requires background that is not obvious from the goal, architecture, or surrounding tasks.

### Scope
- What must be added, changed, or removed
- What must be verified
- What behavior must be preserved

### Out of scope
- What must not be changed
- Related work explicitly excluded from this task
- Features or refactors that must wait for another task

### Acceptance criteria
- Observable result 1
- Observable result 2
- Observable result 3

### Test requirements
- Unit test requirement 1
- Edge case test requirement 2
- Regression test requirement 3

### Files likely affected
Optional. Include only if the task touches unexpected, non-obvious, generated, legacy, or cross-cutting files.
- `src/...`
- `tests/...`

### Commands
Replace with actual project commands from `/AGENTS.md` or the project README.
- `<test command>`
- `<lint command>`
- `<typecheck command, if applicable>`
- `<build command, if applicable>`

### Dependencies
- TASK-000, if applicable
- None, if no dependency exists

### Escalate if
Global escalation rules are defined in `/AGENTS.md`.
Add only task-specific escalation triggers here.
- Task-specific ambiguity or contradiction
- Missing domain schema, fixture, or contract required by this task
- Required change exceeds this task scope

### Done means
Inherits project defaults from `/AGENTS.md`.
Override here only if this task has additional completion requirements.
```

---

## 4. Writing Rules

### 4.1 Goal

The goal must be one sentence.

Bad:

```markdown
Improve parser.
```

Good:

```markdown
Add a provider response parser that converts raw provider payloads into normalized internal records.
```

### 4.2 Why

The `Why` section must explain the reason, not repeat the goal.

Bad:

```markdown
We need this because we need a parser.
```

Good:

```markdown
The scoring engine must not depend on provider-specific response formats.
```

### 4.3 Context

The `Context` section is optional.

Use it when the implementation agent needs background that is not obvious from the title, goal, or architecture documents.

Good reasons to add context:

```text
- The task belongs to a larger feature or migration
- The task depends on a previous design decision
- The task touches a user flow or business rule
- There is a known historical bug or regression
- There is a non-obvious integration constraint
```

Bad context:

```markdown
This is important.
```

Good context:

```markdown
Provider responses are stored as raw JSON for auditability, but downstream scoring should operate only on normalized parser records. This task creates the normalization boundary before scoring is implemented.
```

Do not use `Context` as a place to duplicate the full architecture document.

### 4.4 Scope

Scope must describe what the implementation agent is allowed and expected to change.

Good:

```markdown
### Scope
- Add parser module
- Add typed normalized output object
- Handle malformed provider response safely
- Add unit tests for parser behavior
```

### 4.5 Out of scope

Every task must explicitly say what not to touch.

Good:

```markdown
### Out of scope
- Do not change scoring logic
- Do not change provider clients
- Do not change database schema
- Do not add new provider integrations
```

Scope and out-of-scope must not overlap. If they appear to overlap, the task is not ready.

---

## 5. Acceptance Criteria Rules

Acceptance criteria must be observable and testable.

Bad:

```markdown
- Parser should work well
- Code should be clean
```

Good:

```markdown
- Valid provider response returns a normalized record
- Missing optional fields do not crash the parser
- Missing required fields return an explicit validation error
- Malformed JSON returns a safe parser error
```

Acceptance criteria must not describe implementation details unless the implementation detail is part of the requirement.

Each acceptance criterion should be verifiable by at least one of:

```text
- Unit test
- Integration test
- Typecheck
- Lint/static analysis
- Build
- Manual verification step
- Reviewer inspection
```

---

## 6. Test Requirements Rules

Every implementation task must include test requirements.

The test section must specify at least:

```markdown
- Success path
- Failure path
- Edge case
- Regression case, if applicable
```

Good:

```markdown
### Test requirements
- Add unit test for valid provider response
- Add unit test for missing required field
- Add unit test for malformed JSON
- Add regression test for empty response
```

If no automated test is required, the task must explicitly explain why:

```markdown
### Test requirements
- No automated test required because this task only updates documentation.
```

Avoid vague test requirements.

Bad:

```markdown
- Add tests
- Cover edge cases
```

Good:

```markdown
- Add a unit test where the provider response is empty
- Add a unit test where a required field is missing
- Add a unit test where malformed JSON returns a safe parser error
```

---

## 7. Commands Rules

The `Commands` section must not hardcode commands from another ecosystem.

Project-specific commands belong in `/AGENTS.md`, package scripts, Makefiles, CI configuration, or project README.

Task files may either reference project defaults:

```markdown
### Commands
Use project commands from `/AGENTS.md`.
```

Or list concrete commands when the task needs special handling:

```markdown
### Commands
- `<test command>`
- `<lint command>`
- `<typecheck command, if applicable>`
- `<build command, if applicable>`
```

Examples by ecosystem:

```text
JavaScript/TypeScript:
- npm test
- npm run lint
- npm run typecheck
- npm run build

Python:
- pytest
- ruff check .
- mypy .
- python -m build

Go:
- go test ./...
- go vet ./...
- go build ./...

Rust:
- cargo test
- cargo clippy -- -D warnings
- cargo build
```

The examples above are illustrative only. Replace them with the actual project commands.

---

## 8. Files Likely Affected Rules

`Files likely affected` is optional.

Use this section only when it prevents confusion.

Good use cases:

```text
- The relevant files are non-obvious
- The task touches generated files
- The task touches legacy code
- The task touches configuration outside the main source tree
- The task must avoid similarly named files
```

Bad use cases:

```text
- Guessing files before the implementation exists
- Listing every possible file
- Using the section as a hard boundary when the task may require nearby tests or fixtures
```

If included, the section is a hint, not a hard constraint unless explicitly stated.

Recommended wording:

```markdown
### Files likely affected
Optional hint, not a hard boundary.
- `src/parser/...`
- `tests/parser/...`
```

If the task must be limited to specific files, state that explicitly in `Scope` or `Out of scope`.

---

## 9. Task Size Rules

A task must fit into one pull request.

Principles:

```text
- One task = one PR
- One PR = one coherent change
- Prefer small, reviewable diffs
- Avoid mixing feature work, refactoring, formatting, and migrations
- Adjust size thresholds per project
```

Suggested starting thresholds:

```text
- Preferred: under 500 lines of diff
- Warning threshold: around 800 lines of diff
- Hard threshold: around 1200 lines of diff unless explicitly approved
```

These numbers are starting points, not universal limits. Adjust them based on project language, generated code, test fixture size, and reviewer capacity.

Split the task if:

```text
- It affects unrelated modules
- It mixes refactoring and feature work
- It changes architecture and implementation at the same time
- It requires large fixtures or migrations
- It cannot be reviewed in one focused pass
```

---

## 10. Dependencies

Dependencies must be explicit.

Good:

```markdown
### Dependencies
- TASK-003 — Define normalized provider response schema
```

If there are no dependencies:

```markdown
### Dependencies
- None
```

Do not rely only on task order. If a task requires another task to be completed first, say so.

---

## 11. Escalation Rules

Global escalation rules belong in `/AGENTS.md`.

Task files should include only task-specific escalation triggers.

Global examples:

```text
- Security-sensitive area is touched
- Authentication or authorization is touched
- Payments are touched
- Permissions are touched
- Secrets are touched
- Database migration appears necessary
- Public API behavior would change
- Existing tests contradict the task
- Implementation requires product decision
- Scope expansion is needed
```

Task-specific examples:

```markdown
### Escalate if
- Provider response schema is missing or inconsistent
- Parser implementation requires changing scoring logic
- Existing fixtures contradict the expected parser behavior
```

The agent must not silently invent product behavior.

---

## 12. Done Means Rules

Generic completion rules belong in `/AGENTS.md`.

Example global completion rule:

```markdown
## Done means

A task is done only when:
- Code is implemented
- Required tests are added or updated
- Project commands pass
- CI passes
- PR description includes summary and test report
- No out-of-scope files were changed
```

Do not copy this checklist into every task unless the project intentionally requires it.

In a task file, use:

```markdown
### Done means
Inherits project defaults from `/AGENTS.md`.
```

Only override when the task has additional completion requirements:

```markdown
### Done means
Inherits project defaults from `/AGENTS.md`.

Additional completion requirements:
- Migration rollback instructions are documented
- Manual QA checklist for the export flow is attached to the PR
```

---

## 13. Forbidden Task Wording

Avoid vague instructions:

```text
- improve
- optimize
- clean up
- make better
- fix everything
- refactor the module
- handle all edge cases
- make it production-ready
```

These words are allowed only when followed by concrete criteria.

Bad:

```markdown
Optimize parser performance.
```

Good:

```markdown
Reduce parser runtime for a 1,000-item provider response by avoiding repeated JSON parsing. Add a benchmark or unit-level performance guard if the project supports it.
```

---

## 14. Task Status Values

Allowed status values:

```text
Planned
Ready
In Progress
Blocked
In Review
Done
Cancelled
```

Do not mark a task as `Ready` unless it has:

```text
- Goal
- Scope
- Out of scope
- Acceptance criteria
- Test requirements
- Dependencies
- Task-specific escalation rules, or an explicit statement that global escalation rules are sufficient
```

Recommended wording when no task-specific escalation rule exists:

```markdown
### Escalate if
- Use global escalation rules from `/AGENTS.md`.
```

---

## 15. Example Task

```markdown
## TASK-014 — Implement provider response parser

### Status
Ready

### Goal
Add a parser that converts raw provider responses into normalized internal parser records.

### Why
The scoring engine must consume one stable internal format instead of depending on provider-specific response structures.

### Context
Provider responses are stored as raw JSON for auditability, but scoring should only consume normalized parser records. This task creates the normalization boundary before scoring logic is implemented.

### Scope
- Add provider response parser module
- Define typed normalized parser output
- Handle malformed input safely
- Return explicit validation errors for missing required fields
- Add unit tests for parser behavior

### Out of scope
- Do not change scoring logic
- Do not change provider clients
- Do not change database schema
- Do not add new provider integrations

### Acceptance criteria
- Valid provider response returns a normalized record
- Missing optional fields do not crash the parser
- Missing required fields return an explicit validation error
- Malformed JSON returns a safe parser error
- Existing scoring tests continue to pass

### Test requirements
- Add unit test for valid provider response
- Add unit test for missing optional fields
- Add unit test for missing required fields
- Add unit test for malformed JSON
- Add regression test for empty provider response

### Files likely affected
Optional hint, not a hard boundary.
- `src/parser/...`
- `tests/parser/...`

### Commands
Use project commands from `/AGENTS.md`.

### Dependencies
- TASK-003 — Define normalized provider response schema

### Escalate if
- Provider response schema is missing or inconsistent
- Parser implementation requires changing scoring logic
- Existing fixtures contradict the expected parser behavior

### Done means
Inherits project defaults from `/AGENTS.md`.
```

---

## 16. Human Reviewer Checklist

A human reviewer must reject a task if:

```text
- Acceptance criteria are vague
- Test requirements are missing
- Out of scope is missing
- Dependencies are missing
- Escalation rules are missing or only implied
- The task mixes unrelated changes
- The task is too large for one PR
- The task requires a product decision but does not state it
- Scope and out-of-scope overlap
- Commands are copied from the wrong ecosystem
```

---

## 17. AI Reviewer Checklist

An AI reviewer must reject or request clarification if any of the following conditions are true:

```text
Required section checks:
- Missing Goal
- Missing Scope
- Missing Out of scope
- Missing Acceptance criteria
- Missing Test requirements
- Missing Dependencies
- Missing Escalate if

Quality checks:
- Goal is not one sentence
- Acceptance criteria contain only vague wording
- Test requirements say only "add tests" or "cover edge cases"
- Scope and out-of-scope appear to contradict each other
- Files likely affected is treated as a hard boundary without saying so
- Commands are hardcoded from an unrelated ecosystem
- Done means duplicates global project rules without task-specific overrides
- The task uses forbidden wording without concrete measurable criteria
- The task appears too large for one focused PR
- The task requires a product decision but does not ask for escalation
```

Forbidden wording detection:

```text
Flag these words unless followed by concrete criteria:
- improve
- optimize
- clean up
- make better
- fix everything
- refactor
- handle all edge cases
- production-ready
```

Suggested structured review output:

```json
{
  "decision": "request_changes",
  "severity": "important",
  "missing_sections": ["Out of scope"],
  "issues": ["Acceptance criteria contain vague wording: 'should work well'"],
  "recommended_changes": ["Replace vague criteria with observable conditions"]
}
```

Alternative decisions:

```text
approve
request_changes
needs_human_clarification
```

Severity levels:

```text
none
minor
important
critical
```

The AI reviewer must not approve a task with missing acceptance criteria, missing test requirements, or unclear scope.

---

## 18. Execution Prompt Template

Use this template when assigning a task to an AI implementation agent:

```text
Implement TASK-000 from /docs/TASKS.md.

Follow:
- /AGENTS.md
- /docs/ARCHITECTURE.md
- /docs/TEST_STRATEGY.md
- /docs/TASK_AUTHORING_GUIDE.md

Requirements:
- Keep changes limited to the task scope.
- Do not change anything listed as out of scope.
- Add or update required tests before or alongside implementation.
- Use project commands from /AGENTS.md.
- Fix failing tests before opening the PR.
- Open a PR with a concise summary and test report.

Escalate instead of proceeding if the task is ambiguous, contradicts architecture, or requires scope expansion.
In case of conflict between documents, do not proceed. Escalate instead of guessing.
```

---

## 19. Task Authoring Preflight Checklist

Before marking a task as `Ready`, verify:

```text
- The task has one clear goal
- The task has a reason
- Context is included if needed
- Scope is specific
- Out-of-scope is explicit
- Acceptance criteria are observable
- Test requirements are concrete
- Dependencies are explicit
- Commands reference project defaults or use actual project commands
- Files likely affected is omitted unless useful
- Escalation rules are task-specific or explicitly defer to global rules
- Done means inherits project defaults unless task-specific completion rules are needed
- The task can fit into one focused PR
```
