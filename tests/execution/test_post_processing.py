from __future__ import annotations

import unittest
from unittest.mock import patch

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from apps.api.main import build_audit_results_response, build_audit_summary_response
from libs.execution.post_processing import process_audit_results
from libs.execution.provider_adapter import ProviderResponse
from libs.storage.models import (
    Audit,
    AuditStatus,
    Base,
    Brand,
    CompetitorCandidate,
    Concept,
    ParsedResult,
    Query,
    RawResponse,
    Run,
    RunStatus,
    Score,
)


class AuditPostProcessingTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        self.session: AsyncSession = self.session_factory()

    async def asyncTearDown(self) -> None:
        await self.session.close()
        await self.engine.dispose()

    async def _create_audit(
        self,
        *,
        brand_name: str = "Acme AI",
        brand_domain: str | None = "acme.ai",
        providers: list[str] | None = None,
        query_texts: list[str] | None = None,
        runs_per_query: int = 1,
        status: AuditStatus = AuditStatus.RUNNING,
    ) -> Audit:
        brand = Brand(name=brand_name, domain=brand_domain)
        audit = Audit(
            brand=brand,
            providers=providers or ["openai"],
            runs_per_query=runs_per_query,
            status=status,
        )
        self.session.add(audit)
        await self.session.flush()
        for query_text in query_texts or ["best ai monitoring tools"]:
            self.session.add(Query(audit_id=audit.id, text=query_text))
        await self.session.commit()
        await self.session.refresh(audit)
        return audit

    async def _add_run(
        self,
        audit: Audit,
        *,
        query_index: int = 0,
        provider: str | None = None,
        run_number: int = 1,
        status: RunStatus = RunStatus.SUCCESS,
        raw_answer: str | None = "Acme AI is recommended. Beta Labs is another vendor.",
        citations: list[dict] | None = None,
        provider_status: str = "success",
        parsed: bool = False,
        scored: bool = False,
        parsed_competitors: list[object] | None = None,
    ) -> Run:
        queries = (
            await self.session.execute(
                select(Query).where(Query.audit_id == audit.id).order_by(Query.id)
            )
        ).scalars().all()
        run = Run(
            audit_id=audit.id,
            query_id=queries[query_index].id,
            provider=provider or (audit.providers or ["openai"])[0],
            run_number=run_number,
            status=status,
        )
        self.session.add(run)
        await self.session.flush()

        if raw_answer is not None or provider_status != "missing":
            self.session.add(
                RawResponse(
                    run_id=run.id,
                    request_snapshot={
                        "query": queries[query_index].text,
                        "provider": run.provider,
                    },
                    raw_answer=raw_answer,
                    citations=citations if citations is not None else [],
                    provider_metadata={"model": "test-model"},
                    provider_status=provider_status,
                    response_time=0.2,
                    error_object=(
                        None
                        if status == RunStatus.SUCCESS
                        else {"code": "provider_error", "message": "Provider failed."}
                    ),
                )
            )

        if parsed:
            self.session.add(
                ParsedResult(
                    run_id=run.id,
                    visible_brand=True,
                    brand_position_rank=1,
                    prominence_score=0.8,
                    sentiment=1.0,
                    recommendation_score=1.0,
                    source_quality_score=0.0,
                    competitors=parsed_competitors or [],
                    sources=[],
                    parsed_payload={"match_type": "exact"},
                )
            )
        if scored:
            self.session.add(
                Score(
                    run_id=run.id,
                    visibility_score=1.0,
                    prominence_score=0.8,
                    sentiment_score=1.0,
                    recommendation_score=1.0,
                    source_quality_score=0.0,
                    final_score=0.8,
                )
            )

        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def test_successful_post_processing_persists_legacy_concepts(self) -> None:
        audit = await self._create_audit()
        await self._add_run(
            audit,
            raw_answer="Acme AI is discussed alongside category concepts.",
            parsed=True,
            scored=True,
            parsed_competitors=["brand visibility", {"name": "answer monitoring"}],
        )

        await process_audit_results(self.session, audit.id)

        concepts = (
            await self.session.execute(
                select(Concept).where(Concept.audit_id == audit.id).order_by(Concept.text)
            )
        ).scalars().all()
        self.assertEqual(
            [(concept.text, concept.category, concept.count) for concept in concepts],
            [
                ("answer monitoring", "legacy_phrase", 1),
                ("brand visibility", "legacy_phrase", 1),
            ],
        )
        self.assertEqual(concepts[0].evidence_count, 1)
        self.assertEqual(concepts[0].evidence[0]["execution_provider"], "openai")

    async def test_successful_post_processing_persists_competitor_candidate(
        self,
    ) -> None:
        audit = await self._create_audit(
            brand_name="Acme AI",
            query_texts=["alternatives to Acme AI"],
        )
        await self._add_run(
            audit,
            raw_answer="Alternatives to Acme AI include Beta Labs and GammaSoft.",
            parsed=True,
            scored=True,
        )

        await process_audit_results(self.session, audit.id)

        candidates = (
            await self.session.execute(
                select(CompetitorCandidate)
                .where(CompetitorCandidate.audit_id == audit.id)
                .order_by(CompetitorCandidate.name)
            )
        ).scalars().all()
        self.assertEqual([candidate.name for candidate in candidates], ["Beta Labs", "GammaSoft"])
        self.assertEqual(candidates[0].confidence, 0.7)
        self.assertEqual(candidates[0].evidence_count, 1)
        self.assertEqual(candidates[0].evidence[0]["matched_phrase"], "Beta Labs")

    async def test_post_processing_concept_and_candidate_rebuild_is_idempotent(
        self,
    ) -> None:
        audit = await self._create_audit(query_texts=["alternatives to Acme AI"])
        await self._add_run(
            audit,
            raw_answer="Alternatives to Acme AI include Beta Labs.",
            parsed=True,
            scored=True,
            parsed_competitors=["brand visibility"],
        )

        await process_audit_results(self.session, audit.id)
        await process_audit_results(self.session, audit.id)

        concept_count = (
            await self.session.execute(
                select(func.count()).select_from(Concept).where(Concept.audit_id == audit.id)
            )
        ).scalar_one()
        candidate_count = (
            await self.session.execute(
                select(func.count())
                .select_from(CompetitorCandidate)
                .where(CompetitorCandidate.audit_id == audit.id)
            )
        ).scalar_one()
        self.assertEqual(concept_count, 1)
        self.assertEqual(candidate_count, 1)

    async def test_competitor_candidate_evidence_merges_across_runs(self) -> None:
        audit = await self._create_audit(query_texts=["alternatives to Acme AI"])
        await self._add_run(
            audit,
            raw_answer="Alternatives to Acme AI include Beta Labs.",
            parsed=True,
            scored=True,
        )
        await self._add_run(
            audit,
            run_number=2,
            raw_answer="Teams also compare Acme AI with Beta Labs.",
            parsed=True,
            scored=True,
        )

        await process_audit_results(self.session, audit.id)

        candidate = (
            await self.session.execute(
                select(CompetitorCandidate).where(
                    CompetitorCandidate.audit_id == audit.id,
                    CompetitorCandidate.name == "Beta Labs",
                )
            )
        ).scalar_one()
        self.assertEqual(candidate.evidence_count, 2)
        self.assertEqual(len(candidate.evidence), 2)

    async def test_failed_and_no_answer_runs_do_not_create_concepts_or_candidates(
        self,
    ) -> None:
        audit = await self._create_audit(query_texts=["alternatives to Acme AI"])
        await self._add_run(
            audit,
            status=RunStatus.ERROR,
            raw_answer=None,
            provider_status="error",
        )
        await self._add_run(
            audit,
            run_number=2,
            raw_answer=None,
            provider_status="missing",
        )

        await process_audit_results(self.session, audit.id)

        concept_count = (
            await self.session.execute(
                select(func.count()).select_from(Concept).where(Concept.audit_id == audit.id)
            )
        ).scalar_one()
        candidate_count = (
            await self.session.execute(
                select(func.count())
                .select_from(CompetitorCandidate)
                .where(CompetitorCandidate.audit_id == audit.id)
            )
        ).scalar_one()
        self.assertEqual(concept_count, 0)
        self.assertEqual(candidate_count, 0)

    async def test_processes_successful_stored_raw_response_into_parsed_result_and_score(
        self,
    ) -> None:
        audit = await self._create_audit()
        run = await self._add_run(audit)

        summary = await process_audit_results(self.session, audit.id)

        parsed_result = (
            await self.session.execute(
                select(ParsedResult).where(ParsedResult.run_id == run.id)
            )
        ).scalar_one()
        score = (
            await self.session.execute(select(Score).where(Score.run_id == run.id))
        ).scalar_one()
        saved_audit = await self.session.get(Audit, audit.id)
        assert saved_audit is not None
        self.assertEqual(summary.total_runs_inspected, 1)
        self.assertEqual(summary.runs_processed, 1)
        self.assertEqual(summary.audit_status, "completed")
        self.assertTrue(parsed_result.visible_brand)
        self.assertEqual(parsed_result.brand_position_rank, 1)
        self.assertGreater(score.final_score, 0.0)
        self.assertEqual(saved_audit.status, AuditStatus.COMPLETED)

    async def test_results_and_summary_endpoints_reflect_saved_post_processing(
        self,
    ) -> None:
        audit = await self._create_audit()
        await self._add_run(
            audit,
            citations=[
                {
                    "url": "https://www.wikipedia.org/wiki/Acme_AI",
                    "title": "Acme AI",
                }
            ],
        )

        await process_audit_results(self.session, audit.id)
        saved_audit = await self.session.get(Audit, audit.id)
        assert saved_audit is not None
        results = await build_audit_results_response(self.session, saved_audit)
        summary = await build_audit_summary_response(self.session, saved_audit)

        self.assertEqual(results.total, 1)
        self.assertTrue(results.rows[0].visible_brand)
        self.assertIsNotNone(results.rows[0].final_score)
        self.assertEqual(summary.status, "completed")
        self.assertEqual(summary.total_runs, 1)
        self.assertEqual(summary.successful_runs, 1)
        self.assertEqual(summary.visibility_ratio, 1.0)
        self.assertIsNotNone(summary.average_score)

    async def test_missing_raw_response_is_skipped_and_marks_audit_partial(self) -> None:
        audit = await self._create_audit()
        await self._add_run(audit, raw_answer=None, provider_status="missing")

        summary = await process_audit_results(self.session, audit.id)
        saved_audit = await self.session.get(Audit, audit.id)
        assert saved_audit is not None
        self.assertEqual(summary.runs_processed, 0)
        self.assertEqual(summary.skipped_missing_raw_response, 1)
        self.assertEqual(saved_audit.status, AuditStatus.PARTIAL)

    async def test_non_successful_run_is_skipped_and_marks_audit_partial(self) -> None:
        audit = await self._create_audit()
        await self._add_run(
            audit,
            status=RunStatus.ERROR,
            raw_answer=None,
            provider_status="error",
        )

        summary = await process_audit_results(self.session, audit.id)
        saved_audit = await self.session.get(Audit, audit.id)
        assert saved_audit is not None
        self.assertEqual(summary.skipped_non_successful_run, 1)
        self.assertEqual(summary.runs_processed, 0)
        self.assertEqual(saved_audit.status, AuditStatus.PARTIAL)

    async def test_pending_expected_runs_keep_audit_running_after_success_processing(
        self,
    ) -> None:
        audit = await self._create_audit(query_texts=["one", "two"])
        await self._add_run(audit, query_index=0, status=RunStatus.SUCCESS)
        await self._add_run(
            audit,
            query_index=1,
            status=RunStatus.PENDING,
            raw_answer=None,
            provider_status="missing",
            run_number=1,
        )

        summary = await process_audit_results(self.session, audit.id)
        saved_audit = await self.session.get(Audit, audit.id)
        assert saved_audit is not None
        self.assertEqual(summary.runs_processed, 1)
        self.assertEqual(summary.skipped_non_successful_run, 1)
        self.assertEqual(saved_audit.status, AuditStatus.RUNNING)

    async def test_parser_miss_does_not_mark_audit_failed(self) -> None:
        audit = await self._create_audit()
        run = await self._add_run(
            audit,
            raw_answer="This response discusses dashboards but does not mention the brand.",
        )

        summary = await process_audit_results(self.session, audit.id)
        parsed_result = (
            await self.session.execute(
                select(ParsedResult).where(ParsedResult.run_id == run.id)
            )
        ).scalar_one()
        score = (
            await self.session.execute(select(Score).where(Score.run_id == run.id))
        ).scalar_one()
        saved_audit = await self.session.get(Audit, audit.id)
        assert saved_audit is not None
        self.assertFalse(parsed_result.visible_brand)
        self.assertEqual(score.final_score, 0.0)
        self.assertEqual(summary.audit_status, "completed")
        self.assertEqual(saved_audit.status, AuditStatus.COMPLETED)

    async def test_stored_raw_response_is_adapted_into_provider_response_contract(
        self,
    ) -> None:
        audit = await self._create_audit(brand_name="Stored Brand", brand_domain="stored.test")
        await self._add_run(
            audit,
            raw_answer="Stored Brand appears in the stored answer.",
            citations=[{"url": "https://stored.test/source", "title": "Stored"}],
        )
        captured: dict[str, object] = {}

        def fake_parse(
            brand_name: str,
            brand_domain: str | None,
            query: str,
            provider_response: ProviderResponse,
        ) -> dict:
            captured["brand_name"] = brand_name
            captured["brand_domain"] = brand_domain
            captured["query"] = query
            captured["provider_response"] = provider_response
            return {
                "visible_brand": True,
                "brand_position_rank": 1,
                "prominence_score": 1.0,
                "sentiment": 0.0,
                "recommendation_score": 0.0,
                "source_quality_score": 0.0,
                "competitors": [],
                "sources": [],
                "parsed_payload": {"match_type": "test"},
            }

        with patch("libs.execution.post_processing.parser.parse", side_effect=fake_parse):
            await process_audit_results(self.session, audit.id)

        provider_response = captured["provider_response"]
        assert isinstance(provider_response, ProviderResponse)
        self.assertEqual(captured["brand_name"], "Stored Brand")
        self.assertEqual(captured["brand_domain"], "stored.test")
        self.assertEqual(captured["query"], "best ai monitoring tools")
        self.assertEqual(provider_response.status, "success")
        self.assertEqual(
            provider_response.raw_answer,
            "Stored Brand appears in the stored answer.",
        )
        self.assertEqual(provider_response.citations[0]["url"], "https://stored.test/source")
        self.assertEqual(provider_response.provider_metadata, {"model": "test-model"})

    async def test_idempotent_rerun_does_not_duplicate_parsed_results_or_scores(
        self,
    ) -> None:
        audit = await self._create_audit()
        await self._add_run(audit)

        first_summary = await process_audit_results(self.session, audit.id)
        second_summary = await process_audit_results(self.session, audit.id)

        parsed_count = (
            await self.session.execute(select(func.count()).select_from(ParsedResult))
        ).scalar_one()
        score_count = (
            await self.session.execute(select(func.count()).select_from(Score))
        ).scalar_one()
        self.assertEqual(first_summary.runs_processed, 1)
        self.assertEqual(second_summary.runs_processed, 0)
        self.assertEqual(second_summary.skipped_already_processed, 1)
        self.assertEqual(parsed_count, 1)
        self.assertEqual(score_count, 1)

    async def test_existing_parsed_result_without_score_creates_missing_score_only(
        self,
    ) -> None:
        audit = await self._create_audit()
        await self._add_run(audit, parsed=True, scored=False)

        summary = await process_audit_results(self.session, audit.id)

        parsed_count = (
            await self.session.execute(select(func.count()).select_from(ParsedResult))
        ).scalar_one()
        score_count = (
            await self.session.execute(select(func.count()).select_from(Score))
        ).scalar_one()
        self.assertEqual(summary.runs_processed, 1)
        self.assertEqual(parsed_count, 1)
        self.assertEqual(score_count, 1)

    async def test_missing_audit_returns_fatal_summary(self) -> None:
        summary = await process_audit_results(self.session, 404)

        self.assertEqual(summary.audit_id, 404)
        self.assertIn("was not found", summary.fatal_error or "")
        self.assertEqual(summary.total_runs_inspected, 0)

    async def test_post_processing_does_not_call_provider_adapters(self) -> None:
        audit = await self._create_audit()
        await self._add_run(audit)

        with patch(
            "libs.execution.openai_provider.OpenAIProviderAdapter.query",
            side_effect=AssertionError("provider should not be called"),
        ) as provider_mock:
            summary = await process_audit_results(self.session, audit.id)

        self.assertEqual(summary.runs_processed, 1)
        provider_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
