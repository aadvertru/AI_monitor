from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi import HTTPException, Request
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.api.main import (
    ProfilePreferencesUpdateRequest,
    get_profile,
    update_profile_preferences,
)
from apps.api.security import create_access_token, load_auth_config
from libs.storage.models import Base, User, UserPreference, UserRole

AUTH_ENV = {"JWT_SECRET": "test-secret-value"}


class ProfileAPITests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def asyncTearDown(self) -> None:
        await self.engine.dispose()

    async def _create_user(self, email: str = "owner@example.com") -> User:
        async with self.session_factory() as session:
            user = User(
                email=email,
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

    async def test_get_profile_requires_authentication(self) -> None:
        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                self.assertRaises(HTTPException) as context,
            ):
                await get_profile(request=self._anonymous_request(), session=session)

        self.assertEqual(context.exception.status_code, 401)

    async def test_get_profile_returns_identity_demo_plan_usage_and_preferences(self) -> None:
        user = await self._create_user("owner@example.com")

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                response = await get_profile(
                    request=self._authenticated_request(user),
                    session=session,
                )

        self.assertEqual(response.user.id, user.id)
        self.assertEqual(response.user.email, "owner@example.com")
        self.assertIsNone(response.user.display_name)
        self.assertEqual(response.plan.name, "Starter")
        self.assertEqual(response.plan.status, "demo")
        self.assertTrue(response.plan.is_demo)
        self.assertEqual(response.usage.tokens_remaining, 10000)
        self.assertEqual(response.usage.tokens_total, 10000)
        self.assertTrue(response.usage.is_demo)
        self.assertEqual(response.preferences.locale, "en")
        self.assertTrue(response.preferences.email_notifications)
        self.assertTrue(response.preferences.audit_completed_notifications)
        self.assertFalse(response.preferences.provider_error_notifications)

        payload = response.model_dump(mode="json")
        serialized_keys = str(payload).lower()
        for unsafe_key in (
            "password",
            "hashed_password",
            "jwt",
            "secret",
            "api_key",
            "openai_api_key",
            "openrouter_api_key",
        ):
            self.assertNotIn(unsafe_key, serialized_keys)

    async def test_put_profile_preferences_requires_authentication(self) -> None:
        payload = ProfilePreferencesUpdateRequest.model_validate(
            {
                "locale": "ru",
                "email_notifications": False,
                "audit_completed_notifications": True,
                "provider_error_notifications": True,
            }
        )

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                self.assertRaises(HTTPException) as context,
            ):
                await update_profile_preferences(
                    payload=payload,
                    request=self._anonymous_request(),
                    session=session,
                )

        self.assertEqual(context.exception.status_code, 401)

    async def test_put_profile_preferences_updates_only_preferences(self) -> None:
        user = await self._create_user("owner@example.com")
        payload = ProfilePreferencesUpdateRequest.model_validate(
            {
                "locale": "ru",
                "email_notifications": False,
                "audit_completed_notifications": False,
                "provider_error_notifications": True,
            }
        )

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                response = await update_profile_preferences(
                    payload=payload,
                    request=self._authenticated_request(user),
                    session=session,
                )

            saved_user = await session.get(User, user.id)
            self.assertIsNotNone(saved_user)
            assert saved_user is not None
            self.assertEqual(saved_user.email, "owner@example.com")
            self.assertEqual(saved_user.hashed_password, "hashed-password")
            preferences = (
                await session.execute(
                    select(UserPreference).where(UserPreference.user_id == user.id)
                )
            ).scalars().one()

        self.assertEqual(response.user.email, "owner@example.com")
        self.assertEqual(response.preferences.locale, "ru")
        self.assertFalse(response.preferences.email_notifications)
        self.assertFalse(response.preferences.audit_completed_notifications)
        self.assertTrue(response.preferences.provider_error_notifications)
        self.assertEqual(preferences.locale, "ru")
        self.assertFalse(preferences.email_notifications)
        self.assertFalse(preferences.audit_completed_notifications)
        self.assertTrue(preferences.provider_error_notifications)

    def test_profile_preferences_reject_invalid_locale(self) -> None:
        with self.assertRaises(ValidationError):
            ProfilePreferencesUpdateRequest.model_validate(
                {
                    "locale": "de",
                    "email_notifications": True,
                    "audit_completed_notifications": True,
                    "provider_error_notifications": False,
                }
            )

    def test_profile_preferences_reject_identity_and_billing_fields(self) -> None:
        with self.assertRaises(ValidationError):
            ProfilePreferencesUpdateRequest.model_validate(
                {
                    "locale": "en",
                    "email_notifications": True,
                    "audit_completed_notifications": True,
                    "provider_error_notifications": False,
                    "email": "attacker@example.com",
                    "display_name": "Injected",
                    "plan": {"name": "Enterprise"},
                    "tokens_remaining": 999999,
                }
            )
