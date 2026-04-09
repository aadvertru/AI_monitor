from __future__ import annotations

import unittest

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from apps.api.main import AuditCreateRequest, create_audit
from libs.storage.models import Audit, Brand, Query


class CreateAuditAPITests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Brand.metadata.create_all)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def asyncTearDown(self) -> None:
        await self.engine.dispose()

    async def test_valid_input_creates_audit(self) -> None:
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
            result = await create_audit(payload=payload, session=session)

        self.assertIsNotNone(result.audit_id)
        self.assertEqual(result.status, "created")
        self.assertEqual(result.providers, ["openai", "mock"])
        self.assertEqual(result.runs_per_query, 2)
        self.assertEqual(
            result.seed_queries,
            [
                "best ai brand monitoring",
                "best ai brand monitoring",
                "how to monitor brand visibility",
            ],
        )

        async with self.session_factory() as session:
            saved_audit = await session.get(Audit, result.audit_id)
            self.assertIsNotNone(saved_audit)
            assert saved_audit is not None
            self.assertEqual(saved_audit.providers, ["openai", "mock"])

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
                    "best ai brand monitoring",
                    "how to monitor brand visibility",
                ],
            )

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


if __name__ == "__main__":
    unittest.main()
