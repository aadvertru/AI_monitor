# TASK-N211 — Stabilize Model Catalog and Target Selector from Captured Issues

## Status

Conditional. Run only after TASK-N210.

## Goal

Fix captured Phase N issues only under strict scope control.

This task may proceed only when all Blocker/Major issues are in one subsystem. Otherwise split into issue-specific tasks.

## Dependencies

Requires:

```text
TASK-N210
docs/MODEL_CATALOG_SELECTOR_VERIFICATION.md with captured issues
```

## Scope gate

Before coding, group issues by subsystem:

```text
catalog service
cache
catalog endpoint
frontend selector
create/edit payload
estimate
legacy compatibility
model allowlist
safety
```

Proceed only if:

```text
all Blocker/Major issues are in one subsystem
and expected fix is small/task-scoped
```

If not, create narrower tasks, for example:

```text
TASK-N211A — Fix catalog stale-cache behavior
TASK-N211B — Fix selector model_targets payload mapping
TASK-N211C — Fix estimate integration warning state
```

## Allowed fixes

Only captured issues from TASK-N210.

## Not allowed

```text
broad backend+frontend stabilization PR
provider adapter changes
Phase M contract changes
results matrix UI
evaluation/fact-checking
unrelated legacy failures
```

## Required tests

Add tests directly tied to fixed issues.

## Acceptance criteria

- Only captured issues fixed.
- Scope gate respected.
- Tests added/updated.
- Affected verification scenarios rerun.
- Verification document updated.
- Task-scoped checks pass.

## Escalate if

- Fix touches more than one subsystem.
- Fix requires provider adapter changes.
- Fix requires changing backend target contract.
- Unrelated test failures appear.

## Commands

Run task-scoped backend and/or frontend checks for touched subsystem only.

## Done means

A small, single-subsystem Phase N issue set is fixed and re-verified, or the work is split.
