"""Audit-scoped brand fact snapshot helpers."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from libs.storage.models import (
    Audit,
    Brand,
    BrandFact,
    BrandFactSource,
    BrandFactType,
)


@dataclass(frozen=True)
class BrandFactDraft:
    fact_text: str
    fact_type: BrandFactType
    source: BrandFactSource
    confidence: float | None = None


def build_brand_fact_drafts(brand: Brand) -> list[BrandFactDraft]:
    return build_brand_fact_drafts_from_values(
        brand_name=brand.name,
        brand_domain=brand.domain,
        brand_description=brand.description,
    )


def build_brand_fact_drafts_from_values(
    *,
    brand_name: str | None,
    brand_domain: str | None,
    brand_description: str | None,
) -> list[BrandFactDraft]:
    drafts: list[BrandFactDraft] = []

    name = _clean_fact_text(brand_name)
    if name:
        drafts.append(
            BrandFactDraft(
                fact_text=f"Brand name: {name}",
                fact_type=BrandFactType.BRAND_NAME,
                source=BrandFactSource.BRAND_NAME,
                confidence=1.0,
            )
        )

    domain = _clean_fact_text(brand_domain)
    if domain:
        drafts.append(
            BrandFactDraft(
                fact_text=f"Official domain: {domain}",
                fact_type=BrandFactType.OFFICIAL_DOMAIN,
                source=BrandFactSource.BRAND_DOMAIN,
                confidence=1.0,
            )
        )

    description = _clean_fact_text(brand_description)
    if description:
        drafts.append(
            BrandFactDraft(
                fact_text=description,
                fact_type=BrandFactType.DESCRIPTION_CLAIM,
                source=BrandFactSource.BRAND_DESCRIPTION,
                confidence=None,
            )
        )

    return drafts


async def create_brand_facts_for_audit(
    session: AsyncSession,
    audit: Audit,
    brand: Brand,
    *,
    brand_name: str | None = None,
    brand_domain: str | None = None,
    brand_description: str | None = None,
) -> list[BrandFact]:
    facts = [
        BrandFact(
            audit_id=audit.id,
            brand_id=brand.id,
            fact_text=draft.fact_text,
            fact_type=draft.fact_type,
            source=draft.source,
            confidence=draft.confidence,
        )
        for draft in build_brand_fact_drafts_from_values(
            brand_name=brand_name if brand_name is not None else brand.name,
            brand_domain=brand_domain if brand_domain is not None else brand.domain,
            brand_description=(
                brand_description if brand_description is not None else brand.description
            ),
        )
    ]
    session.add_all(facts)
    return facts


async def replace_brand_facts_for_audit(
    session: AsyncSession,
    audit: Audit,
    brand: Brand,
    *,
    brand_name: str | None = None,
    brand_domain: str | None = None,
    brand_description: str | None = None,
) -> list[BrandFact]:
    await session.execute(delete(BrandFact).where(BrandFact.audit_id == audit.id))
    return await create_brand_facts_for_audit(
        session,
        audit,
        brand,
        brand_name=brand_name,
        brand_domain=brand_domain,
        brand_description=brand_description,
    )


async def list_brand_facts_for_audit(
    session: AsyncSession,
    audit_id: int,
) -> list[BrandFact]:
    rows = (
        await session.execute(
            select(BrandFact).where(BrandFact.audit_id == audit_id).order_by(BrandFact.id)
        )
    ).scalars()
    return list(rows)


def _clean_fact_text(value: str | None) -> str:
    return " ".join((value or "").strip().split())
