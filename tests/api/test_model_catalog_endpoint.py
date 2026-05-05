from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.api.main import get_model_catalog_endpoint
from apps.api.security import create_access_token, load_auth_config
from libs.execution.openrouter_model_catalog import (
    ModelCatalogFamily,
    ModelCatalogModel,
    ModelCatalogResponse,
)
from libs.execution.provider_errors import (
    no_api_key_error,
    provider_disabled_error,
    provider_request_failed_error,
)
from libs.storage.models import Base, User, UserRole

AUTH_ENV = {"JWT_SECRET": "test-secret-value"}


class ModelCatalogEndpointTests(unittest.IsolatedAsyncioTestCase):
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
                email="catalog@example.com",
                hashed_password="hashed",
                role=UserRole.USER,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

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

    async def test_model_catalog_requires_authentication(self) -> None:
        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                self.assertRaises(HTTPException) as context,
            ):
                await get_model_catalog_endpoint(self._anonymous_request(), session)

        self.assertEqual(context.exception.status_code, 401)

    async def test_authenticated_request_returns_allowed_only_safe_catalog(self) -> None:
        user = await self._create_user()
        response = _catalog_response()
        service_mock = AsyncMock(return_value=response)

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                patch("apps.api.main.get_openrouter_model_catalog", service_mock),
            ):
                result = await get_model_catalog_endpoint(
                    self._authenticated_request(user),
                    session,
                )

        self.assertEqual(result, response)
        self.assertEqual(service_mock.await_count, 1)
        dumped = result.model_dump_json(exclude_none=True)
        self.assertIn("openai/gpt-4o-mini", dumped)
        self.assertNotIn("is_allowed", dumped)
        self.assertNotIn("not-allowed", dumped)
        self.assertNotIn("sk-hidden", dumped)
        self.assertNotIn("raw_response", dumped)

    async def test_stale_cache_warning_is_returned_with_200_response(self) -> None:
        user = await self._create_user()
        response = _catalog_response(warnings=["OpenRouter catalog refresh failed."])

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                patch(
                    "apps.api.main.get_openrouter_model_catalog",
                    AsyncMock(return_value=response),
                ),
            ):
                result = await get_model_catalog_endpoint(
                    self._authenticated_request(user),
                    session,
                )

        self.assertEqual(result.warnings, ["OpenRouter catalog refresh failed."])
        self.assertGreater(len(result.families), 0)

    async def test_no_cache_fetch_failure_returns_safe_503(self) -> None:
        user = await self._create_user()
        response = ModelCatalogResponse(
            families=[],
            diagnostic=provider_request_failed_error("openrouter").to_error_dict(),
        )

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                patch(
                    "apps.api.main.get_openrouter_model_catalog",
                    AsyncMock(return_value=response),
                ),
                self.assertRaises(HTTPException) as context,
            ):
                await get_model_catalog_endpoint(self._authenticated_request(user), session)

        self.assertEqual(context.exception.status_code, 503)
        self.assertEqual(context.exception.detail["code"], "PROVIDER_REQUEST_FAILED")
        self.assertNotIn("raw", str(context.exception.detail).lower())
        self.assertNotIn("sk-hidden", str(context.exception.detail))

    async def test_catalog_disabled_and_missing_key_are_safe_503(self) -> None:
        user = await self._create_user()

        for diagnostic in (
            provider_disabled_error("openrouter").to_error_dict(),
            no_api_key_error("openrouter").to_error_dict(),
        ):
            with self.subTest(code=diagnostic["code"]):
                async with self.session_factory() as session:
                    with (
                        patch.dict("os.environ", AUTH_ENV, clear=True),
                        patch(
                            "apps.api.main.get_openrouter_model_catalog",
                            AsyncMock(
                                return_value=ModelCatalogResponse(
                                    families=[],
                                    diagnostic=diagnostic,
                                )
                            ),
                        ),
                        self.assertRaises(HTTPException) as context,
                    ):
                        await get_model_catalog_endpoint(
                            self._authenticated_request(user),
                            session,
                        )

                self.assertEqual(context.exception.status_code, 503)
                self.assertEqual(context.exception.detail["code"], diagnostic["code"])


def _catalog_response(*, warnings: list[str] | None = None) -> ModelCatalogResponse:
    cached_at = datetime(2026, 5, 5, tzinfo=UTC)
    return ModelCatalogResponse(
        families=[
            ModelCatalogFamily(
                id="chatgpt",
                label="ChatGPT",
                models=[
                    ModelCatalogModel(
                        model_id="openai/gpt-4o-mini",
                        display_name="GPT-4o mini",
                        model_provider="openai",
                        ai_family="chatgpt",
                        context_length=128000,
                    )
                ],
            )
        ],
        cached_at=cached_at,
        expires_at=cached_at + timedelta(days=1),
        warnings=warnings or [],
    )


if __name__ == "__main__":
    unittest.main()
