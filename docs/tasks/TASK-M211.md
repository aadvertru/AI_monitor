# TASK-M211 — Stabilize Canonical Audit Targets from Captured Issues

## Status

Conditional. Run only after TASK-M210.

## Goal

Fix captured Phase M issues only under strict scope control.

This task is not a catch-all. It can be used only when verification shows a small, single-subsystem issue set. Otherwise split into issue-specific tasks.

---

## Dependencies

Requires:

```text
TASK-M210
docs/AUDIT_TARGETS_VERIFICATION.md with captured issues
```

---

## Hard scope rule

Before changing code, classify captured issues by subsystem:

```text
DB/model
API DTO
scheduler
provider execution
frontend API mapping
caps/estimate
legacy compatibility
safety
```

This task may proceed only if:

```text
all Blocker/Major issues are in one subsystem
and the expected fix is small/task-scoped
and no unrelated legacy failures need fixing
```

If more than one subsystem has Blocker/Major issues, do not use this task as a combined fix PR. Create issue-specific tasks, for example:

```text
TASK-M211A — Fix provider model_id handoff
TASK-M211B — Fix frontend model_targets wire mapping
TASK-M211C — Fix audit estimate cap validation
```

---

## Allowed fixes

Only fix issues captured in TASK-M210.

Allowed categories:

```text
AuditTarget model validation bugs
create/update/detail DTO bugs
legacy compatibility bugs
scheduler query × target bugs
target_id persistence bugs
provider model_id handoff bugs
caps/estimate bugs
frontend API wire mapping bugs
safe metadata serialization bugs
```

---

## Not allowed

```text
model catalog implementation
audit target selector UI
results matrix UI
evaluation/fact-checking
parser/scoring redesign
OpenRouter adapter redesign beyond model_id handoff
unrelated legacy fixes
multiple-subsystem stabilization PR
```

---

## Required tests

Add/update tests directly tied to captured issues.

Likely tests:

```text
model_targets create/update/detail
legacy conversion
query × target scheduling
target.model_id provider request payload
target_id persistence
POST /audits/estimate
caps/run estimate
frontend modelTargets ↔ model_targets mapping
OpenRouter gateway metadata
legacy audit compatibility
```

---

## Required verification after fixes

Re-run only affected scenarios from:

```text
docs/AUDIT_TARGETS_VERIFICATION.md
```

Update issue statuses:

```text
Fixed
Deferred
Not reproducible
Needs follow-up
Blocked by environment
```

For each fixed issue, add:

```text
Fix summary
Files changed
Verification result
```

---

## Acceptance criteria

- Only captured Phase M issues are fixed.
- If more than one subsystem had Blocker/Major issues, this task was split instead of used as a catch-all.
- Tests added/updated for each fixed issue.
- Affected verification scenarios rerun.
- Verification document updated.
- No unrelated legacy failures fixed.
- Task-scoped backend/frontend tests pass.
- Touched-file ruff/typecheck pass.

---

## Escalate if

- Fix touches more than one subsystem.
- Fix requires changing parser/scoring.
- Fix requires model catalog or selector UI.
- Fix requires broad provider adapter redesign.
- Unrelated tests fail and cannot be isolated.
- Captured issues are too broad to resolve safely in one PR.

## Commands

Run only task-scoped checks related to fixed issues.

Suggested:

```bash
pytest <backend tests for fixed subsystem>
ruff check <touched backend files>
```

If frontend touched:

```bash
cd apps/web
npm run typecheck
npm test -- <frontend tests for fixed subsystem>
```

Do not fix unrelated full-suite failures.

---

## Done means

Captured issue(s) in one subsystem are fixed, tested, and re-verified, or the task is split into narrower issue-specific tasks.

---

## Non-goals

- Do not implement model catalog.
- Do not implement selector UI.
- Do not change parser/scoring.
- Do not fix unrelated bugs.
