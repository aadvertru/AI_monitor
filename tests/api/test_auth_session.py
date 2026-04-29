from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi import HTTPException, Response
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.api.main import (
    LoginRequest,
    get_current_user_record,
    login_user_record,
    logout_user,
)
from apps.api.security import create_access_token, hash_password, load_auth_config
from libs.storage.models import Base, User, UserRole


class AuthSessionAPITests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        self.config = load_auth_config(
            env={
                "JWT_SECRET": "test-secret-value",
                "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
                "AUTH_COOKIE_NAME": "auth_token",
                "AUTH_COOKIE_HTTPONLY": "true",
                "AUTH_COOKIE_SECURE": "false",
                "AUTH_COOKIE_SAMESITE": "lax",
            }
        )

    async def asyncTearDown(self) -> None:
        await self.engine.dispose()

    async def _create_user(self) -> User:
        async with self.session_factory() as session:
            user = User(
                email="user@example.com",
                hashed_password=hash_password("plain-password"),
                role=UserRole.USER,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    async def test_login_accepts_valid_credentials_and_sets_auth_cookie(self) -> None:
        user = await self._create_user()
        payload = LoginRequest.model_validate(
            {"email": " USER@example.com ", "password": "plain-password"}
        )
        response = Response()

        async with self.session_factory() as session:
            result = await login_user_record(
                session=session,
                payload=payload,
                response=response,
                config=self.config,
            )

        self.assertEqual(result.id, user.id)
        self.assertEqual(result.email, "user@example.com")
        self.assertEqual(result.role, "user")
        self.assertNotIn("password", result.model_dump())
        self.assertNotIn("hashed_password", result.model_dump())

        set_cookie_header = response.headers["set-cookie"]
        self.assertIn("auth_token=", set_cookie_header)
        self.assertIn("HttpOnly", set_cookie_header)
        self.assertIn("SameSite=lax", set_cookie_header)

    async def test_login_rejects_unknown_email(self) -> None:
        payload = LoginRequest.model_validate(
            {"email": "missing@example.com", "password": "plain-password"}
        )

        async with self.session_factory() as session:
            with self.assertRaises(HTTPException) as context:
                await login_user_record(
                    session=session,
                    payload=payload,
                    response=Response(),
                    config=self.config,
                )

        self.assertEqual(context.exception.status_code, 401)

    async def test_login_rejects_invalid_password(self) -> None:
        await self._create_user()
        payload = LoginRequest.model_validate(
            {"email": "user@example.com", "password": "wrong-password"}
        )

        async with self.session_factory() as session:
            with self.assertRaises(HTTPException) as context:
                await login_user_record(
                    session=session,
                    payload=payload,
                    response=Response(),
                    config=self.config,
                )

        self.assertEqual(context.exception.status_code, 401)

    def test_login_rejects_missing_password(self) -> None:
        with self.assertRaises(ValidationError):
            LoginRequest.model_validate({"email": "user@example.com"})

    async def test_get_current_user_returns_user_for_valid_cookie_token(self) -> None:
        user = await self._create_user()
        token = create_access_token(user_id=user.id, role="user", config=self.config)

        async with self.session_factory() as session:
            result = await get_current_user_record(
                session=session,
                token=token,
                config=self.config,
            )

        self.assertEqual(result.id, user.id)
        self.assertEqual(result.email, "user@example.com")
        self.assertEqual(result.role, "user")
        self.assertNotIn("password", result.model_dump())
        self.assertNotIn("hashed_password", result.model_dump())

    async def test_get_current_user_rejects_missing_cookie_token(self) -> None:
        async with self.session_factory() as session:
            with self.assertRaises(HTTPException) as context:
                await get_current_user_record(
                    session=session,
                    token=None,
                    config=self.config,
                )

        self.assertEqual(context.exception.status_code, 401)

    async def test_get_current_user_rejects_invalid_cookie_token(self) -> None:
        async with self.session_factory() as session:
            with self.assertRaises(HTTPException) as context:
                await get_current_user_record(
                    session=session,
                    token="not-a-valid-token",
                    config=self.config,
                )

        self.assertEqual(context.exception.status_code, 401)

    async def test_get_current_user_rejects_expired_cookie_token(self) -> None:
        user = await self._create_user()
        expired_config = load_auth_config(
            env={
                "JWT_SECRET": "test-secret-value",
                "ACCESS_TOKEN_EXPIRE_MINUTES": "1",
            }
        )
        token = create_access_token(
            user_id=user.id,
            role="user",
            config=expired_config,
            now=datetime.now(tz=timezone.utc) - timedelta(minutes=2),
        )

        async with self.session_factory() as session:
            with self.assertRaises(HTTPException) as context:
                await get_current_user_record(
                    session=session,
                    token=token,
                    config=expired_config,
                )

        self.assertEqual(context.exception.status_code, 401)

    async def test_logout_clears_auth_cookie(self) -> None:
        response = Response()

        with patch.dict("os.environ", {"JWT_SECRET": "test-secret-value"}, clear=True):
            result = await logout_user(response=response)

        self.assertEqual(result.status, "logged_out")
        set_cookie_header = response.headers["set-cookie"]
        self.assertIn("auth_token=", set_cookie_header)
        self.assertIn("Max-Age=0", set_cookie_header)
        self.assertIn("HttpOnly", set_cookie_header)


if __name__ == "__main__":
    unittest.main()
