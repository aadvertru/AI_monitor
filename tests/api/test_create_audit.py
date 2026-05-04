from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi import HTTPException, Request
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.api.main import AuditCreateRequest, create_audit, update_audit
from apps.api.security import create_access_token, load_auth_config
from libs.storage.models import (
    Audit,
    AuditStatus,
    Base,
    Brand,
    Query,
    SeedQuerySource,
    SeedQueryType,
    User,
    UserRole,
)

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
                "brand_domain": "  Acme.AI/ ",
                "seed_queries": [
                    " best ai brand monitoring ",
                    "best ai brand monitoring",
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
            self.assertEqual([row.source for row in query_rows], [SeedQuerySource.USER] * 2)
            self.assertEqual([row.query_type for row in query_rows], [None, None])

    async def test_unauthenticated_create_audit_is_rejected(self) -> None:
        payload = AuditCreateRequest.model_validate(
            {
                "brand_name": "Acme AI",
                "providers": ["openai"],
                "runs_per_query": 1,
                "seed_queries": ["valid query"],
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

    def test_invalid_brand_domain_rejected(self) -> None:
        for brand_domain in (
            "https://example.com",
            "http://example.com",
            "example.com/page",
            "example.com?a=1",
            "localhost",
            "bad_domain",
        ):
            with self.subTest(brand_domain=brand_domain), self.assertRaises(ValidationError):
                AuditCreateRequest.model_validate(
                    {
                        "brand_name": "Acme",
                        "brand_domain": brand_domain,
                        "providers": ["openai"],
                        "runs_per_query": 1,
                        "seed_queries": ["valid query"],
                    }
                )

    def test_brand_description_length_is_limited(self) -> None:
        valid_payload = AuditCreateRequest.model_validate(
            {
                "brand_name": "Acme",
                "brand_description": "x" * 500,
                "providers": ["openai"],
                "runs_per_query": 1,
                "seed_queries": ["valid query"],
            }
        )
        self.assertEqual(valid_payload.brand_description, "x" * 500)

        with self.assertRaises(ValidationError):
            AuditCreateRequest.model_validate(
                {
                    "brand_name": "Acme",
                    "brand_description": "x" * 501,
                    "providers": ["openai"],
                    "runs_per_query": 1,
                    "seed_queries": ["valid query"],
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
                "seed_queries": ["valid query"],
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
                "seed_queries": ["valid query"],
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

    async def test_create_audit_accepts_canonical_seed_query_items(self) -> None:
        user = await self._create_user()
        payload = AuditCreateRequest.model_validate(
            {
                "brand_name": "Acme Typed",
                "providers": ["mock"],
                "runs_per_query": 1,
                "seed_query_items": [
                    {
                        "text": "What is Acme Typed?",
                        "type": "brand_direct",
                        "source": "ai",
                    },
                    {
                        "text": "Manual competitive query",
                    },
                ],
            }
        )

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                result = await create_audit(
                    payload=payload,
                    request=self._authenticated_request(user),
                    session=session,
                )

        self.assertEqual(
            result.seed_queries,
            ["What is Acme Typed?", "Manual competitive query"],
        )
        self.assertEqual(result.seed_query_items[0].source, "ai")
        self.assertEqual(result.seed_query_items[0].type, "brand_direct")
        self.assertEqual(result.seed_query_items[1].source, "user")
        self.assertIsNone(result.seed_query_items[1].type)

        async with self.session_factory() as session:
            query_rows = (
                await session.execute(
                    select(Query).where(Query.audit_id == result.audit_id).order_by(Query.id)
                )
            ).scalars().all()

        self.assertEqual(query_rows[0].text, "What is Acme Typed?")
        self.assertEqual(query_rows[0].source, SeedQuerySource.AI)
        self.assertEqual(query_rows[0].query_type, SeedQueryType.BRAND_DIRECT)
        self.assertEqual(query_rows[1].source, SeedQuerySource.USER)
        self.assertIsNone(query_rows[1].query_type)

    def test_seed_query_item_validation_rejects_unknown_type_or_source(self) -> None:
        for seed_query_item in (
            {"text": "Valid text", "type": "unknown", "source": "ai"},
            {"text": "Valid text", "type": "brand_direct", "source": "unknown"},
            {"text": "Valid text", "source": "ai"},
        ):
            with self.subTest(seed_query_item=seed_query_item), self.assertRaises(
                ValidationError
            ):
                AuditCreateRequest.model_validate(
                    {
                        "brand_name": "Acme",
                        "providers": ["mock"],
                        "runs_per_query": 1,
                        "seed_query_items": [seed_query_item],
                    }
                )

    def test_seed_query_field_conflict_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            AuditCreateRequest.model_validate(
                {
                    "brand_name": "Acme",
                    "providers": ["mock"],
                    "runs_per_query": 1,
                    "seed_queries": ["legacy query"],
                    "seed_query_items": [{"text": "typed query"}],
                }
            )

    def test_at_least_one_seed_query_is_required(self) -> None:
        for payload_fragment in (
            {},
            {"seed_queries": []},
            {"seed_query_items": []},
        ):
            with self.subTest(payload_fragment=payload_fragment), self.assertRaises(
                ValidationError
            ):
                AuditCreateRequest.model_validate(
                    {
                        "brand_name": "Acme",
                        "providers": ["mock"],
                        "runs_per_query": 1,
                        **payload_fragment,
                    }
                )

    def test_seed_query_count_limit_is_enforced(self) -> None:
        valid_payload = AuditCreateRequest.model_validate(
            {
                "brand_name": "Acme",
                "providers": ["mock"],
                "runs_per_query": 1,
                "seed_queries": [f"query {index}" for index in range(20)],
            }
        )
        self.assertEqual(len(valid_payload.seed_queries or []), 20)

        with self.assertRaises(ValidationError):
            AuditCreateRequest.model_validate(
                {
                    "brand_name": "Acme",
                    "providers": ["mock"],
                    "runs_per_query": 1,
                    "seed_queries": [f"query {index}" for index in range(21)],
                }
            )

        with self.assertRaises(ValidationError):
            AuditCreateRequest.model_validate(
                {
                    "brand_name": "Acme",
                    "providers": ["mock"],
                    "runs_per_query": 1,
                    "seed_query_items": [
                        {"text": f"query {index}"} for index in range(21)
                    ],
                }
            )

    def test_seed_query_text_validation_is_enforced(self) -> None:
        for seed_queries in ([""], ["   "], ["ab"], ["x" * 301]):
            with self.subTest(seed_queries=seed_queries), self.assertRaises(ValidationError):
                AuditCreateRequest.model_validate(
                    {
                        "brand_name": "Acme",
                        "providers": ["mock"],
                        "runs_per_query": 1,
                        "seed_queries": seed_queries,
                    }
                )

        for seed_query_item in (
            {"text": ""},
            {"text": "   "},
            {"text": "ab"},
            {"text": "x" * 301},
        ):
            with self.subTest(seed_query_item=seed_query_item), self.assertRaises(
                ValidationError
            ):
                AuditCreateRequest.model_validate(
                    {
                        "brand_name": "Acme",
                        "providers": ["mock"],
                        "runs_per_query": 1,
                        "seed_query_items": [seed_query_item],
                    }
                )

    def test_seed_query_text_normalization_is_conservative(self) -> None:
        payload = AuditCreateRequest.model_validate(
            {
                "brand_name": "Acme",
                "providers": ["mock"],
                "runs_per_query": 1,
                "seed_queries": ["  What   Is   Acme?  ", "what is acme?"],
            }
        )

        self.assertEqual(payload.seed_queries, ["What Is Acme?"])

    async def test_repeated_audits_reuse_existing_brand(self) -> None:
        user = await self._create_user()
        first_payload = AuditCreateRequest.model_validate(
            {
                "brand_name": "Acme AI",
                "providers": ["openai"],
                "runs_per_query": 1,
                "brand_domain": "acme.ai",
                "seed_queries": ["valid query"],
            }
        )
        second_payload = AuditCreateRequest.model_validate(
            {
                "brand_name": "  ACME AI  ",
                "providers": ["mock"],
                "runs_per_query": 1,
                "seed_queries": ["valid query"],
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
                "seed_queries": ["valid query"],
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

    async def test_created_audit_can_be_updated_before_run(self) -> None:
        user = await self._create_user()
        create_payload = AuditCreateRequest.model_validate(
            {
                "brand_name": "Acme AI",
                "brand_domain": "acme.ai",
                "providers": ["mock"],
                "runs_per_query": 1,
                "seed_queries": ["old query"],
            }
        )
        update_payload = AuditCreateRequest.model_validate(
            {
                "brand_name": "Acme Updated",
                "brand_domain": "updated.example",
                "brand_description": "Updated description.",
                "providers": ["openai"],
                "runs_per_query": 1,
                "language": "uk",
                "country": "UA",
                "locale": "uk-UA",
                "max_queries": 3,
                "seed_queries": ["new query", "another query"],
                "enable_source_intelligence": True,
                "scdl_level": "L2",
            }
        )

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                created = await create_audit(
                    payload=create_payload,
                    request=self._authenticated_request(user),
                    session=session,
                )

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                result = await update_audit(
                    audit_id=created.audit_id,
                    payload=update_payload,
                    request=self._authenticated_request(user),
                    session=session,
                )

        self.assertEqual(result.brand_name, "Acme Updated")
        self.assertEqual(result.brand_domain, "updated.example")
        self.assertEqual(result.brand_description, "Updated description.")
        self.assertEqual(result.providers, ["openai"])
        self.assertEqual(result.language, "uk")
        self.assertEqual(result.country, "UA")
        self.assertEqual(result.locale, "uk-UA")
        self.assertEqual(result.max_queries, 3)
        self.assertEqual(result.seed_queries, ["new query", "another query"])
        self.assertTrue(result.enable_source_intelligence)
        self.assertEqual(result.scdl_level, "L2")

        async with self.session_factory() as session:
            query_rows = (
                await session.execute(
                    select(Query).where(Query.audit_id == created.audit_id).order_by(Query.id)
                )
            ).scalars().all()
            self.assertEqual([row.text for row in query_rows], ["new query", "another query"])

    async def test_created_audit_can_be_updated_with_seed_query_items(self) -> None:
        user = await self._create_user()
        create_payload = AuditCreateRequest.model_validate(
            {
                "brand_name": "Acme AI",
                "providers": ["mock"],
                "runs_per_query": 1,
                "seed_queries": ["old query"],
            }
        )
        update_payload = AuditCreateRequest.model_validate(
            {
                "brand_name": "Acme AI",
                "providers": ["mock"],
                "runs_per_query": 1,
                "seed_query_items": [
                    {
                        "text": "Generated query",
                        "type": "recommendation",
                        "source": "ai",
                    }
                ],
            }
        )

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                created = await create_audit(
                    payload=create_payload,
                    request=self._authenticated_request(user),
                    session=session,
                )

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                result = await update_audit(
                    audit_id=created.audit_id,
                    payload=update_payload,
                    request=self._authenticated_request(user),
                    session=session,
                )

        self.assertEqual(result.seed_queries, ["Generated query"])
        self.assertEqual(result.seed_query_items[0].source, "ai")
        self.assertEqual(result.seed_query_items[0].type, "recommendation")

    async def test_non_created_audit_update_is_rejected(self) -> None:
        user = await self._create_user()
        payload = AuditCreateRequest.model_validate(
            {
                "brand_name": "Acme AI",
                "providers": ["mock"],
                "runs_per_query": 1,
                "seed_queries": ["valid query"],
            }
        )

        async with self.session_factory() as session:
            with patch.dict("os.environ", AUTH_ENV, clear=True):
                created = await create_audit(
                    payload=payload,
                    request=self._authenticated_request(user),
                    session=session,
                )

        async with self.session_factory() as session:
            audit = await session.get(Audit, created.audit_id)
            assert audit is not None
            audit.status = AuditStatus.COMPLETED
            await session.commit()

        async with self.session_factory() as session:
            with (
                patch.dict("os.environ", AUTH_ENV, clear=True),
                self.assertRaises(HTTPException) as context,
            ):
                await update_audit(
                    audit_id=created.audit_id,
                    payload=payload,
                    request=self._authenticated_request(user),
                    session=session,
                )

        self.assertEqual(context.exception.status_code, 409)


if __name__ == "__main__":
    unittest.main()
