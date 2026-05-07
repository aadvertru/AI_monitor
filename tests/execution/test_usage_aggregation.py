from __future__ import annotations

import unittest

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from libs.execution.usage_aggregation import (
    aggregate_audit_usage,
    aggregate_target_usage,
    aggregate_user_usage,
)
from libs.storage.models import (
    Audit,
    AuditStatus,
    AuditTarget,
    Base,
    Brand,
    Query,
    RawResponse,
    Run,
    RunStatus,
    SCDLLevel,
    User,
)


class ProviderUsageAggregationTests(unittest.IsolatedAsyncioTestCase):
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
        email: str = "user@example.com",
        brand_name: str = "Acme",
        scdl_level: SCDLLevel = SCDLLevel.L1,
    ) -> tuple[User, Audit, Query]:
        user = User(email=email, hashed_password="hash")
        brand = Brand(name=brand_name, domain=f"{brand_name.lower()}.com")
        audit = Audit(
            brand=brand,
            user=user,
            providers=["openrouter"],
            runs_per_query=1,
            scdl_level=scdl_level,
            status=AuditStatus.COMPLETED,
        )
        query = Query(audit=audit, text="best tools")
        self.session.add_all([user, brand, audit, query])
        await self.session.flush()
        return user, audit, query

    async def _add_target(
        self,
        audit: Audit,
        *,
        execution_provider: str = "openrouter",
        model_provider: str = "google",
        model_id: str = "google/gemini-2.0-flash-001",
        level: SCDLLevel = SCDLLevel.L1,
        display_name: str = "Gemini",
    ) -> AuditTarget:
        target = AuditTarget(
            audit_id=audit.id,
            ai_family=model_provider,
            execution_provider=execution_provider,
            model_provider=model_provider,
            model_id=model_id,
            display_name=display_name,
            level=level,
            gateway=execution_provider == "openrouter",
            gateway_l2_experimental=level == SCDLLevel.L2,
        )
        self.session.add(target)
        await self.session.flush()
        return target

    async def _add_run(
        self,
        audit: Audit,
        query: Query,
        *,
        provider: str = "openrouter",
        target: AuditTarget | None = None,
        run_number: int = 1,
        status: RunStatus = RunStatus.SUCCESS,
        metadata: dict | None = None,
        response_time: float | None = 0.25,
    ) -> Run:
        run = Run(
            audit_id=audit.id,
            query_id=query.id,
            audit_target_id=target.id if target is not None else None,
            provider=provider,
            run_number=run_number,
            status=status,
        )
        self.session.add(run)
        await self.session.flush()
        self.session.add(
            RawResponse(
                run_id=run.id,
                request_snapshot={"raw_prompt": "must not leak"},
                raw_answer="raw answer must not leak",
                citations=[],
                provider_metadata=metadata,
                provider_status=status.value,
                response_time=response_time,
                error_object={"headers": {"authorization": "Bearer sk-hidden"}},
            )
        )
        await self.session.commit()
        return run

    async def test_aggregate_audit_usage_across_targets(self) -> None:
        _user, audit, query = await self._create_audit()
        gemini = await self._add_target(audit)
        claude = await self._add_target(
            audit,
            model_provider="anthropic",
            model_id="anthropic/claude-3.5-sonnet",
            display_name="Claude",
        )
        await self._add_run(
            audit,
            query,
            target=gemini,
            metadata={
                "provider": "openrouter",
                "execution_provider": "openrouter",
                "model_id": "google/gemini-2.0-flash-001",
                "level": "L1",
                "usage": {
                    "input_tokens": 10,
                    "output_tokens": 20,
                    "total_tokens": 30,
                    "cached_tokens": 2,
                    "reasoning_tokens": 1,
                },
                "raw_response": {"secret": "sk-hidden"},
            },
        )
        await self._add_run(
            audit,
            query,
            target=claude,
            metadata={
                "provider": "openrouter",
                "execution_provider": "openrouter",
                "model_id": "anthropic/claude-3.5-sonnet",
                "level": "L1",
                "usage": {"input_tokens": 5, "output_tokens": 7},
            },
            response_time=0.5,
        )

        summary = await aggregate_audit_usage(self.session, audit.id)

        self.assertEqual(summary.run_count, 2)
        self.assertEqual(summary.totals.input_tokens, 15)
        self.assertEqual(summary.totals.output_tokens, 27)
        self.assertEqual(summary.totals.total_tokens, 42)
        self.assertEqual(summary.totals.cached_tokens, 2)
        self.assertEqual(summary.totals.reasoning_tokens, 1)
        self.assertEqual(summary.totals.duration_ms, 750)
        self.assertEqual(len(summary.targets), 2)

    async def test_aggregate_target_usage_groups_by_target(self) -> None:
        _user, audit, query = await self._create_audit()
        target = await self._add_target(audit)
        await self._add_run(
            audit,
            query,
            target=target,
            metadata={"usage": {"input_tokens": 4, "output_tokens": 6}},
        )
        await self._add_run(
            audit,
            query,
            target=target,
            run_number=2,
            metadata={"usage": {"input_tokens": 1, "output_tokens": 2}},
        )

        targets = await aggregate_target_usage(self.session, audit.id)

        self.assertEqual(len(targets), 1)
        self.assertEqual(targets[0].target_id, target.id)
        self.assertEqual(targets[0].run_count, 2)
        self.assertEqual(targets[0].totals.total_tokens, 13)

    async def test_aggregate_user_usage_across_audits(self) -> None:
        user, first_audit, first_query = await self._create_audit(
            email="owner@example.com", brand_name="First"
        )
        second_user, second_audit, second_query = await self._create_audit(
            email="other@example.com", brand_name="Second"
        )
        third_brand = Brand(name="Third", domain="third.com")
        third_audit = Audit(
            brand=third_brand,
            user=user,
            providers=["mock"],
            runs_per_query=1,
            scdl_level=SCDLLevel.L1,
            status=AuditStatus.COMPLETED,
        )
        third_query = Query(audit=third_audit, text="third query")
        self.session.add_all([third_brand, third_audit, third_query])
        await self.session.flush()
        await self._add_run(
            first_audit,
            first_query,
            metadata={"usage": {"total_tokens": 11}},
        )
        await self._add_run(
            third_audit,
            third_query,
            provider="mock",
            metadata={"usage": {"total_tokens": 13}},
        )
        await self._add_run(
            second_audit,
            second_query,
            metadata={"usage": {"total_tokens": 99}},
        )

        summary = await aggregate_user_usage(self.session, user.id)

        self.assertEqual(second_user.email, "other@example.com")
        self.assertEqual(summary.run_count, 2)
        self.assertEqual(summary.totals.total_tokens, 24)

    async def test_missing_usage_is_safe(self) -> None:
        _user, audit, query = await self._create_audit()
        await self._add_run(audit, query, metadata=None, response_time=None)

        summary = await aggregate_audit_usage(self.session, audit.id)

        self.assertEqual(summary.run_count, 1)
        self.assertEqual(summary.totals.total_tokens, 0)
        self.assertEqual(summary.totals.duration_ms, 0)

    async def test_openrouter_web_search_requests_are_included_when_present(self) -> None:
        _user, audit, query = await self._create_audit(scdl_level=SCDLLevel.L2)
        target = await self._add_target(audit, level=SCDLLevel.L2)
        await self._add_run(
            audit,
            query,
            target=target,
            metadata={
                "provider": "openrouter",
                "execution_provider": "openrouter",
                "model_id": "google/gemini-2.0-flash-001",
                "level": "L2",
                "usage": {"total_tokens": 10, "web_search_requests": 3},
            },
        )

        summary = await aggregate_audit_usage(self.session, audit.id)

        self.assertEqual(summary.totals.web_search_requests, 3)
        self.assertEqual(summary.runs[0].level, "L2")

    async def test_legacy_run_without_target_is_safe(self) -> None:
        _user, audit, query = await self._create_audit(scdl_level=SCDLLevel.L1)
        await self._add_run(
            audit,
            query,
            provider="openai",
            target=None,
            metadata={"provider": "openai", "model": "gpt-test", "usage": {"total_tokens": 8}},
        )

        summary = await aggregate_audit_usage(self.session, audit.id)

        self.assertEqual(summary.run_count, 1)
        self.assertIsNone(summary.runs[0].target_id)
        self.assertEqual(summary.runs[0].provider, "openai")
        self.assertEqual(summary.runs[0].model_id, "gpt-test")
        self.assertEqual(summary.runs[0].level, "L1")

    async def test_summary_serialization_does_not_include_raw_provider_data(self) -> None:
        _user, audit, query = await self._create_audit()
        await self._add_run(
            audit,
            query,
            metadata={
                "usage": {"total_tokens": 5},
                "raw_prompt": "secret prompt",
                "headers": {"authorization": "Bearer sk-hidden"},
                "request_snapshot": {"api_key": "sk-hidden"},
            },
        )

        payload = (await aggregate_audit_usage(self.session, audit.id)).to_dict()
        combined = str(payload).lower()

        self.assertIn("total_tokens", combined)
        self.assertNotIn("secret prompt", combined)
        self.assertNotIn("authorization", combined)
        self.assertNotIn("sk-hidden", combined)
        self.assertNotIn("raw_answer", combined)
        self.assertNotIn("request_snapshot", combined)


if __name__ == "__main__":
    unittest.main()
