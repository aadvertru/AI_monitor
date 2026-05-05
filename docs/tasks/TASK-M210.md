# TASK-M210 — Run Multi-Target Audit Verification and Capture Issues

## Status

Ready after TASK-M209.

## Goal

Run the multi-target audit verification checklist and capture actual issues.

This is a verification-only task. Do not fix implementation bugs in this task, except tiny documentation/setup corrections required to complete verification.

---

## Dependencies

Requires:

```text
TASK-M201 through TASK-M209
docs/AUDIT_TARGETS_CONTRACT.md
docs/AUDIT_TARGETS_VERIFICATION.md
```

---

## Scope

Allowed:

```text
run manual/API verification scenarios
record pass/fail/partial/blocked results
capture issues with severity and evidence
make tiny doc/setup corrections if necessary
```

Not allowed:

```text
fix AuditTarget model bugs
fix DTO bugs
fix scheduler bugs
fix provider model payload bugs
fix frontend API mapping bugs
fix caps/estimate bugs
fix unrelated legacy failures
```

Implementation fixes belong to follow-up issue-specific tasks or TASK-M211 under strict constraints.

---

## Verification expectations

Run scenarios:

```text
M-S01 through M-S13
```

Every non-pass scenario must have a captured issue.

---

## Issue capture rules

For every failed, partial, or blocked scenario, add:

```markdown
## ISSUE-M-001 — Short title

### Scenario
M-Sxx

### Severity
Blocker | Major | Minor | Cosmetic

### Subsystem
DB/model | API DTO | scheduler | provider execution | frontend API mapping | caps/estimate | legacy compatibility | safety | other

### Actual result
...

### Expected result
...

### Evidence
...

### Suggested next step
Fix now / defer / needs investigation.
```

---

## Required attention points

During verification, explicitly check:

```text
target.model_id drives actual provider request model
two same-level targets with different model_id values do not collapse
frontend request body uses model_targets, not modelTargets
POST /audits/estimate exists and returns concrete response
legacy providers/scdl audits still work
caps reject excessive audits
no raw provider data exposed
```

---

## Acceptance criteria

- Verification document updated with actual results.
- Every scenario M-S01 through M-S13 marked Pass/Fail/Partial/Blocked.
- Every non-pass has captured issue.
- Every issue includes subsystem.
- No implementation bugs fixed in this task.
- No unrelated legacy failures fixed.
- No secrets/raw provider data pasted into docs.

---

## Escalate if

- More than one subsystem has Blocker/Major issues.
- A scenario cannot be run because a required prior task was not implemented.
- Verification requires real provider calls unexpectedly.
- Evidence would require logging raw prompts/responses/secrets.
- Fixing anything would require touching more than tiny doc/setup files.

## Commands

Run only verification/manual/API checks necessary for the checklist.

If lightweight task-scoped tests are useful for confirming observed behavior, run them, but do not fix failures in this task.

Suggested:

```bash
pytest <task-specific verification/support tests, if any>
```

---

## Done means

Phase M verification results are documented, issues are captured with subsystem labels, and the next fix tasks can be scoped precisely.

---

## Non-goals

- Do not implement model catalog.
- Do not implement selector UI.
- Do not change parser/scoring.
- Do not fix implementation bugs.
- Do not fix unrelated bugs.
