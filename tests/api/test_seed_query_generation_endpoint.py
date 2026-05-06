from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException, Request
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.api.main import (
    GenerateSeedQuerySuggestionsRequest,
    suggest_seed_queries,
)
from apps.api.security import create_access_token, load_auth_config
from apps.api.services.seed_query_generation import (
    GeneratedSeedQueriesResult,
    GeneratedSeedQuerySuggestion,
    SeedQueryGenerationConfigError,
    SeedQueryGenerationUnavailable,
)
from libs.storage.models import (
    Audit,
    AuditStatus,
    Base,
    Brand,
    Query,
    Run,
    SCDLLevel,
    User,
    UserRole,
)

AUTH_ENV = {"JWT_SECRET": "test-secret-value"}


class SeedQueryGenerationEndpointTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def asyncTearDown(self) -> None:
        await self.engine.dispose()

    async def _create_user(self) -> User:
        async with self.session_factory() as session:
            user = User(
                email="owner@example.com",
                hashed_password="hashed-password",
                role=UserRole.USER,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    async def _create_audit(self, user: User, status: AuditStatus = AuditStatus.CREATED) -> Audit:
        async with self.session_factory() as session:
            brand = Brand(
                name="Seopaja",
                domain="seopaja.fi",
                description="SEO services",
            )
            session.add(brand)
            await session.flush()
            audit = Audit(
                brand_id=brand.id,
                user_id=user.id,
                status=status,
                providers=["openai"],
                runs_per_query=1,
                language="en",
                country="US",
                locale="en-US",
                scdl_level=SCDLLevel.L1,
            )
            session.add(audit)
            await session.commit()
            await session.refresh(audit)
            return audit

    def _authenticated_request(self, user: User) -> Request:
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

    async def test_unauthenticated_request_is_rejected(self) -> None:
        payload = GenerateSeedQuerySuggestionsRequest.model_validate(
            {
                "brand_description": "SEO services",
                "use_description": True,
                "existing_queries": [],
            }
        )

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                self.assertRaises(HTTPException) as context,
            ):
                await suggest_seed_queries(
                    payload=payload,
                    request=self._anonymous_request(),
                    session=session,
                )

        self.assertEqual(context.exception.status_code, 401)

    async def test_authenticated_request_returns_safe_suggestions(self) -> None:
        user = await self._create_user()
        payload = GenerateSeedQuerySuggestionsRequest.model_validate(
            {
                "brand_name": "Seopaja",
                "brand_domain": "seopaja.fi",
                "brand_description": "SEO services",
                "use_domain": True,
                "use_description": True,
                "count": 10,
                "existing_queries": [{"text": "What is Seopaja?"}],
            }
        )
        service = AsyncMock(
            return_value=GeneratedSeedQueriesResult(
                suggestions=[
                    GeneratedSeedQuerySuggestion(
                        text="Best SEO agencies",
                        type="category_discovery",
                    )
                ],
                skipped_duplicates=1,
                warnings=["1 duplicate query suggestion(s) skipped."],
            )
        )

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                patch("apps.api.main.generate_seed_query_suggestions", service),
            ):
                response = await suggest_seed_queries(
                    payload=payload,
                    request=self._authenticated_request(user),
                    session=session,
                )

        self.assertEqual(response.suggestions[0].text, "Best SEO agencies")
        self.assertEqual(response.suggestions[0].source, "ai")
        self.assertEqual(response.skipped_duplicates, 1)
        self.assertEqual(response.warnings, ["1 duplicate query suggestion(s) skipped."])
        self.assertNotIn("prompt", response.model_dump())
        self.assertNotIn("raw_response", response.model_dump())
        service.assert_awaited_once()
        service_payload = service.await_args.args[0]
        self.assertEqual(service_payload.brand_domain, "seopaja.fi")
        self.assertEqual(service_payload.existing_queries[0].source, "user")

    async def test_paa_request_fields_and_source_are_forwarded(self) -> None:
        user = await self._create_user()
        payload = GenerateSeedQuerySuggestionsRequest.model_validate(
            {
                "brand_name": "Seopaja",
                "use_paa": True,
                "language": "en",
                "country": "US",
                "paa_seed_query": "SEO tools",
                "existing_queries": [
                    {
                        "text": "Existing PAA query",
                        "type": "brand_direct",
                        "source": "paa",
                    }
                ],
            }
        )
        service = AsyncMock(
            return_value=GeneratedSeedQueriesResult(
                suggestions=[
                    GeneratedSeedQuerySuggestion(
                        text="People also ask query",
                        type="problem_solution",
                        source="paa",
                        metadata={"paa_provider": "mock", "language": "en"},
                    )
                ],
                warnings=["PAA warning"],
            )
        )

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                patch("apps.api.main.generate_seed_query_suggestions", service),
            ):
                response = await suggest_seed_queries(
                    payload=payload,
                    request=self._authenticated_request(user),
                    session=session,
                )

        self.assertEqual(response.suggestions[0].source, "paa")
        self.assertEqual(response.suggestions[0].metadata["paa_provider"], "mock")
        self.assertEqual(response.warnings, ["PAA warning"])
        service_payload = service.await_args.args[0]
        self.assertTrue(service_payload.use_paa)
        self.assertEqual(service_payload.language, "en")
        self.assertEqual(service_payload.country, "US")
        self.assertEqual(service_payload.paa_seed_query, "SEO tools")
        self.assertEqual(service_payload.existing_queries[0].source, "paa")

    async def test_generation_validation_error_returns_422(self) -> None:
        user = await self._create_user()
        payload = GenerateSeedQuerySuggestionsRequest.model_validate(
            {
                "brand_description": "SEO services",
                "use_description": True,
                "existing_queries": [],
            }
        )

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                patch(
                    "apps.api.main.generate_seed_query_suggestions",
                    AsyncMock(side_effect=SeedQueryGenerationConfigError("bad request")),
                ),
                self.assertRaises(HTTPException) as context,
            ):
                await suggest_seed_queries(
                    payload=payload,
                    request=self._authenticated_request(user),
                    session=session,
                )

        self.assertEqual(context.exception.status_code, 422)

    async def test_no_selected_source_returns_422(self) -> None:
        user = await self._create_user()
        payload = GenerateSeedQuerySuggestionsRequest.model_validate(
            {
                "use_domain": False,
                "use_description": False,
                "existing_queries": [],
            }
        )

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                self.assertRaises(HTTPException) as context,
            ):
                await suggest_seed_queries(
                    payload=payload,
                    request=self._authenticated_request(user),
                    session=session,
                )

        self.assertEqual(context.exception.status_code, 422)

    async def test_generation_unavailable_returns_503(self) -> None:
        user = await self._create_user()
        payload = GenerateSeedQuerySuggestionsRequest.model_validate(
            {
                "brand_description": "SEO services",
                "use_description": True,
            }
        )

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                patch(
                    "apps.api.main.generate_seed_query_suggestions",
                    AsyncMock(side_effect=SeedQueryGenerationUnavailable("disabled")),
                ),
                self.assertRaises(HTTPException) as context,
            ):
                await suggest_seed_queries(
                    payload=payload,
                    request=self._authenticated_request(user),
                    session=session,
                )

        self.assertEqual(context.exception.status_code, 503)

    async def test_openai_mode_without_config_returns_503(self) -> None:
        user = await self._create_user()
        payload = GenerateSeedQuerySuggestionsRequest.model_validate(
            {
                "brand_description": "SEO services",
                "use_description": True,
            }
        )
        env = {
            **AUTH_ENV,
            "SEED_QUERY_GENERATION_ENABLED": "1",
            "SEED_QUERY_GENERATION_PROVIDER": "openai",
        }

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", env, clear=True),
                self.assertRaises(HTTPException) as context,
            ):
                await suggest_seed_queries(
                    payload=payload,
                    request=self._authenticated_request(user),
                    session=session,
                )

        self.assertEqual(context.exception.status_code, 503)

    async def test_suggestions_are_not_persisted(self) -> None:
        user = await self._create_user()
        payload = GenerateSeedQuerySuggestionsRequest.model_validate(
            {
                "brand_description": "SEO services",
                "use_description": True,
                "existing_queries": [],
            }
        )

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                patch(
                    "apps.api.main.generate_seed_query_suggestions",
                    AsyncMock(
                        return_value=GeneratedSeedQueriesResult(
                            suggestions=[
                                GeneratedSeedQuerySuggestion(
                                    text="Generated query",
                                    type="recommendation",
                                )
                            ]
                        )
                    ),
                ),
            ):
                await suggest_seed_queries(
                    payload=payload,
                    request=self._authenticated_request(user),
                    session=session,
                )

            query_count = len((await session.execute(select(Query))).scalars().all())

        self.assertEqual(query_count, 0)

    async def test_generation_does_not_change_existing_audit_status_or_create_runs(self) -> None:
        user = await self._create_user()
        audit = await self._create_audit(user, status=AuditStatus.CREATED)
        payload = GenerateSeedQuerySuggestionsRequest.model_validate(
            {
                "brand_description": "SEO services",
                "use_description": True,
                "existing_queries": [],
            }
        )

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                patch(
                    "apps.api.main.generate_seed_query_suggestions",
                    AsyncMock(
                        return_value=GeneratedSeedQueriesResult(
                            suggestions=[
                                GeneratedSeedQuerySuggestion(
                                    text="Generated query",
                                    type="recommendation",
                                )
                            ]
                        )
                    ),
                ),
            ):
                await suggest_seed_queries(
                    payload=payload,
                    request=self._authenticated_request(user),
                    session=session,
                )

            refreshed_audit = await session.get(Audit, audit.id)
            query_count = len((await session.execute(select(Query))).scalars().all())
            run_count = len((await session.execute(select(Run))).scalars().all())

        self.assertIsNotNone(refreshed_audit)
        self.assertEqual(refreshed_audit.status, AuditStatus.CREATED)
        self.assertEqual(query_count, 0)
        self.assertEqual(run_count, 0)

    def test_count_above_ten_is_rejected_by_request_schema(self) -> None:
        with self.assertRaises(ValidationError):
            GenerateSeedQuerySuggestionsRequest.model_validate(
                {
                    "brand_description": "SEO services",
                    "use_description": True,
                    "count": 11,
                }
            )

    def test_invalid_selected_domain_is_rejected_by_request_schema(self) -> None:
        with self.assertRaises(ValidationError):
            GenerateSeedQuerySuggestionsRequest.model_validate(
                {
                    "brand_domain": "https://seopaja.fi/page",
                    "use_domain": True,
                }
            )

    def test_unknown_seed_query_source_is_rejected_by_request_schema(self) -> None:
        with self.assertRaises(ValidationError):
            GenerateSeedQuerySuggestionsRequest.model_validate(
                {
                    "brand_name": "Seopaja",
                    "use_paa": True,
                    "existing_queries": [
                        {
                            "text": "Existing query",
                            "type": "brand_direct",
                            "source": "crawler",
                        }
                    ],
                }
            )


if __name__ == "__main__":
    unittest.main()
