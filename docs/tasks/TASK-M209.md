# TASK-M209 — Add Multi-Target Audit Verification Checklist

## Status

Ready for implementation after TASK-M208.

## Goal

Create a manual QA checklist for canonical multi-target audit behavior.

This task is documentation-only. Do not change runtime code.

---

## Dependencies

Requires:

```text
TASK-M201 through TASK-M208
```

---

## File to create

```text
docs/AUDIT_TARGETS_VERIFICATION.md
```

---

## Required scenario format

Use this format for every scenario:

```markdown
## M-S01 — Scenario title

### Purpose
What this verifies.

### Preconditions
- Backend/frontend state.
- Test user/account.
- Provider mode/mock requirements.

### Steps
1. Step one.
2. Step two.

### Expected result
- Expected UI/API/backend behavior.

### Actual result
To be filled during verification.

### Status
Not run | Pass | Fail | Blocked | Partial

### Issue ID
Optional.
```

---

## Required scenarios

```text
M-S01 — Create legacy provider audit
M-S02 — Create audit with one model L1 target
M-S03 — Create audit with one model L1+L2 targets
M-S04 — Create audit with two model targets
M-S05 — Scheduler creates query × target runs
M-S06 — target_id preserved in jobs/runs/results
M-S07 — caps reject excessive audit
M-S08 — OpenRouter gateway target metadata preserved
M-S09 — Legacy audit still opens/runs
M-S10 — No raw provider data exposed
M-S11 — Same-level different model_id targets produce different provider request models
M-S12 — Frontend sends model_targets wire field, not modelTargets
M-S13 — POST /audits/estimate returns correct estimate and cap violations
```

---

## Result table

Include:

```markdown
| Scenario | Status | Notes | Issue ID |
|---|---|---|---|
| M-S01 | Not run |  |  |
```

Allowed statuses:

```text
Not run
Pass
Fail
Blocked
Partial
```

---

## Captured issues section

Use standard issue template:

```markdown
# Captured Issues

## ISSUE-M-001 — Short title

### Scenario
M-Sxx

### Severity
Blocker | Major | Minor | Cosmetic

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

## Acceptance criteria

- `docs/AUDIT_TARGETS_VERIFICATION.md` exists.
- Scenarios M-S01 through M-S13 included.
- Result table included.
- Captured issues template included.
- Checklist verifies legacy compatibility, target scheduling, caps, provider model payload, frontend wire shape, estimate endpoint, and safety.
- No runtime code changed.

---

## Escalate if

- A required scenario cannot be described because implementation surface is missing.
- Product wants to remove legacy compatibility from manual verification.
- Provider model payload cannot be manually or log-verified in current test environment.

## Commands

Documentation-only task.

Optional:

```bash
markdownlint docs/AUDIT_TARGETS_VERIFICATION.md
```

Do not run backend/frontend test suites.

---

## Done means

Manual QA checklist exists and is specific enough to verify canonical model targets end to end.

---

## Non-goals

- Do not run checklist.
- Do not fix bugs.
- Do not implement target model.
