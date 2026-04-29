from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi import HTTPException, Request
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.api.main import AuditCreateRequest, create_audit
from apps.api.security import create_access_token, load_auth_config
from libs.storage.models import Audit, Base, Brand, Query, User, UserRole

AUTH_ENV = {"JWT_SECRET": "test-secret-value"}


class CreateAuditAPITests(unittest.IsolatedAsyncioTestCase):
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

    async def test_valid_input_creates_audit(self) -> None:
        user = await self._create_user()
        payload = AuditCreateRequest.model_validate(
            {
                "brand_name": "  Acme AI  ",
                "providers": ["openai", "OPENAI", "mock"],
                "runs_per_query": 2,
                "brand_domain": "  acme.ai ",
                "seed_queries": [
                    " best ai brand monitoring ",
                    "best ai brand monitoring",
                    "",
                    "  how to monitor brand visibility  ",
                ],
                "max_queries": 20,
                "follow_up_depth": 1,
            }
        )

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                result = await create_audit(
                    payload=payload,
                    request=self._authenticated_request(user),
                    session=session,
                )

        self.assertIsNotNone(result.audit_id)
        self.assertEqual(result.status, "created")
        self.assertEqual(result.providers, ["openai", "mock"])
        self.assertEqual(result.runs_per_query, 2)
        self.assertEqual(result.scdl_level, "L1")
        self.assertEqual(
            result.seed_queries,
            [
                "best ai brand monitoring",
                "how to monitor brand visibility",
            ],
        )

        async with self.session_factory() as session:
            saved_audit = await session.get(Audit, result.audit_id)
            self.assertIsNotNone(saved_audit)
            assert saved_audit is not None
            self.assertEqual(saved_audit.providers, ["openai", "mock"])
            self.assertEqual(saved_audit.user_id, user.id)
            self.assertEqual(saved_audit.scdl_level.value, "L1")

            brand = await session.get(Brand, saved_audit.brand_id)
            self.assertIsNotNone(brand)
            assert brand is not None
            self.assertEqual(brand.name, "Acme AI")
            self.assertEqual(brand.domain, "acme.ai")

            query_rows = (
                await session.execute(
                    select(Query).where(Query.audit_id == saved_audit.id).order_by(Query.id)
                )
            ).scalars().all()
            self.assertEqual(
                [row.text for row in query_rows],
                [
                    "best ai brand monitoring",
                    "how to monitor brand visibility",
                ],
            )

    async def test_unauthenticated_create_audit_is_rejected(self) -> None:
        payload = AuditCreateRequest.model_validate(
            {
                "brand_name": "Acme AI",
                "providers": ["openai"],
                "runs_per_query": 1,
            }
        )

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                self.assertRaises(HTTPException) as context,
            ):
                await create_audit(
                    payload=payload,
                    request=self._anonymous_request(),
                    session=session,
                )

        self.assertEqual(context.exception.status_code, 401)

    async def test_empty_brand_name_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            AuditCreateRequest.model_validate(
                {
                    "brand_name": "   ",
                    "providers": ["openai"],
                    "runs_per_query": 1,
                }
            )

    async def test_invalid_provider_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            AuditCreateRequest.model_validate(
                {
                    "brand_name": "Acme",
                    "providers": ["openai", "unknown_provider"],
                    "runs_per_query": 1,
                }
            )

    async def test_invalid_runs_per_query_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            AuditCreateRequest.model_validate(
                {
                    "brand_name": "Acme",
                    "providers": ["openai"],
                    "runs_per_query": 6,
                }
            )

    def test_invalid_scdl_level_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            AuditCreateRequest.model_validate(
                {
                    "brand_name": "Acme",
                    "providers": ["openai"],
                    "runs_per_query": 1,
                    "scdl_level": "L3",
                }
            )

    async def test_create_audit_accepts_and_persists_l1_scdl_level(self) -> None:
        user = await self._create_user()
        payload = AuditCreateRequest.model_validate(
            {
                "brand_name": "Acme L1",
                "providers": ["mock"],
                "runs_per_query": 1,
                "scdl_level": "L1",
            }
        )

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                result = await create_audit(
                    payload=payload,
                    request=self._authenticated_request(user),
                    session=session,
                )

        self.assertEqual(result.scdl_level, "L1")
        async with self.session_factory() as session:
            saved_audit = await session.get(Audit, result.audit_id)
        assert saved_audit is not None
        self.assertEqual(saved_audit.scdl_level.value, "L1")

    async def test_create_audit_accepts_and_persists_l2_scdl_level(self) -> None:
        user = await self._create_user()
        payload = AuditCreateRequest.model_validate(
            {
                "brand_name": "Acme L2",
                "providers": ["mock"],
                "runs_per_query": 1,
                "scdl_level": "L2",
            }
        )

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                result = await create_audit(
                    payload=payload,
                    request=self._authenticated_request(user),
                    session=session,
                )

        self.assertEqual(result.scdl_level, "L2")
        async with self.session_factory() as session:
            saved_audit = await session.get(Audit, result.audit_id)
        assert saved_audit is not None
        self.assertEqual(saved_audit.scdl_level.value, "L2")

    async def test_repeated_audits_reuse_existing_brand(self) -> None:
        user = await self._create_user()
        first_payload = AuditCreateRequest.model_validate(
            {
                "brand_name": "Acme AI",
                "providers": ["openai"],
                "runs_per_query": 1,
                "brand_domain": "acme.ai",
            }
        )
        second_payload = AuditCreateRequest.model_validate(
            {
                "brand_name": "  ACME AI  ",
                "providers": ["mock"],
                "runs_per_query": 1,
            }
        )

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                first_result = await create_audit(
                    payload=first_payload,
                    request=self._authenticated_request(user),
                    session=session,
                )

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                second_result = await create_audit(
                    payload=second_payload,
                    request=self._authenticated_request(user),
                    session=session,
                )

        self.assertEqual(first_result.brand_id, second_result.brand_id)

        async with self.session_factory() as session:
            brands = (await session.execute(select(Brand).order_by(Brand.id))).scalars().all()
            self.assertEqual(len(brands), 1)
            self.assertEqual(brands[0].name, "Acme AI")

    async def test_created_audit_is_not_assigned_to_another_user(self) -> None:
        owner = await self._create_user("owner@example.com")
        other_user = await self._create_user("other@example.com")
        payload = AuditCreateRequest.model_validate(
            {
                "brand_name": "Acme AI",
                "providers": ["openai"],
                "runs_per_query": 1,
            }
        )

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                result = await create_audit(
                    payload=payload,
                    request=self._authenticated_request(owner),
                    session=session,
                )

        async with self.session_factory() as session:
            saved_audit = await session.get(Audit, result.audit_id)
            self.assertIsNotNone(saved_audit)
            assert saved_audit is not None
            self.assertEqual(saved_audit.user_id, owner.id)
            self.assertNotEqual(saved_audit.user_id, other_user.id)


if __name__ == "__main__":
    unittest.main()
