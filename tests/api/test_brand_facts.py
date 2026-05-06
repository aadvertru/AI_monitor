from __future__ import annotations

import unittest

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.api.main import AuditCreateRequest, create_audit_record, update_audit_record
from libs.evaluation.brand_facts import (
    build_brand_fact_drafts,
    list_brand_facts_for_audit,
)
from libs.storage.models import (
    Audit,
    AuditStatus,
    Base,
    Brand,
    BrandFact,
    BrandFactSource,
    BrandFactType,
    SCDLLevel,
    User,
    UserRole,
)


class BrandFactTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def asyncTearDown(self) -> None:
        await self.engine.dispose()

    async def test_brand_fact_requires_audit_id(self) -> None:
        async with self.session_factory() as session:
            fact = BrandFact(
                fact_text="Brand name: Acme",
                fact_type=BrandFactType.BRAND_NAME,
                source=BrandFactSource.BRAND_NAME,
                confidence=1.0,
            )
            session.add(fact)

            with self.assertRaises(IntegrityError):
                await session.flush()

    async def test_fact_drafts_are_conservative_and_source_labelled(self) -> None:
        brand = Brand(
            name="  Acme AI  ",
            domain=" acme.example/ ",
            description="  AI visibility monitoring.  ",
        )

        drafts = build_brand_fact_drafts(brand)

        self.assertEqual(
            [(draft.fact_type.value, draft.source.value) for draft in drafts],
            [
                ("brand_name", "brand_name"),
                ("official_domain", "brand_domain"),
                ("description_claim", "brand_description"),
            ],
        )
        self.assertEqual(
            [draft.fact_text for draft in drafts],
            [
                "Brand name: Acme AI",
                "Official domain: acme.example/",
                "AI visibility monitoring.",
            ],
        )

    async def test_empty_description_does_not_create_unsupported_fact(self) -> None:
        brand = Brand(name="Acme AI", domain="acme.example", description="  ")

        drafts = build_brand_fact_drafts(brand)

        self.assertEqual([draft.fact_type for draft in drafts], [
            BrandFactType.BRAND_NAME,
            BrandFactType.OFFICIAL_DOMAIN,
        ])

    async def test_create_audit_creates_audit_scoped_brand_fact_snapshot(self) -> None:
        async with self.session_factory() as session:
            user = User(email="owner@example.com", hashed_password="hashed", role=UserRole.USER)
            session.add(user)
            await session.commit()
            await session.refresh(user)

            audit_response = await create_audit_record(
                session,
                AuditCreateRequest(
                    brand_name="Acme AI",
                    brand_domain="acme.example",
                    brand_description="AI visibility monitoring.",
                    providers=["mock"],
                    runs_per_query=1,
                    seed_queries=["best ai visibility tools"],
                ),
                user_id=user.id,
            )
            facts = await list_brand_facts_for_audit(session, audit_response.audit_id)

        self.assertEqual(len(facts), 3)
        self.assertTrue(all(fact.audit_id == audit_response.audit_id for fact in facts))
        self.assertTrue(all(fact.brand_id == audit_response.brand_id for fact in facts))
        self.assertEqual(
            [(fact.fact_type.value, fact.source.value) for fact in facts],
            [
                ("brand_name", "brand_name"),
                ("official_domain", "brand_domain"),
                ("description_claim", "brand_description"),
            ],
        )

    async def test_old_audit_facts_do_not_change_when_brand_changes_later(self) -> None:
        async with self.session_factory() as session:
            brand = Brand(
                name="Acme AI",
                domain="acme.example",
                description="Original description.",
            )
            audit = Audit(
                brand=brand,
                user_id=None,
                status=AuditStatus.CREATED,
                providers=["mock"],
                runs_per_query=1,
                scdl_level=SCDLLevel.L1,
            )
            session.add(audit)
            await session.flush()
            session.add(
                BrandFact(
                    audit_id=audit.id,
                    brand_id=brand.id,
                    fact_text="Original description.",
                    fact_type=BrandFactType.DESCRIPTION_CLAIM,
                    source=BrandFactSource.BRAND_DESCRIPTION,
                    confidence=None,
                )
            )
            await session.commit()

            brand.description = "Changed future description."
            await session.commit()

            facts = await list_brand_facts_for_audit(session, audit.id)

        self.assertEqual([fact.fact_text for fact in facts], ["Original description."])

    async def test_update_created_audit_explicitly_regenerates_fact_snapshot(self) -> None:
        async with self.session_factory() as session:
            user = User(email="owner@example.com", hashed_password="hashed", role=UserRole.USER)
            session.add(user)
            await session.commit()
            await session.refresh(user)

            created = await create_audit_record(
                session,
                AuditCreateRequest(
                    brand_name="Regenerate AI",
                    brand_domain="regen.example",
                    brand_description="Original.",
                    providers=["mock"],
                    runs_per_query=1,
                    seed_queries=["original query"],
                ),
                user_id=user.id,
            )
            audit = (
                await session.execute(select(Audit).where(Audit.id == created.audit_id))
            ).scalar_one()
            updated = await update_audit_record(
                session,
                audit,
                AuditCreateRequest(
                    brand_name="Regenerate AI",
                    brand_domain="regen.example",
                    brand_description="Updated.",
                    providers=["mock"],
                    runs_per_query=1,
                    seed_queries=["updated query"],
                ),
            )
            facts = await list_brand_facts_for_audit(session, updated.audit_id)

        self.assertIn("Updated.", [fact.fact_text for fact in facts])
        self.assertNotIn("Original.", [fact.fact_text for fact in facts])


if __name__ == "__main__":
    unittest.main()
