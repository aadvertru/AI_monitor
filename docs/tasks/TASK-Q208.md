# TASK-Q208 — Add Domain Check and PAA Verification Checklist

## Goal

Create a manual QA checklist for domain availability checks and PAA seed query enrichment.

This task is documentation-only. Do not change runtime code.

---

## File to create

```text
docs/DOMAIN_PAA_VERIFICATION.md
```

---

## Required scenarios

Use scenario format with purpose, preconditions, steps, expected result, actual result, status, and issue ID.

Scenarios:

```text
Q-S01 — Reachable domain check
Q-S02 — Invalid domain check
Q-S03 — DNS failure / unreachable domain
Q-S04 — Private network / localhost blocked
Q-S05 — Domain unavailable soft-blocks domain-based generation only
Q-S06 — Manual seed queries still work with unavailable domain
Q-S07 — Generate queries with PAA enabled
Q-S08 — PAA disabled / missing SerpApi key safe error
Q-S09 — PAA suggestions deduplicate with existing queries
Q-S10 — PAA suggestions respect max seed query limit
Q-S11 — PAA language/country parameters
Q-S12 — PAA suggestions save/reload correctly after user confirmation
```

---

## Result table

Include:

```markdown
| Scenario | Status | Notes | Issue ID |
|---|---|---|---|
| Q-S01 | Not run |  |  |
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

## ISSUE-Q-001 — Short title

### Scenario
Q-Sxx

### Severity
Blocker | Major | Minor | Cosmetic

### Actual result
...

### Expected result
...

### Evidence
...

### Suggested next step
...
```

---

## Acceptance criteria

- `docs/DOMAIN_PAA_VERIFICATION.md` exists.
- Scenarios Q-S01 through Q-S12 included.
- Result table included.
- Captured issue template included.
- Checklist verifies domain soft-block policy.
- Checklist verifies PAA source/dedup/persistence behavior.
- Checklist verifies no SerpApi key/raw response leakage.
- No runtime code changed.

---

## Non-goals

- Do not run checklist.
- Do not fix bugs.
- Do not implement domain/PAA features.
