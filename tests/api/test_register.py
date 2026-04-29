from __future__ import annotations

import unittest

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.api.main import RegisterRequest, register_user
from apps.api.security import verify_password
from libs.storage.models import Base, User, UserRole


class RegisterAPITests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def asyncTearDown(self) -> None:
        await self.engine.dispose()

    async def test_register_creates_user_with_safe_response(self) -> None:
        payload = RegisterRequest.model_validate(
            {
                "email": "  USER@Example.COM  ",
                "password": "plain-password",
            }
        )

        async with self.session_factory() as session:
            response = await register_user(payload=payload, session=session)

        self.assertIsNotNone(response.id)
        self.assertEqual(response.email, "user@example.com")
        self.assertEqual(response.role, "user")
        self.assertNotIn("password", response.model_dump())
        self.assertNotIn("hashed_password", response.model_dump())
        self.assertNotIn("access_token", response.model_dump())

    async def test_register_hashes_stored_password(self) -> None:
        payload = RegisterRequest.model_validate(
            {
                "email": "user@example.com",
                "password": "plain-password",
            }
        )

        async with self.session_factory() as session:
            response = await register_user(payload=payload, session=session)

        async with self.session_factory() as session:
            user = await session.get(User, response.id)
            self.assertIsNotNone(user)
            assert user is not None
            self.assertNotEqual(user.hashed_password, "plain-password")
            self.assertTrue(verify_password("plain-password", user.hashed_password))

    async def test_register_rejects_duplicate_email(self) -> None:
        payload = RegisterRequest.model_validate(
            {
                "email": "user@example.com",
                "password": "plain-password",
            }
        )

        async with self.session_factory() as session:
            await register_user(payload=payload, session=session)

        async with self.session_factory() as session:
            with self.assertRaises(HTTPException) as context:
                await register_user(payload=payload, session=session)

        self.assertEqual(context.exception.status_code, 409)
        self.assertEqual(context.exception.detail, "Email is already registered.")

    def test_register_rejects_invalid_email(self) -> None:
        with self.assertRaises(ValidationError):
            RegisterRequest.model_validate(
                {
                    "email": "not-an-email",
                    "password": "plain-password",
                }
            )

    def test_register_rejects_missing_password(self) -> None:
        with self.assertRaises(ValidationError):
            RegisterRequest.model_validate({"email": "user@example.com"})

    async def test_register_assigns_default_user_role(self) -> None:
        payload = RegisterRequest.model_validate(
            {
                "email": "user@example.com",
                "password": "plain-password",
            }
        )

        async with self.session_factory() as session:
            response = await register_user(payload=payload, session=session)

        async with self.session_factory() as session:
            users = (await session.execute(select(User))).scalars().all()

        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].id, response.id)
        self.assertEqual(users[0].role, UserRole.USER)


if __name__ == "__main__":
    unittest.main()
