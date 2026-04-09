from __future__ import annotations

import unittest

from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from libs.storage.models import (
    Audit,
    AuditStatus,
    Base,
    Brand,
    ParsedResult,
    Query,
    RawResponse,
    Run,
    RunStatus,
    Score,
)


class CoreModelsTests(unittest.TestCase):
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

    def test_entities_can_be_created_with_basic_relations(self) -> None:
        brand = Brand(
            name="Acme AI",
            domain="acme.ai",
            description="AI brand visibility platform.",
        )
        audit = Audit(
            brand=brand,
            providers=["openai"],
            runs_per_query=2,
            max_queries=20,
        )
        query = Query(audit=audit, text="best ai brand monitoring tools")
        run = Run(audit=audit, query=query, provider="openai", run_number=1)

        raw_response = RawResponse(
            run=run,
            request_snapshot={"prompt": "best ai brand monitoring tools"},
            raw_answer="Acme AI is one of the options.",
            citations=[{"url": "https://example.com"}],
            provider_metadata={"model": "gpt"},
            provider_status="success",
        )
        parsed_result = ParsedResult(
            run=run,
            visible_brand=True,
            brand_position_rank=1,
            prominence_score=0.9,
            sentiment=0.2,
            recommendation_score=0.8,
            source_quality_score=0.7,
            competitors=["other-ai"],
            sources=["https://example.com"],
            parsed_payload={"matched_brand": "Acme AI"},
        )
        score = Score(
            run=run,
            visibility_score=1.0,
            prominence_score=0.9,
            sentiment_score=0.2,
            recommendation_score=0.8,
            source_quality_score=0.7,
            final_score=0.85,
        )

        self.session.add_all(
            [brand, audit, query, run, raw_response, parsed_result, score]
        )
        self.session.commit()

        self.assertIsNotNone(brand.id)
        self.assertIsNotNone(audit.id)
        self.assertIsNotNone(query.id)
        self.assertIsNotNone(run.id)
        self.assertIsNotNone(raw_response.id)
        self.assertIsNotNone(parsed_result.id)
        self.assertIsNotNone(score.id)

        self.assertEqual(audit.status, AuditStatus.CREATED)
        self.assertEqual(run.status, RunStatus.PENDING)
        self.assertEqual(run.raw_response.run_id, run.id)
        self.assertEqual(run.parsed_result.run_id, run.id)
        self.assertEqual(run.score.run_id, run.id)
        self.assertEqual(query.audit_id, audit.id)
        self.assertEqual(run.query_id, query.id)
        self.assertEqual(run.audit_id, audit.id)

    def test_required_fields_and_relations_fail_predictably(self) -> None:
        invalid_brand = Brand(name=None)  # type: ignore[arg-type]
        self.session.add(invalid_brand)
        with self.assertRaises(IntegrityError):
            self.session.commit()
        self.session.rollback()

        brand = Brand(name="Acme AI")
        audit = Audit(brand=brand, providers=["openai"], runs_per_query=1)
        self.session.add_all([brand, audit])
        self.session.commit()

        invalid_run = Run(
            audit_id=audit.id,
            query_id=999999,
            provider="openai",
            run_number=1,
        )
        self.session.add(invalid_run)
        with self.assertRaises(IntegrityError):
            self.session.commit()
        self.session.rollback()


if __name__ == "__main__":
    unittest.main()

