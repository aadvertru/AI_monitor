# TASK-S202 — Add Audit-Scoped Brand Facts Store

## Status

Ready for implementation.

## Goal

Add a structured, audit-scoped brand facts store for answer evaluation/fact-checking.

## Dependencies

Requires:

```text
TASK-S201 — Evaluation contract
audit/brand models
```

## Decision

Brand facts are audit-scoped snapshots.

Rules:

```text
BrandFact.audit_id is required.
BrandFact.brand_id may be stored as reference if available.
Evaluation uses facts from the same audit snapshot.
Facts are immutable for that audit unless explicitly regenerated.
Changing brand profile later does not alter old audit facts.
```

This prevents old evaluations from using the wrong future brand facts.

## Scope

Implement:

```text
BrandFact model/table or equivalent
audit-scoped fact creation
fact DTOs
migration if applicable
task-scoped backend tests
```

## Fields

Suggested:

```text
id
audit_id
brand_id nullable/reference
fact_text
fact_type
source
confidence
created_at
```

Fact types:

```text
brand_name
official_domain
description_claim
user_provided
domain_analysis_future
```

Sources:

```text
brand_name
brand_domain
brand_description
user
system
```

## Initial fact creation

Create conservative facts from:

```text
brand_name
brand_domain
brand_description
```

Do not invent unsupported facts.

## Tests

Backend tests:

```text
BrandFact requires audit_id
facts can reference brand_id if available
facts created from brand name/domain/description
facts are audit-scoped
old audit facts unchanged when brand fields change later
facts preserve source/type
empty description handled
legacy audit handled
no unsupported facts invented
```

## Acceptance criteria

- Audit-scoped BrandFact storage exists.
- `audit_id` required.
- Facts are conservative and source-labelled.
- Facts are stable snapshots for the audit.
- Task-scoped backend tests pass.
- Touched-file ruff passes.

## Escalate if

- Current data model has no stable audit-brand relationship.
- Product wants brand-scoped shared facts instead of audit snapshots.
- Fact regeneration policy is required now.

## Commands

```bash
pytest <brand facts tests>
ruff check <touched backend files>
```

## Done means

Evaluation can later load an immutable audit-scoped set of brand facts for each audit.
