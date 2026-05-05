# TASK-Y202 — Add Provider Usage Aggregation Model and Service

## Goal

Add backend storage/service for aggregating provider usage across runs, targets, audits, and users.

---

## Scope

Implement:

```text
usage aggregation DTO/model if needed
usage aggregation service
audit-level usage summary
target-level usage summary
task-scoped backend tests
```

Do not implement billing or token decrementing.

---

## Usage fields

Track available safe fields:

```text
input_tokens
output_tokens
total_tokens
cached_tokens
reasoning_tokens
web_search_requests
duration_ms
provider
model_id
level
target_id
run_id
audit_id
user_id
```

Do not estimate cost unless existing pricing data is already available.

---

## Rules

- Missing usage should not fail aggregation.
- Usage aggregation should handle OpenAI/OpenRouter/mock.
- Usage must not expose raw provider payloads.
- Usage should be safe for Profile page later, but not decrement fake tokens yet.

---

## Tests

Backend tests:

```text
aggregate audit usage
aggregate target usage
aggregate user usage if service supports it
missing usage safe
OpenRouter web_search_requests included if present
legacy runs safe
no raw provider data included
```

---

## Acceptance criteria

- Usage aggregation service exists.
- Audit-level usage can be computed.
- Target-level usage can be computed.
- Missing usage safe.
- No billing/token decrementing implemented.
- Task-scoped backend tests pass.
- Touched-file ruff passes.

---

## Non-goals

- Do not implement real billing.
- Do not decrement user tokens.
- Do not implement background worker.
- Do not change provider adapters unless needed to expose safe usage already available.
