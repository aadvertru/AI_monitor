"""Deterministic job scheduler for query x provider x run combinations."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from libs.storage.models import (
    Audit,
    AuditTarget,
    Job,
    JobStatus,
    Query,
    build_job_idempotency_key,
)


def schedule_jobs_for_audit(
    session: Session,
    audit_id: int,
    *,
    commit: bool = True,
) -> list[Job]:
    """Create missing scheduling jobs for an audit without executing them."""
    audit = session.get(Audit, audit_id)
    if audit is None:
        raise ValueError(f"Audit with id={audit_id} was not found.")

    query_stmt = select(Query).where(Query.audit_id == audit_id).order_by(Query.id)
    queries = session.execute(query_stmt).scalars().all()
    if audit.max_queries is not None:
        queries = queries[: audit.max_queries]

    if not queries:
        return []

    targets = _scheduling_targets(session, audit)
    if not targets:
        return []

    candidates: list[tuple[int, int | None, str, int, str]] = []
    for query in queries:
        for target_id, provider in targets:
            for run_number in range(1, audit.runs_per_query + 1):
                key = build_job_idempotency_key(
                    audit_id=audit_id,
                    query_id=query.id,
                    provider=provider,
                    run_number=run_number,
                    audit_target_id=target_id,
                )
                candidates.append((query.id, target_id, provider, run_number, key))

    candidate_keys = [item[4] for item in candidates]
    existing_keys_stmt = select(Job.idempotency_key).where(
        Job.audit_id == audit_id, Job.idempotency_key.in_(candidate_keys)
    )
    existing_keys = set(session.execute(existing_keys_stmt).scalars().all())

    created_jobs: list[Job] = []
    for query_id, target_id, provider, run_number, key in candidates:
        if key in existing_keys:
            continue
        job = Job(
            audit_id=audit_id,
            query_id=query_id,
            audit_target_id=target_id,
            provider=provider,
            run_number=run_number,
            status=JobStatus.PENDING,
            idempotency_key=key,
        )
        session.add(job)
        created_jobs.append(job)
        existing_keys.add(key)

    if commit:
        session.commit()
    else:
        session.flush()
    return created_jobs


def _scheduling_targets(session: Session, audit: Audit) -> Sequence[tuple[int | None, str]]:
    target_rows = (
        session.execute(
            select(AuditTarget)
            .where(AuditTarget.audit_id == audit.id)
            .order_by(AuditTarget.id)
        )
        .scalars()
        .all()
    )
    if target_rows:
        return [(target.id, target.execution_provider) for target in target_rows]
    return [(None, provider) for provider in audit.providers or []]
