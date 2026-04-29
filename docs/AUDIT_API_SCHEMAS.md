# Audit API Schemas

TASK-107 defines frontend-facing DTOs in `apps/api/audit_schemas.py`.

These contracts are intentionally separate from ORM models and pipeline objects. Later endpoint tasks should map database rows, parsed results, scores, and aggregation output into these schemas rather than returning internal objects directly.

## Intentionally Unavailable Fields

- Full raw provider answers are not exposed by these schemas. Result rows may include `raw_answer_ref` when a stored raw-response id is available and access-controlled by a later endpoint.
- SCDL level is represented as `scdl_level: "L1" | "L2"` after TASK-113. `L1` means no web access; `L2` means web access. Provider web/no-web execution behavior is not wired by TASK-113.
- Audit run trigger uses `AuditRunTriggerResponse` after TASK-109. The trigger response reports scheduled job counts and the audit state, but it does not expose internal worker/job objects.
- Competitor and source summary lists are schema-level frontend contracts. They default to empty lists until endpoint and aggregation tasks provide backed data.
- Sensitive user/auth fields such as `user_id`, `email`, `hashed_password`, password values, provider credentials, and raw credentials are not part of audit response DTOs.
