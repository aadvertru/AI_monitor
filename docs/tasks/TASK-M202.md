# TASK-M202 — Add AuditTarget DB Model and Migration

## Status

Ready for implementation after TASK-M201.

## Goal

Add persistent storage for canonical audit targets.

Each audit target represents one model at one SCDL level.

---

## Dependencies

Requires:

```text
TASK-M201 — Define Canonical AuditTarget Contract
```

---

## Scope

Implement:

```text
AuditTarget DB model/table
migration if project uses migrations
repository/model helper validation where appropriate
basic DTO/schema support only if needed for model tests
task-scoped backend tests
```

Do not update audit create/update API behavior yet unless required to make model-level tests pass.

---

## Suggested fields

```text
id
audit_id
ai_family
execution_provider
model_provider
model_id
display_name
level
gateway
gateway_l2_experimental
created_at
updated_at
```

Optional fields:

```text
provider_config_snapshot
model_display_order
capability_metadata
```

Avoid overbuilding.

---

## Validation boundary for this task

This task is DB/model-layer focused.

Required validation may be implemented in one of these places, depending on project conventions:

```text
ORM/model helper
repository create/update helper
Pydantic schema used only for AuditTarget construction
DB CHECK constraint if the project commonly uses DB constraints
```

Do not add public audit create/update API validation in this task. That belongs to `TASK-M203`.

### Required model-layer validation

Validate:

```text
audit_id required
level must be L1 or L2
model_id required
execution_provider required
ai_family required
model_provider required or derivable
gateway_l2_experimental=true is invalid for level=L1
```

If the database cannot enforce all of these portably across SQLite/PostgreSQL, enforce them in repository/model helper tests and document any DB-level limitations.

---

## Rules

- Audit targets are audit-owned data.
- Deleting an audit should delete its targets according to existing audit-owned data policy.
- Existing audits should remain valid after migration.
- Do not require all existing audits to have targets immediately unless you also add a safe backfill.

Recommended:

```text
new audit_targets table starts empty for old audits
legacy conversion handled in later API/scheduling tasks
```

---

## Tests

Backend tests:

```text
migration creates audit_targets table
target can be created for audit
target requires audit_id
target requires model_id
target requires execution_provider
target requires ai_family
target requires model_provider or derives it according to helper policy
invalid level rejected by model/repository/schema layer
gateway_l2_experimental=true rejected for L1 by model/repository/schema layer
gateway_l2_experimental=true accepted for L2
targets deleted with audit if cascade exists
legacy audit without targets still loads
```

If DB constraints are implemented, add DB constraint tests for:

```text
invalid level
gateway_l2_experimental=true with L1
```

If DB constraints are not implemented, explicitly test the model/repository/schema validation path.

---

## Acceptance criteria

- AuditTarget model/table exists.
- Migration added if project uses migrations.
- Required fields validated at model/repository/schema layer.
- Validation boundary is documented in code/tests.
- Existing audits are not broken.
- Audit-owned relationship works.
- Task-scoped backend tests pass.
- Touched-file ruff passes.

---

## Escalate if

- The current DB migration system is unclear or unavailable.
- SQLite and PostgreSQL constraints diverge in a way that would make tests flaky.
- Existing audit delete policy is ambiguous for audit-owned records.
- Adding AuditTarget requires unrelated audit model refactor.

## Commands

Use task-scoped commands. Adjust exact paths to the repository layout.

Suggested backend checks:

```bash
pytest <task-specific tests>
ruff check <touched backend files>
```

Do not run or fix unrelated full-suite legacy failures inside this task.


## Done means

AuditTarget storage exists, migrations/tests pass, existing audits still load, and model-layer validation is covered without changing public create/update audit behavior.

---

## Non-goals

- Do not update create/edit API yet.
- Do not update scheduler yet.
- Do not update frontend.
- Do not implement model catalog.
- Do not fix unrelated legacy failures.
