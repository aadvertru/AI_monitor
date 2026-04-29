"""Deterministic job scheduler for query x provider x run combinations."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from libs.storage.models import (
    Audit,
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

    providers: Sequence[str] = audit.providers or []
    if not providers:
        return []

    query_stmt = select(Query).where(Query.audit_id == audit_id).order_by(Query.id)
    queries = session.execute(query_stmt).scalars().all()
    if audit.max_queries is not None:
        queries = queries[: audit.max_queries]

    if not queries:
        return []

    candidates: list[tuple[int, str, int, str]] = []
    for query in queries:
        for provider in providers:
            for run_number in range(1, audit.runs_per_query + 1):
                key = build_job_idempotency_key(
                    audit_id=audit_id,
                    query_id=query.id,
                    provider=provider,
                    run_number=run_number,
                )
                candidates.append((query.id, provider, run_number, key))

    candidate_keys = [item[3] for item in candidates]
    existing_keys_stmt = select(Job.idempotency_key).where(
        Job.audit_id == audit_id, Job.idempotency_key.in_(candidate_keys)
    )
    existing_keys = set(session.execute(existing_keys_stmt).scalars().all())

    created_jobs: list[Job] = []
    for query_id, provider, run_number, key in candidates:
        if key in existing_keys:
            continue
        job = Job(
            audit_id=audit_id,
            query_id=query_id,
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
