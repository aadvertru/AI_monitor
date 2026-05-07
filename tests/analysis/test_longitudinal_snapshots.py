from __future__ import annotations

import unittest

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from libs.analysis.longitudinal_snapshots import (
    create_audit_metrics_snapshot,
    normalize_brand_name,
    normalize_domain,
)
from libs.storage.models import (
    AnswerEvaluation,
    AnswerEvaluationVerdict,
    Audit,
    AuditMetricsSnapshot,
    AuditStatus,
    AuditTarget,
    Base,
    Brand,
    CompetitorCandidate,
    Concept,
    ParsedResult,
    Query,
    RawResponse,
    Run,
    RunStatus,
    SCDLLevel,
    Score,
    User,
)


class LongitudinalSnapshotTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        self.session: AsyncSession = self.session_factory()

    async def asyncTearDown(self) -> None:
        await self.session.close()
        await self.engine.dispose()

    async def _audit(
        self,
        *,
        status: AuditStatus = AuditStatus.COMPLETED,
        brand_name: str = "Acme AI",
        domain: str | None = "https://www.acme.example/",
    ) -> tuple[Audit, Query, AuditTarget]:
        user = User(
            email=f"{brand_name.lower().replace(' ', '')}@example.com",
            hashed_password="hash",
        )
        brand = Brand(name=brand_name, domain=domain)
        audit = Audit(
            brand=brand,
            user=user,
            providers=["openrouter"],
            runs_per_query=1,
            scdl_level=SCDLLevel.L1,
            status=status,
        )
        query = Query(audit=audit, text="best tools")
        target = AuditTarget(
            audit=audit,
            ai_family="google",
            execution_provider="openrouter",
            model_provider="google",
            model_id="google/gemini-2.0-flash-001",
            display_name="Gemini Flash",
            level=SCDLLevel.L1,
            gateway=True,
        )
        self.session.add_all([user, brand, audit, query, target])
        await self.session.flush()
        return audit, query, target

    async def _successful_run(
        self,
        audit: Audit,
        query: Query,
        target: AuditTarget,
        *,
        visible: bool = True,
    ) -> Run:
        run = Run(
            audit_id=audit.id,
            query_id=query.id,
            audit_target_id=target.id,
            provider="openrouter",
            run_number=1,
            status=RunStatus.SUCCESS,
        )
        self.session.add(run)
        await self.session.flush()
        self.session.add_all(
            [
                ParsedResult(
                    run_id=run.id,
                    visible_brand=visible,
                    competitors=[],
                    sources=[{"domain": "example.com", "url": "https://example.com/a"}],
                    parsed_payload={"raw_prompt": "do not leak"},
                ),
                Score(run_id=run.id, final_score=0.8),
                RawResponse(
                    run_id=run.id,
                    request_snapshot={"raw_prompt": "secret"},
                    raw_answer="raw answer",
                    citations=[],
                    provider_metadata={
                        "parser_version": "parser-v1",
                        "scoring_version": "score-v1",
                        "api_key": "sk-hidden",
                    },
                    provider_status="success",
                ),
                AnswerEvaluation(
                    audit_id=audit.id,
                    run_id=run.id,
                    query_id=query.id,
                    target_id=target.id,
                    verdict=AnswerEvaluationVerdict.CORRECT,
                    evaluation_version="eval-v1",
                ),
                Concept(
                    audit_id=audit.id,
                    run_id=run.id,
                    query_id=query.id,
                    target_id=target.id,
                    text="Visibility",
                    count=2,
                    evidence_count=1,
                ),
                CompetitorCandidate(
                    audit_id=audit.id,
                    name="Rival",
                    confidence=0.8,
                    evidence_count=1,
                ),
            ]
        )
        await self.session.commit()
        return run

    async def test_snapshot_created_for_completed_audit_without_raw_data(self) -> None:
        audit, query, target = await self._audit()
        await self._successful_run(audit, query, target)

        result = await create_audit_metrics_snapshot(self.session, audit.id)

        assert result.snapshot is not None
        snapshot = result.snapshot
        self.assertEqual(snapshot.snapshot_version, 1)
        self.assertEqual(snapshot.normalized_domain, "acme.example")
        self.assertEqual(snapshot.normalized_brand_name, "acme ai")
        self.assertEqual(snapshot.summary_metrics["mentionability_l1"], 100.0)
        self.assertEqual(snapshot.summary_metrics["accuracy_l1"], 1.0)
        self.assertEqual(snapshot.parser_version, "parser-v1")
        self.assertEqual(snapshot.scoring_version, "score-v1")
        self.assertEqual(snapshot.evaluation_version, "eval-v1")
        dumped = str(snapshot.summary_metrics) + str(snapshot.model_summaries)
        dumped += str(snapshot.source_domains_summary)
        self.assertNotIn("raw_prompt", dumped)
        self.assertNotIn("raw answer", dumped)
        self.assertNotIn("sk-hidden", dumped)

    async def test_snapshot_created_for_cancelled_audit_with_usable_data(self) -> None:
        audit, query, target = await self._audit(status=AuditStatus.CANCELLED)
        await self._successful_run(audit, query, target)

        result = await create_audit_metrics_snapshot(self.session, audit.id)

        assert result.snapshot is not None
        self.assertEqual(result.snapshot.audit_status, AuditStatus.CANCELLED)

    async def test_no_snapshot_for_failed_audit_without_usable_data(self) -> None:
        audit, _query, _target = await self._audit(status=AuditStatus.FAILED)
        await self.session.commit()

        result = await create_audit_metrics_snapshot(self.session, audit.id)

        self.assertIsNone(result.snapshot)
        self.assertEqual(result.skipped_reason, "no_usable_data")

    async def test_snapshot_versions_are_immutable(self) -> None:
        audit, query, target = await self._audit()
        await self._successful_run(audit, query, target)
        first = await create_audit_metrics_snapshot(self.session, audit.id)
        second = await create_audit_metrics_snapshot(
            self.session,
            audit.id,
            force_new_version=True,
        )

        assert first.snapshot is not None
        assert second.snapshot is not None
        self.assertEqual(first.snapshot.snapshot_version, 1)
        self.assertEqual(second.snapshot.snapshot_version, 2)
        snapshots = (
            await self.session.execute(select(AuditMetricsSnapshot))
        ).scalars().all()
        self.assertEqual(len(snapshots), 2)

    def test_normalizers_are_safe(self) -> None:
        self.assertEqual(normalize_domain(" https://www.Example.com/path "), "example.com")
        self.assertEqual(normalize_brand_name("  Acme   AI "), "acme ai")
