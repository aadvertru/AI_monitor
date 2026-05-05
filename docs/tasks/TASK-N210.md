# TASK-N210 — Run Model Catalog and Target Selector Verification

## Status

Ready after TASK-N209. Verification-only.

## Goal

Run the model catalog/selector verification checklist and capture actual issues.

Do not fix implementation bugs in this task except tiny documentation/setup corrections required to complete verification.

## Dependencies

Requires:

```text
TASK-N201 through TASK-N209
docs/MODEL_CATALOG_CONTRACT.md
docs/MODEL_CATALOG_SELECTOR_VERIFICATION.md
```

## Scope

Allowed:

```text
run manual/API/UI verification scenarios
record pass/fail/partial/blocked results
capture issues with severity and subsystem
```

Not allowed:

```text
fix catalog service bugs
fix cache bugs
fix selector bugs
fix create/edit bugs
fix estimate bugs
fix legacy compatibility bugs
fix unrelated failures
```

## Verification expectations

Run scenarios from the checklist:

```text
N-S01 through N-S14
```

Every non-pass scenario must have a captured issue.

## Issue template addition

Every issue must include subsystem:

```text
catalog service
cache
catalog endpoint
frontend selector
create/edit payload
estimate
legacy compatibility
model allowlist
i18n/display
safety
```

## Escalation rule

Escalate and split follow-up fixes if:

```text
more than one subsystem has Blocker/Major issues
fix would touch both backend and frontend
fix requires changing Phase M target contract
fix requires provider adapter changes
```

## Acceptance criteria

- Verification document updated with results.
- All scenarios marked.
- Every non-pass has issue with subsystem.
- No implementation bugs fixed.
- No secrets/raw provider data pasted into docs.

## Commands

Manual/API/UI verification only. Optional task-scoped tests may be run to support evidence, but failures must not be fixed in this task.

## Done means

Phase N issues are captured precisely enough to create narrow fix tasks.
