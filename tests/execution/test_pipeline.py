from __future__ import annotations

import logging
import unittest
from unittest.mock import patch

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from apps.api.main import build_audit_results_response, build_audit_summary_response
from libs.execution.audit_execution import AuditJobExecutionSummary, execute_audit_jobs
from libs.execution.openrouter_config import OpenRouterProviderConfig
from libs.execution.openrouter_provider import OpenRouterProviderAdapter
from libs.execution.pilot_config import RealProviderPilotConfig
from libs.execution.pipeline import run_audit_pipeline
from libs.execution.post_processing import AuditPostProcessingSummary, process_audit_results
from libs.execution.provider_adapter import BaseProviderAdapter, ProviderResponse
from libs.storage.models import (
    Audit,
    AuditMetricsSnapshot,
    AuditStatus,
    Base,
    Brand,
    Job,
    ParsedResult,
    Query,
    RawResponse,
    SCDLLevel,
    Score,
)


class _QueryAwareProvider(BaseProviderAdapter):
    def __init__(self, *, brand_name: str = "Acme AI") -> None:
        self.brand_name = brand_name
        self.calls: list[str] = []

    async def query(self, query: str, **kwargs) -> ProviderResponse:
        self.calls.append(query)
        if "error" in query:
            return ProviderResponse(
                status="error",
                raw_answer=None,
                citations=None,
                response_time=0.2,
                error={"code": "mock_error", "message": "Provider failed."},
                provider_metadata={"provider": "mock"},
            )
        if "missing" in query:
            answer = "This answer discusses dashboards without naming the target brand."
        else:
            answer = f"{self.brand_name} is a recommended visibility platform."
        return ProviderResponse(
            status="success",
            raw_answer=answer,
            citations=[],
            response_time=0.1,
            error=None,
            provider_metadata={"provider": "mock"},
        )


class _OpenRouterLikeProvider(BaseProviderAdapter):
    async def query(self, query: str, **kwargs) -> ProviderResponse:
        return ProviderResponse(
            status="success",
            raw_answer="Acme AI is a recommended visibility platform.",
            citations=[],
            response_time=0.123,
            error=None,
            provider_metadata={
                "provider": "openrouter",
                "execution_provider": "openrouter",
                "model_id": "anthropic/claude-3.5-sonnet",
                "model_provider": "anthropic",
                "gateway": True,
                "gateway_l2_experimental": kwargs.get("scdl_level") == "L2",
                "level": kwargs.get("scdl_level"),
                "usage": {
                    "input_tokens": 11,
                    "output_tokens": 22,
                    "total_tokens": 33,
                },
            },
        )


class _UnsafeRaisingProvider(BaseProviderAdapter):
    async def query(self, query: str, **kwargs) -> ProviderResponse:
        raise RuntimeError(
            "sk-or-secret OPENROUTER_API_KEY authorization headers raw_prompt "
            "raw_response traceback Bearer"
        )


class _OpenRouterAdapterLikeProvider(OpenRouterProviderAdapter):
    """Real OpenRouterProviderAdapter subclass with a stubbed query() for pipeline tests."""

    def __init__(self) -> None:
        super().__init__(
            config=OpenRouterProviderConfig(
                model_l1="google/gemini-2.0-flash-001",
                model_l2="anthropic/claude-3.5-sonnet",
            )
        )

    async def query(self, query: str, **kwargs) -> ProviderResponse:
        return ProviderResponse(
            status="success",
            raw_answer="Acme AI is a recommended visibility platform.",
            citations=[],
            response_time=0.123,
            error=None,
            provider_metadata={
                "provider": "openrouter",
                "execution_provider": "openrouter",
                "model_id": "anthropic/claude-3.5-sonnet",
                "model_provider": "anthropic",
                "gateway": True,
                "gateway_l2_experimental": kwargs.get("scdl_level") == "L2",
                "level": kwargs.get("scdl_level"),
                "usage": {
                    "input_tokens": 11,
                    "output_tokens": 22,
                    "total_tokens": 33,
                },
            },
        )


class _ListHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


