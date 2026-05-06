from __future__ import annotations

import unittest

from sqlalchemy import create_engine, event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from libs.storage.models import (
    Audit,
    AuditTarget,
    Base,
    Brand,
    CompetitorCandidate,
    Concept,
    Query,
    Run,
    SCDLLevel,
)


class ConceptsCompetitorsModelTests(unittest.TestCase):
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

    def test_concept_and_competitor_candidate_store_safe_evidence(self) -> None:
        audit, query, run, target = self._audit_with_run()
        concept = Concept(
            audit=audit,
            run=run,
            query=query,
            target=target,
            text="brand awareness",
            category="theme",
            count=2,
            evidence_count=1,
            evidence=[
                {
                    "query_id": query.id,
                    "run_id": run.id,
                    "target_id": target.id,
                    "answer_excerpt": "The answer mentions brand awareness.",
                    "level": "L1",
                    "model_id": "openai/gpt-4o-mini",
                    "execution_provider": "openrouter",
                }
            ],
        )
        candidate = CompetitorCandidate(
            audit=audit,
            name="Example Rival",
            domain="rival.example",
            confidence=0.75,
            evidence_type="comparison",
            evidence_count=1,
            evidence=[
                {
                    "query_id": query.id,
                    "run_id": run.id,
                    "target_id": target.id,
                    "answer_excerpt": "Example Rival is compared with the brand.",
                    "level": "L1",
                    "model_id": "openai/gpt-4o-mini",
                    "execution_provider": "openrouter",
                }
            ],
        )

        self.session.add_all([concept, candidate])
        self.session.commit()

        self.assertIsNotNone(concept.id)
        self.assertIsNotNone(candidate.id)
        self.assertEqual(audit.concepts[0].text, "brand awareness")
        self.assertEqual(audit.competitor_candidates[0].name, "Example Rival")
        self.assertEqual(concept.evidence[0]["query_id"], query.id)
        self.assertEqual(candidate.evidence[0]["execution_provider"], "openrouter")

    def test_empty_evidence_arrays_are_stable(self) -> None:
        audit, _query, _run, _target = self._audit_with_run()
        concept = Concept(
            audit=audit,
            text="pricing",
            count=0,
            evidence_count=0,
            evidence=[],
        )
        candidate = CompetitorCandidate(
            audit=audit,
            name="Example Rival",
            confidence=None,
            evidence_count=0,
            evidence=[],
        )

        self.session.add_all([concept, candidate])
        self.session.commit()

        self.assertEqual(concept.evidence, [])
        self.assertEqual(candidate.evidence, [])

    def test_competitor_candidate_rejects_confidence_outside_range(self) -> None:
        audit, _query, _run, _target = self._audit_with_run()
        self.session.add(
            CompetitorCandidate(
                audit=audit,
                name="Impossible Rival",
                confidence=1.5,
                evidence_count=0,
                evidence=[],
            )
        )

        with self.assertRaises(IntegrityError):
            self.session.commit()
        self.session.rollback()

    def test_audit_delete_cascades_without_deleting_shared_brand(self) -> None:
        audit, _query, _run, _target = self._audit_with_run()
        brand_id = audit.brand_id
        concept = Concept(audit=audit, text="support", count=1, evidence_count=0)
        candidate = CompetitorCandidate(
            audit=audit,
            name="Example Rival",
            confidence=0.6,
            evidence_count=0,
        )
        self.session.add_all([concept, candidate])
        self.session.commit()

        audit_id = audit.id
        self.session.delete(audit)
        self.session.commit()

        self.assertEqual(
            self.session.scalars(
                select(Concept).where(Concept.audit_id == audit_id)
            ).all(),
            [],
        )
        self.assertEqual(
            self.session.scalars(
                select(CompetitorCandidate).where(
                    CompetitorCandidate.audit_id == audit_id
                )
            ).all(),
            [],
        )
        self.assertIsNotNone(self.session.get(Brand, brand_id))

    def _audit_with_run(self) -> tuple[Audit, Query, Run, AuditTarget]:
        brand = Brand(name="Acme AI", domain="acme.ai")
        audit = Audit(brand=brand, providers=["openrouter"], runs_per_query=1)
        query = Query(audit=audit, text="best ai monitoring")
        target = AuditTarget(
            audit=audit,
            ai_family="chatgpt",
            execution_provider="openrouter",
            model_provider="openai",
            model_id="openai/gpt-4o-mini",
            display_name="GPT-4o mini",
            level=SCDLLevel.L1,
            gateway=True,
        )
        run = Run(
            audit=audit,
            query=query,
            audit_target=target,
            provider="openrouter",
            run_number=1,
        )
        self.session.add_all([brand, audit, query, target, run])
        self.session.commit()
        return audit, query, run, target
