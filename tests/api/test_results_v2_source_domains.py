from __future__ import annotations

import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.api.main import get_audit_source_domains
from apps.api.security import create_access_token, load_auth_config
from libs.storage.models import (
    Audit,
    AuditStatus,
    AuditTarget,
    Base,
    Brand,
    ParsedResult,
    Query,
    RawResponse,
    Run,
    RunStatus,
    SCDLLevel,
    User,
    UserRole,
)

AUTH_ENV = {"JWT_SECRET": "test-secret-value"}
NOW = datetime(2026, 5, 6, 10, 0, tzinfo=timezone.utc)


class ResultsV2SourceDomainsAPITests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.auth_env = patch.dict("os.environ", AUTH_ENV, clear=True)
        self.auth_env.start()
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def asyncTearDown(self) -> None:
        await self.engine.dispose()
        self.auth_env.stop()

    async def _create_user(self, email: str = "owner@example.com") -> User:
        async with self.session_factory() as session:
            user = User(email=email, hashed_password="hashed", role=UserRole.USER)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    async def _create_audit(
        self,
        user: User,
        *,
        level: SCDLLevel = SCDLLevel.L1,
        include_sources: bool = True,
        with_target: bool = False,
        invalid_source: bool = False,
    ) -> Audit:
        async with self.session_factory() as session:
            brand = Brand(name=f"Sources {user.id}", domain=f"sources-{user.id}.example")
            audit = Audit(
                brand=brand,
                user_id=user.id,
                status=AuditStatus.COMPLETED,
                providers=["mock"],
                runs_per_query=1,
                scdl_level=level,
                created_at=NOW,
                updated_at=NOW,
            )
            session.add(audit)
            await session.flush()
            target = None
            if with_target:
                target = AuditTarget(
                    audit_id=audit.id,
                    ai_family="chatgpt",
                    execution_provider="openrouter",
                    model_provider="openai",
                    model_id="openai/gpt-4o-mini",
                    display_name="GPT-4o mini",
                    level=level,
                    gateway=True,
                    gateway_l2_experimental=level == SCDLLevel.L2,
                )
                session.add(target)
                await session.flush()
            query = Query(audit_id=audit.id, text="source heavy query")
            session.add(query)
            await session.flush()
            run = Run(
                audit_id=audit.id,
                query_id=query.id,
                audit_target_id=target.id if target is not None else None,
                provider=target.execution_provider if target is not None else "mock",
                run_number=1,
                status=RunStatus.SUCCESS,
            )
            session.add(run)
            await session.flush()
            parsed_sources: list[dict[str, object]] = []
            citations: list[dict[str, object]] = []
            if include_sources:
                parsed_sources = [
                    {
                        "url": "https://docs.example.com/path?utm_source=x",
                        "title": "Docs",
                        "snippet": "Documentation snippet.",
                        "raw_source_payload": "must stay hidden",
                    },
                    {"url": "https://blog.example.com/article", "title": "Blog"},
                ]
                citations = [
                    {"url": "https://docs.example.com/path", "title": "Docs"}
                ]
                if invalid_source:
                    parsed_sources.append(
                        {
                            "url": "javascript:alert(1)",
                            "title": "Unsafe",
                            "headers": {"authorization": "secret"},
                        }
                    )
            session.add_all(
                [
                    ParsedResult(
                        run_id=run.id,
                        visible_brand=True,
                        brand_position_rank=1,
                        prominence_score=0.5,
                        sentiment=0.0,
                        recommendation_score=0.5,
                        source_quality_score=0.0,
                        competitors=[],
                        sources=parsed_sources,
                        parsed_payload={"raw_source_payload": "must stay hidden"},
                    ),
                    RawResponse(
                        run_id=run.id,
                        request_snapshot={"query": "safe"},
                        raw_answer="answer with source mentions",
                        citations=citations,
                        provider_metadata={
                            "model": target.model_id if target is not None else "mock"
                        },
                        provider_status="success",
                    ),
                ]
            )
            await session.commit()
            await session.refresh(audit)
            return audit

    def _request(self, user: User) -> Request:
        config = load_auth_config(env=AUTH_ENV)
        token = create_access_token(user_id=user.id, role=user.role.value, config=config)
        return Request(
            {
                "type": "http",
                "headers": [(b"cookie", f"{config.cookie.name}={token}".encode("ascii"))],
            }
        )

    def _anonymous_request(self) -> Request:
        return Request({"type": "http", "headers": []})

    async def test_source_domains_requires_auth_and_enforces_ownership(self) -> None:
        owner = await self._create_user("owner@example.com")
        other = await self._create_user("other@example.com")
        audit = await self._create_audit(owner)

        async with self.session_factory() as session:
            with self.assertRaises(HTTPException) as unauth_context:
                await get_audit_source_domains(
                    audit_id=audit.id,
                    request=self._anonymous_request(),
                    session=session,
                )
            with self.assertRaises(HTTPException) as other_context:
                await get_audit_source_domains(
                    audit_id=audit.id,
                    request=self._request(other),
                    session=session,
                )

        self.assertEqual(unauth_context.exception.status_code, 401)
        self.assertEqual(other_context.exception.status_code, 404)

    async def test_source_domains_groups_sources_and_excludes_raw_fields(self) -> None:
        owner = await self._create_user()
        audit = await self._create_audit(owner, level=SCDLLevel.L1)

        async with self.session_factory() as session:
            result = await get_audit_source_domains(
                audit_id=audit.id,
                request=self._request(owner),
                session=session,
            )

        self.assertEqual(result.audit_id, audit.id)
        self.assertEqual(len(result.domains), 1)
        domain = result.domains[0]
        self.assertEqual(domain.domain, "example.com")
        self.assertEqual(domain.source_count, 3)
        self.assertEqual(domain.unique_url_count, 2)
        self.assertEqual(domain.query_count, 1)
        self.assertEqual(domain.levels, ["L1"])
        self.assertEqual(domain.providers, ["mock"])
        self.assertIn(
            "https://docs.example.com/path",
            {url.normalized_url for url in domain.urls},
        )
        self.assertEqual(result.warnings, [])
        serialized = str(result.model_dump())
        self.assertNotIn("raw_source_payload", serialized)
        self.assertNotIn("headers", serialized)

    async def test_source_domains_returns_empty_state_when_no_sources_exist(self) -> None:
        owner = await self._create_user()
        audit = await self._create_audit(owner, level=SCDLLevel.L2, include_sources=False)

        async with self.session_factory() as session:
            result = await get_audit_source_domains(
                audit_id=audit.id,
                request=self._request(owner),
                session=session,
            )

        self.assertEqual(result.audit_id, audit.id)
        self.assertEqual(result.domains, [])
        self.assertEqual(result.warnings, [])

    async def test_source_domains_includes_gateway_metadata_and_skips_invalid_urls(
        self,
    ) -> None:
        owner = await self._create_user()
        audit = await self._create_audit(
            owner,
            level=SCDLLevel.L2,
            with_target=True,
            invalid_source=True,
        )

        async with self.session_factory() as session:
            result = await get_audit_source_domains(
                audit_id=audit.id,
                request=self._request(owner),
                session=session,
            )

        self.assertEqual(len(result.domains), 1)
        domain = result.domains[0]
        self.assertEqual(domain.models, ["openai/gpt-4o-mini"])
        self.assertEqual(domain.providers, ["openrouter"])
        self.assertEqual(domain.levels, ["L2"])
        self.assertTrue(domain.urls[0].gateway)
        self.assertTrue(domain.urls[0].gateway_l2_experimental)
        self.assertEqual(result.warnings, ["Skipped 1 invalid source URL(s)."])
        serialized = str(result.model_dump())
        self.assertNotIn("javascript", serialized)
        self.assertNotIn("authorization", serialized)


if __name__ == "__main__":
    unittest.main()
