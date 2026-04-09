from __future__ import annotations

import unittest

from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from libs.storage.models import (
    Audit,
    Base,
    Brand,
    Job,
    JobStatus,
    Query,
    build_job_idempotency_key,
)


class JobModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:", future=True)

        @event.listens_for(self.engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        Base.metadata.create_all(self.engine)
        self.session = Session(bind=self.engine)

    def tearDown(self) -> None:
        self.session.close()
        self.engine.dispose()

    def _create_audit_and_query(self) -> tuple[Audit, Query]:
        brand = Brand(name="Acme AI")
        audit = Audit(brand=brand, providers=["openai"], runs_per_query=1)
        query = Query(audit=audit, text="best ai monitoring tools")
        self.session.add_all([brand, audit, query])
        self.session.commit()
        return audit, query

    def test_job_can_be_created_with_required_fields(self) -> None:
        audit, query = self._create_audit_and_query()
        idempotency_key = build_job_idempotency_key(audit.id, query.id, "openai", 1)

        job = Job(
            audit_id=audit.id,
            query_id=query.id,
            provider="openai",
            run_number=1,
            status=JobStatus.PENDING,
            idempotency_key=idempotency_key,
        )
        self.session.add(job)
        self.session.commit()

        self.assertIsNotNone(job.id)
        self.assertEqual(job.status, JobStatus.PENDING)
        self.assertEqual(job.idempotency_key, f"{audit.id}:{query.id}:openai:1")

    def test_duplicate_idempotency_key_is_rejected(self) -> None:
        audit, query = self._create_audit_and_query()
        idempotency_key = build_job_idempotency_key(audit.id, query.id, "openai", 1)

        first = Job(
            audit_id=audit.id,
            query_id=query.id,
            provider="openai",
            run_number=1,
            status=JobStatus.PENDING,
            idempotency_key=idempotency_key,
        )
        second = Job(
            audit_id=audit.id,
            query_id=query.id,
            provider="openai",
            run_number=1,
            status=JobStatus.PENDING,
            idempotency_key=idempotency_key,
        )

        self.session.add(first)
        self.session.commit()

        self.session.add(second)
        with self.assertRaises(IntegrityError):
            self.session.commit()
        self.session.rollback()

    def test_idempotency_key_is_stable_for_same_inputs(self) -> None:
        first = build_job_idempotency_key(10, 20, "openai", 3)
        second = build_job_idempotency_key(10, 20, "openai", 3)

        self.assertEqual(first, second)
        self.assertEqual(first, "10:20:openai:3")


if __name__ == "__main__":
    unittest.main()

