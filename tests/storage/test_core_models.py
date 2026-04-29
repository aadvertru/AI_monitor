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
    User,
    UserRole,
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

    def test_duplicate_brand_name_is_rejected(self) -> None:
        first_brand = Brand(name="Acme AI")
        second_brand = Brand(name="Acme AI")

        self.session.add(first_brand)
        self.session.commit()

        self.session.add(second_brand)
        with self.assertRaises(IntegrityError):
            self.session.commit()
        self.session.rollback()

    def test_duplicate_run_execution_identity_is_rejected(self) -> None:
        brand = Brand(name="Acme AI")
        audit = Audit(brand=brand, providers=["openai"], runs_per_query=1)
        query = Query(audit=audit, text="best ai monitoring")
        self.session.add_all([brand, audit, query])
        self.session.commit()

        first_run = Run(
            audit_id=audit.id,
            query_id=query.id,
            provider="openai",
            run_number=1,
        )
        duplicate_run = Run(
            audit_id=audit.id,
            query_id=query.id,
            provider="openai",
            run_number=1,
        )

        self.session.add(first_run)
        self.session.commit()

        self.session.add(duplicate_run)
        with self.assertRaises(IntegrityError):
            self.session.commit()
        self.session.rollback()

    def test_user_can_be_created_with_required_auth_fields(self) -> None:
        user = User(
            email="user@example.com",
            hashed_password="hashed-password-value",
        )

        self.session.add(user)
        self.session.commit()

        self.assertIsNotNone(user.id)
        self.assertEqual(user.email, "user@example.com")
        self.assertEqual(user.hashed_password, "hashed-password-value")
        self.assertEqual(user.role, UserRole.USER)
        self.assertIsNotNone(user.created_at)
        self.assertIsNotNone(user.updated_at)

    def test_duplicate_user_email_is_rejected(self) -> None:
        first_user = User(
            email="user@example.com",
            hashed_password="first-hash",
        )
        duplicate_user = User(
            email="user@example.com",
            hashed_password="second-hash",
        )

        self.session.add(first_user)
        self.session.commit()

        self.session.add(duplicate_user)
        with self.assertRaises(IntegrityError):
            self.session.commit()
        self.session.rollback()

    def test_user_can_own_multiple_audits(self) -> None:
        user = User(email="owner@example.com", hashed_password="hash")
        first_brand = Brand(name="Acme AI")
        second_brand = Brand(name="Example CRM")
        first_audit = Audit(
            user=user,
            brand=first_brand,
            providers=["openai"],
            runs_per_query=1,
        )
        second_audit = Audit(
            user=user,
            brand=second_brand,
            providers=["mock"],
            runs_per_query=2,
        )

        self.session.add_all(
            [user, first_brand, second_brand, first_audit, second_audit]
        )
        self.session.commit()

        self.assertEqual(first_audit.user_id, user.id)
        self.assertEqual(second_audit.user_id, user.id)
        self.assertEqual(
            [audit.id for audit in user.audits],
            [first_audit.id, second_audit.id],
        )

    def test_audits_can_be_queried_by_owner(self) -> None:
        owner = User(email="owner@example.com", hashed_password="hash")
        other_user = User(email="other@example.com", hashed_password="hash")
        owned_brand = Brand(name="Acme AI")
        other_brand = Brand(name="Other AI")
        owned_audit = Audit(
            user=owner,
            brand=owned_brand,
            providers=["openai"],
            runs_per_query=1,
        )
        other_audit = Audit(
            user=other_user,
            brand=other_brand,
            providers=["mock"],
            runs_per_query=1,
        )

        self.session.add_all(
            [owner, other_user, owned_brand, other_brand, owned_audit, other_audit]
        )
        self.session.commit()

        owned_audits = (
            self.session.query(Audit)
            .filter(Audit.user_id == owner.id)
            .order_by(Audit.id)
            .all()
        )

        self.assertEqual(owned_audits, [owned_audit])

    def test_audit_can_still_be_created_without_owner_for_compatibility(self) -> None:
        brand = Brand(name="Acme AI")
        audit = Audit(brand=brand, providers=["openai"], runs_per_query=1)

        self.session.add_all([brand, audit])
        self.session.commit()

        self.assertIsNotNone(audit.id)
        self.assertIsNone(audit.user_id)


if __name__ == "__main__":
    unittest.main()