class AuditPipelineTests(unittest.IsolatedAsyncioTestCase):
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
        providers: list[str] | None = None,
        query_texts: list[str] | None = None,
        status: AuditStatus = AuditStatus.CREATED,
        scdl_level: SCDLLevel = SCDLLevel.L1,
    ) -> Audit:
        brand = Brand(name=brand_name, domain="acme.ai")
        audit = Audit(
            brand=brand,
            providers=providers or ["mock"],
            runs_per_query=1,
            scdl_level=scdl_level,
            status=status,
        )
        self.session.add(audit)
        await self.session.flush()
        for query_text in query_texts or ["visible query"]:
            self.session.add(Query(audit_id=audit.id, text=query_text))
        await self.session.commit()
        await self.session.refresh(audit)
        return audit

    async def test_full_pipeline_completes_mock_audit_and_updates_api_views(self) -> None:
        audit = await self._create_audit()
        provider = _QueryAwareProvider()

        summary = await run_audit_pipeline(
            self.session,
            audit.id,
            provider_factory=lambda _provider: provider,
        )

        saved_audit = await self.session.get(Audit, audit.id)
        assert saved_audit is not None
        results = await build_audit_results_response(self.session, saved_audit)
        api_summary = await build_audit_summary_response(self.session, saved_audit)
        self.assertEqual(summary.scheduling.scheduled_jobs, 1)
        assert summary.execution is not None
        self.assertEqual(summary.execution.jobs_executed, 1)
        assert summary.post_processing is not None
        self.assertEqual(summary.post_processing.runs_processed, 1)
        self.assertEqual(summary.final_audit_status, "completed")
        self.assertEqual(saved_audit.status, AuditStatus.COMPLETED)
        self.assertEqual(results.total, 1)
        self.assertTrue(results.rows[0].visible_brand)
        self.assertIsNotNone(results.rows[0].final_score)
        self.assertEqual(api_summary.visibility_ratio, 1.0)
        snapshot_count = await self._count(AuditMetricsSnapshot)
        self.assertEqual(snapshot_count, 1)

    async def test_pipeline_sets_status_to_running_before_execution(self) -> None:
        audit = await self._create_audit()
        observed_status: list[AuditStatus] = []

        async def fake_execution(
            session: AsyncSession,
            audit_id: int,
            **_kwargs,
        ) -> AuditJobExecutionSummary:
            saved_audit = await session.get(Audit, audit_id)
            assert saved_audit is not None
            observed_status.append(saved_audit.status)
            return AuditJobExecutionSummary(audit_id=audit_id)

        async def fake_post_processing(
            _session: AsyncSession,
            audit_id: int,
        ) -> AuditPostProcessingSummary:
            return AuditPostProcessingSummary(audit_id=audit_id)

        with (
            patch("libs.execution.pipeline.execute_audit_jobs", side_effect=fake_execution),
            patch(
                "libs.execution.pipeline.process_audit_results",
                side_effect=fake_post_processing,
            ),
        ):
            await run_audit_pipeline(self.session, audit.id)

        self.assertEqual(observed_status, [AuditStatus.RUNNING])

    async def test_pipeline_is_idempotent_on_rerun(self) -> None:
        audit = await self._create_audit()
        provider = _QueryAwareProvider()

        first = await run_audit_pipeline(
            self.session,
            audit.id,
            provider_factory=lambda _provider: provider,
        )
        second = await run_audit_pipeline(
            self.session,
            audit.id,
            provider_factory=lambda _provider: provider,
        )

        job_count = await self._count(Job)
        raw_count = await self._count(RawResponse)
        parsed_count = await self._count(ParsedResult)
        score_count = await self._count(Score)
        self.assertEqual(first.scheduling.scheduled_jobs, 1)
        self.assertEqual(second.scheduling.scheduled_jobs, 0)
        assert second.execution is not None
        self.assertEqual(second.execution.jobs_executed, 0)
        self.assertEqual(second.execution.jobs_skipped, 1)
        assert second.post_processing is not None
        self.assertEqual(second.post_processing.skipped_already_processed, 1)
        self.assertEqual(job_count, 1)
        self.assertEqual(raw_count, 1)
        self.assertEqual(parsed_count, 1)
        self.assertEqual(score_count, 1)
        self.assertEqual(await self._count(AuditMetricsSnapshot), 1)

    async def test_pipeline_calls_execution_and_post_processing_services(self) -> None:
        audit = await self._create_audit()
        provider = _QueryAwareProvider()

        with (
            patch(
                "libs.execution.pipeline.execute_audit_jobs",
                wraps=execute_audit_jobs,
            ) as execution,
            patch(
                "libs.execution.pipeline.process_audit_results",
                wraps=process_audit_results,
            ) as post_processing,
        ):
            summary = await run_audit_pipeline(
                self.session,
                audit.id,
                provider_factory=lambda _provider: provider,
            )

        self.assertEqual(summary.final_audit_status, "completed")
        execution.assert_called_once()
        post_processing.assert_called_once()

    async def test_brand_not_found_still_completes_with_zero_score(self) -> None:
        audit = await self._create_audit(query_texts=["missing brand query"])
        provider = _QueryAwareProvider()

        summary = await run_audit_pipeline(
            self.session,
            audit.id,
            provider_factory=lambda _provider: provider,
        )

        saved_audit = await self.session.get(Audit, audit.id)
        assert saved_audit is not None
        results = await build_audit_results_response(self.session, saved_audit)
        self.assertEqual(summary.final_audit_status, "completed")
        self.assertEqual(saved_audit.status, AuditStatus.COMPLETED)
        self.assertFalse(results.rows[0].visible_brand)
        self.assertEqual(results.rows[0].final_score, 0.0)

    async def test_mixed_success_and_provider_error_results_in_partial(self) -> None:
        audit = await self._create_audit(query_texts=["visible query", "error query"])
        provider = _QueryAwareProvider()

        summary = await run_audit_pipeline(
            self.session,
            audit.id,
            provider_factory=lambda _provider: provider,
        )

        saved_audit = await self.session.get(Audit, audit.id)
        assert saved_audit is not None
        results = await build_audit_results_response(self.session, saved_audit)
        self.assertEqual(summary.final_audit_status, "partial")
        self.assertEqual(saved_audit.status, AuditStatus.PARTIAL)
        self.assertEqual(results.total, 2)
        self.assertTrue(any(row.final_score is not None for row in results.rows))
        self.assertTrue(
            any(row.error_code == "PROVIDER_REQUEST_FAILED" for row in results.rows)
        )

        api_summary = await build_audit_summary_response(self.session, saved_audit)
        self.assertEqual(api_summary.status, "partial")
        self.assertEqual(api_summary.total_runs, 2)

    async def test_all_provider_errors_result_in_failed(self) -> None:
        audit = await self._create_audit(query_texts=["error query"])
        provider = _QueryAwareProvider()

        summary = await run_audit_pipeline(
            self.session,
            audit.id,
            provider_factory=lambda _provider: provider,
        )

        saved_audit = await self.session.get(Audit, audit.id)
        assert saved_audit is not None
        self.assertEqual(summary.final_audit_status, "failed")
        self.assertEqual(saved_audit.status, AuditStatus.FAILED)

    async def test_openai_guardrails_are_preserved_without_real_api_call(self) -> None:
        audit = await self._create_audit(providers=["openai"])

        with patch(
            "libs.execution.openai_provider.OpenAIProviderAdapter.query",
            side_effect=AssertionError("OpenAI should not be called"),
        ) as openai_query:
            summary = await run_audit_pipeline(self.session, audit.id)

        self.assertEqual(summary.final_audit_status, "failed")
        self.assertIn("Provider mode 'mock'", summary.fatal_error or "")
        openai_query.assert_not_called()

    async def test_anthropic_l1_pipeline_completes_with_mocked_provider(self) -> None:
        audit = await self._create_audit(providers=["anthropic"])
        provider = _QueryAwareProvider()

        summary = await run_audit_pipeline(
            self.session,
            audit.id,
            pilot_config=RealProviderPilotConfig(
                real_provider_enabled=True,
                provider_mode="anthropic",
            ),
            provider_factory=lambda _provider: provider,
        )

        saved_audit = await self.session.get(Audit, audit.id)
        assert saved_audit is not None
        results = await build_audit_results_response(self.session, saved_audit)
        self.assertEqual(summary.final_audit_status, "completed")
        self.assertEqual(saved_audit.status, AuditStatus.COMPLETED)
        self.assertEqual(results.total, 1)
        self.assertEqual(results.rows[0].provider, "anthropic")
        self.assertTrue(results.rows[0].visible_brand)

    async def test_anthropic_l2_pipeline_fails_with_unsupported_l2_without_fallback(
        self,
    ) -> None:
        from libs.execution.anthropic_provider import AnthropicProviderAdapter

        audit = await self._create_audit(
            providers=["anthropic"],
            scdl_level=SCDLLevel.L2,
        )

        summary = await run_audit_pipeline(
            self.session,
            audit.id,
            pilot_config=RealProviderPilotConfig(
                real_provider_enabled=True,
                provider_mode="anthropic",
            ),
            provider_factory=lambda _provider: AnthropicProviderAdapter(),
        )

        raw_response = (
            await self.session.execute(select(RawResponse))
        ).scalar_one_or_none()
        self.assertEqual(summary.final_audit_status, "failed")
        assert raw_response is not None
        self.assertEqual(raw_response.error_object["code"], "UNSUPPORTED_L2")

    async def test_openrouter_l1_pipeline_completes_with_mocked_gateway_provider(
        self,
    ) -> None:
        audit = await self._create_audit(providers=["openrouter"])
        provider = _QueryAwareProvider()

        summary = await run_audit_pipeline(
            self.session,
            audit.id,
            pilot_config=RealProviderPilotConfig(
                real_provider_enabled=True,
                provider_mode="openrouter",
            ),
            provider_factory=lambda _provider: provider,
        )

        saved_audit = await self.session.get(Audit, audit.id)
        assert saved_audit is not None
        results = await build_audit_results_response(self.session, saved_audit)
        self.assertEqual(summary.final_audit_status, "completed")
        self.assertEqual(results.total, 1)
        self.assertEqual(results.rows[0].provider, "openrouter")

    async def test_openrouter_l2_pipeline_completes_with_mocked_gateway_provider(
        self,
    ) -> None:
        audit = await self._create_audit(
            providers=["openrouter"],
            scdl_level=SCDLLevel.L2,
        )
        provider = _QueryAwareProvider()

        summary = await run_audit_pipeline(
            self.session,
            audit.id,
            pilot_config=RealProviderPilotConfig(
                real_provider_enabled=True,
                provider_mode="openrouter",
            ),
            provider_factory=lambda _provider: provider,
        )

        saved_audit = await self.session.get(Audit, audit.id)
        assert saved_audit is not None
        results = await build_audit_results_response(self.session, saved_audit)
        self.assertEqual(summary.final_audit_status, "completed")
        self.assertEqual(results.rows[0].provider, "openrouter")

    async def test_pipeline_emits_safe_structured_logs_for_openrouter_gateway(
        self,
    ) -> None:
        audit = await self._create_audit(providers=["openrouter"])
        handler = _ListHandler()
        execution_logger = logging.getLogger("libs.execution")
        previous_level = execution_logger.level
        execution_logger.setLevel(logging.INFO)
        execution_logger.addHandler(handler)
        try:
            await run_audit_pipeline(
                self.session,
                audit.id,
                pilot_config=RealProviderPilotConfig(
                    real_provider_enabled=True,
                    provider_mode="openrouter",
                ),
                provider_factory=lambda _provider: _OpenRouterLikeProvider(),
            )
        finally:
            execution_logger.removeHandler(handler)
            execution_logger.setLevel(previous_level)

        events = [getattr(record, "event", None) for record in handler.records]
        for expected_event in {
            "audit_pipeline_started",
            "audit_jobs_scheduled",
            "audit_job_started",
            "provider_call_started",
            "provider_call_completed",
            "audit_job_completed",
            "post_processing_started",
            "run_processing_completed",
            "post_processing_completed",
            "audit_status_transition",
            "audit_pipeline_completed",
        }:
            self.assertIn(expected_event, events)

        provider_completed = next(
            record
            for record in handler.records
            if getattr(record, "event", None) == "provider_call_completed"
        )
        self.assertEqual(provider_completed.execution_provider, "openrouter")
        self.assertEqual(provider_completed.model_id, "anthropic/claude-3.5-sonnet")
        self.assertEqual(provider_completed.model_provider, "anthropic")
        self.assertTrue(provider_completed.gateway)
        self.assertFalse(provider_completed.gateway_l2_experimental)
        self.assertEqual(provider_completed.level, "L1")
        self.assertEqual(provider_completed.total_tokens, 33)

    async def test_provider_call_started_uses_openrouter_adapter_metadata_for_routed_provider(
        self,
    ) -> None:
        audit = await self._create_audit(providers=["gemini"])
        handler = _ListHandler()
        execution_logger = logging.getLogger("libs.execution")
        previous_level = execution_logger.level
        execution_logger.setLevel(logging.INFO)
        execution_logger.addHandler(handler)
        try:
            await run_audit_pipeline(
                self.session,
                audit.id,
                pilot_config=RealProviderPilotConfig(
                    real_provider_enabled=True,
                    provider_mode="openrouter",
                ),
                provider_factory=lambda _provider: _OpenRouterAdapterLikeProvider(),
            )
        finally:
            execution_logger.removeHandler(handler)
            execution_logger.setLevel(previous_level)

        provider_started = next(
            record
            for record in handler.records
            if getattr(record, "event", None) == "provider_call_started"
        )
        self.assertEqual(provider_started.execution_provider, "openrouter")
        self.assertEqual(provider_started.model_id, "google/gemini-2.0-flash-001")
        self.assertEqual(provider_started.model_provider, "google")
        self.assertTrue(provider_started.gateway)
        self.assertFalse(provider_started.gateway_l2_experimental)

    async def test_provider_failure_logs_do_not_include_unsafe_values(self) -> None:
        audit = await self._create_audit(providers=["openrouter"])
        handler = _ListHandler()
        execution_logger = logging.getLogger("libs.execution")
        previous_level = execution_logger.level
        execution_logger.setLevel(logging.INFO)
        execution_logger.addHandler(handler)
        try:
            summary = await run_audit_pipeline(
                self.session,
                audit.id,
                pilot_config=RealProviderPilotConfig(
                    real_provider_enabled=True,
                    provider_mode="openrouter",
                ),
                provider_factory=lambda _provider: _UnsafeRaisingProvider(),
            )
        finally:
            execution_logger.removeHandler(handler)
            execution_logger.setLevel(previous_level)

        self.assertEqual(summary.final_audit_status, "failed")
        events = [getattr(record, "event", None) for record in handler.records]
        self.assertIn("provider_call_failed", events)
        self.assertEqual(events.count("audit_job_failed"), 0)
        safe_field_names = {
            "event",
            "audit_id",
            "run_id",
            "query_id",
            "execution_provider",
            "model_id",
            "model_provider",
            "level",
            "gateway",
            "gateway_l2_experimental",
            "status",
            "duration_ms",
            "error_code",
            "retryable",
            "source_count",
            "from_status",
            "to_status",
            "reason",
            "exception_type",
        }
        combined = "\n".join(
            " ".join(
                str(getattr(record, name))
                for name in safe_field_names
                if hasattr(record, name)
            )
            for record in handler.records
        ).lower()
        for unsafe in {
            "openrouter_api_key",
            "authorization",
            "headers",
            "bearer",
            "raw_response",
            "raw_prompt",
            "request_body",
            "raw_tool_result",
            "raw_annotations",
            "stack_trace",
            "traceback",
            "sk-or-",
            "sk-",
        }:
            self.assertNotIn(unsafe, combined)

    async def test_missing_audit_returns_fatal_summary(self) -> None:
        summary = await run_audit_pipeline(self.session, 404)

        self.assertEqual(summary.final_audit_status, "failed")
        self.assertIn("was not found", summary.fatal_error or "")

    async def _count(self, model: type) -> int:
        return (
            await self.session.execute(select(func.count()).select_from(model))
        ).scalar_one()


if __name__ == "__main__":
    unittest.main()
