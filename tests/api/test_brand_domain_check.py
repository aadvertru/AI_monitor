from __future__ import annotations

import unittest
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.api.main import BrandDomainCheckRequest, check_brand_domain
from apps.api.security import create_access_token, load_auth_config
from libs.execution.domain_check import DomainCheckResult
from libs.storage.models import Base, User, UserRole

AUTH_ENV = {"JWT_SECRET": "test-secret-value"}


class BrandDomainCheckAPITests(unittest.IsolatedAsyncioTestCase):
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

    async def test_brand_domain_check_requires_authentication(self) -> None:
        payload = BrandDomainCheckRequest(domain="example.com")

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                self.assertRaises(HTTPException) as context,
            ):
                await check_brand_domain(
                    payload=payload,
                    request=self._anonymous_request(),
                    session=session,
                )

        self.assertEqual(context.exception.status_code, 401)

    async def test_brand_domain_check_returns_safe_result(self) -> None:
        user = await self._create_user()
        payload = BrandDomainCheckRequest(domain="https://Example.com/path")
        check_mock = AsyncMock(
            return_value=DomainCheckResult(
                input="https://Example.com/path",
                normalized_domain="example.com",
                status="reachable",
                http_status=200,
                checked_at=datetime(2026, 1, 1, tzinfo=UTC),
                query_generation_allowed=True,
                reason=None,
            )
        )

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                patch("apps.api.main.check_brand_domain_availability", check_mock),
            ):
                response = await check_brand_domain(
                    payload=payload,
                    request=self._authenticated_request(user),
                    session=session,
                )

        check_mock.assert_awaited_once_with("https://Example.com/path")
        self.assertEqual(response.normalized_domain, "example.com")
        self.assertEqual(response.status, "reachable")
        self.assertEqual(response.http_status, 200)
        self.assertTrue(response.query_generation_allowed)
        self.assertEqual(response.cache_ttl_seconds, 86400)

        serialized = str(response.model_dump(mode="json")).lower()
        for unsafe_value in (
            "html",
            "body",
            "authorization",
            "headers",
            "secret",
            "api_key",
            "stack",
        ):
            self.assertNotIn(unsafe_value, serialized)
