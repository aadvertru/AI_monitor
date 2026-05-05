from __future__ import annotations

import unittest

from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session

from libs.control.job_scheduler import schedule_jobs_for_audit
from libs.storage.models import Audit, AuditTarget, Base, Brand, Job, JobStatus, Query


class JobSchedulerTests(unittest.TestCase):
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

    def _create_audit(
        self,
        *,
        providers: list[str],
        runs_per_query: int,
        query_texts: list[str],
        max_queries: int | None = None,
    ) -> Audit:
        brand = Brand(name=f"Acme AI {len(self.session.identity_map)}")
        audit = Audit(
            brand=brand,
            providers=providers,
            runs_per_query=runs_per_query,
            max_queries=max_queries,
        )
        self.session.add_all([brand, audit])
        self.session.flush()

        for text in query_texts:
            self.session.add(Query(audit_id=audit.id, text=text))

        self.session.commit()
        return audit

    def test_correct_combinations_are_created(self) -> None:
        audit = self._create_audit(
            providers=["openai", "mock"],
            runs_per_query=2,
            max_queries=2,
            query_texts=["q1", "q2", "q3"],
        )

        created = schedule_jobs_for_audit(self.session, audit.id)

        queries = (
            self.session.execute(
                select(Query).where(Query.audit_id == audit.id).order_by(Query.id)
            )
            .scalars()
            .all()
        )
        expected_keys = []
        for query in queries[:2]:
            for provider in ["openai", "mock"]:
                for run_number in (1, 2):
                    expected_keys.append(f"{audit.id}:{query.id}:{provider}:{run_number}")

        self.assertEqual(len(created), 8)
        self.assertEqual([job.idempotency_key for job in created], expected_keys)
        self.assertTrue(all(job.status == JobStatus.PENDING for job in created))

    def test_no_duplicate_jobs_are_created(self) -> None:
        audit = self._create_audit(
            providers=["openai", "openai"],
            runs_per_query=2,
            query_texts=["q1"],
        )

        created = schedule_jobs_for_audit(self.session, audit.id)

        self.assertEqual(len(created), 2)
        self.assertEqual(len({job.idempotency_key for job in created}), 2)

    def test_scheduler_handles_empty_queries_or_providers(self) -> None:
        audit_without_queries = self._create_audit(
            providers=["openai"],
            runs_per_query=2,
            query_texts=[],
        )
        self.assertEqual(schedule_jobs_for_audit(self.session, audit_without_queries.id), [])

        audit_without_providers = self._create_audit(
            providers=[],
            runs_per_query=2,
            query_texts=["q1"],
        )
        self.assertEqual(
            schedule_jobs_for_audit(self.session, audit_without_providers.id), []
        )

    def test_repeated_scheduling_does_not_create_uncontrolled_duplicates(self) -> None:
        audit = self._create_audit(
            providers=["openai", "mock"],
            runs_per_query=2,
            query_texts=["q1"],
        )

        first = schedule_jobs_for_audit(self.session, audit.id)
        second = schedule_jobs_for_audit(self.session, audit.id)

        persisted = (
            self.session.execute(select(Job).where(Job.audit_id == audit.id)).scalars().all()
        )

        self.assertEqual(len(first), 4)
        self.assertEqual(second, [])
        self.assertEqual(len(persisted), 4)

    def test_scheduler_expands_queries_by_audit_targets(self) -> None:
        audit = self._create_audit(
            providers=["openrouter"],
            runs_per_query=1,
            query_texts=["q1", "q2"],
        )
        targets = [
            AuditTarget(
                audit_id=audit.id,
                ai_family="chatgpt",
                execution_provider="openrouter",
                model_provider="openai",
                model_id="openai/gpt-4o-mini",
                display_name="GPT-4o mini",
                level="L1",
                gateway=True,
            ),
            AuditTarget(
                audit_id=audit.id,
                ai_family="claude",
                execution_provider="openrouter",
                model_provider="anthropic",
                model_id="anthropic/claude-3.5-sonnet",
                display_name="Claude 3.5 Sonnet",
                level="L1",
                gateway=True,
            ),
            AuditTarget(
                audit_id=audit.id,
                ai_family="chatgpt",
                execution_provider="openrouter",
                model_provider="openai",
                model_id="openai/gpt-4o-mini",
                display_name="GPT-4o mini L2",
                level="L2",
                gateway=True,
                gateway_l2_experimental=True,
            ),
        ]
        self.session.add_all(targets)
        self.session.commit()

        created = schedule_jobs_for_audit(self.session, audit.id)

        self.assertEqual(len(created), 6)
        self.assertEqual(
            {job.audit_target_id for job in created},
            {target.id for target in targets},
        )
        self.assertEqual({job.provider for job in created}, {"openrouter"})
        self.assertEqual(len({job.idempotency_key for job in created}), 6)

    def test_legacy_audit_without_targets_still_schedules_from_providers(self) -> None:
        audit = self._create_audit(
            providers=["mock"],
            runs_per_query=1,
            query_texts=["q1"],
        )

        created = schedule_jobs_for_audit(self.session, audit.id)

        self.assertEqual(len(created), 1)
        self.assertIsNone(created[0].audit_target_id)
        self.assertEqual(created[0].provider, "mock")


if __name__ == "__main__":
    unittest.main()
