"""API entrypoint for audit lifecycle operations."""

from __future__ import annotations

from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.database import get_db_session, init_models, should_auto_create_schema
from libs.control.query_capping import cap_queries
from libs.control.query_deduplication import deduplicate_queries
from libs.control.query_normalization import normalize_seed_queries
from libs.storage.models import Audit, AuditStatus, Brand, Query

SUPPORTED_PROVIDERS = frozenset({"mock", "openai", "anthropic", "gemini"})
MAX_BRAND_NAME_LENGTH = 255


class AuditCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    brand_name: str
    providers: list[str]
    runs_per_query: int = Field(ge=1, le=5)

    brand_domain: str | None = None
    brand_description: str | None = None

    language: str | None = None
    country: str | None = None
    locale: str | None = None
    max_queries: int | None = None
    seed_queries: list[str] | None = None
    enable_query_expansion: bool = False
    enable_source_intelligence: bool = False
    follow_up_depth: int = 0

    @field_validator("brand_name")
    @classmethod
    def validate_brand_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("brand_name must not be empty.")
        if len(normalized) > MAX_BRAND_NAME_LENGTH:
            raise ValueError(f"brand_name max length is {MAX_BRAND_NAME_LENGTH}.")
        return normalized

    @field_validator("providers")
    @classmethod
    def validate_providers(cls, value: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        invalid: list[str] = []

        for provider in value:
            code = provider.strip().lower()
            if not code or code not in SUPPORTED_PROVIDERS:
                invalid.append(provider)
                continue
            if code not in seen:
                seen.add(code)
                normalized.append(code)

        if invalid:
            raise ValueError("providers contains unsupported provider codes.")
        if not normalized:
            raise ValueError("providers must contain at least one supported provider.")
        return normalized

    @field_validator(
        "brand_domain",
        "brand_description",
        "language",
        "country",
        "locale",
    )
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("seed_queries")
    @classmethod
    def normalize_seed_queries(
        cls, value: list[str] | None, info: ValidationInfo
    ) -> list[str] | None:
        normalized = normalize_seed_queries(value)
        deduplicated = deduplicate_queries(normalized)
        capped = cap_queries(deduplicated, max_queries=info.data.get("max_queries"))
        return capped or None

    @field_validator("max_queries")
    @classmethod
    def validate_max_queries(cls, value: int | None) -> int | None:
        if value is None:
            return None
        if value <= 0:
            raise ValueError("max_queries must be greater than 0.")
        return value

    @field_validator("follow_up_depth")
    @classmethod
    def validate_follow_up_depth(cls, value: int) -> int:
        if value not in (0, 1):
            raise ValueError("follow_up_depth must be 0 or 1.")
        return value


class AuditCreateResponse(BaseModel):
    audit_id: int
    brand_id: int
    status: str
    providers: list[str]
    runs_per_query: int
    seed_queries: list[str]


async def create_audit_record(
    session: AsyncSession,
    payload: AuditCreateRequest,
) -> AuditCreateResponse:
    normalized_brand_name = payload.brand_name.lower()
    existing_brand_stmt = (
        select(Brand)
        .where(func.lower(Brand.name) == normalized_brand_name)
        .order_by(Brand.id)
    )
    brand = (await session.execute(existing_brand_stmt)).scalars().first()
    if brand is None:
        brand = Brand(
            name=payload.brand_name,
            domain=payload.brand_domain,
            description=payload.brand_description,
        )
        session.add(brand)
    else:
        if brand.domain is None and payload.brand_domain is not None:
            brand.domain = payload.brand_domain
        if brand.description is None and payload.brand_description is not None:
            brand.description = payload.brand_description

    audit = Audit(
        brand=brand,
        status=AuditStatus.CREATED,
        providers=payload.providers,
        runs_per_query=payload.runs_per_query,
        language=payload.language,
        country=payload.country,
        locale=payload.locale,
        max_queries=payload.max_queries,
        enable_query_expansion=payload.enable_query_expansion,
        enable_source_intelligence=payload.enable_source_intelligence,
        follow_up_depth=payload.follow_up_depth,
    )
    session.add(audit)
    await session.flush()

    seed_queries = payload.seed_queries or []
    for query_text in seed_queries:
        session.add(Query(audit_id=audit.id, text=query_text))

    await session.commit()
    await session.refresh(audit)

    return AuditCreateResponse(
        audit_id=audit.id,
        brand_id=audit.brand_id,
        status=audit.status.value,
        providers=audit.providers,
        runs_per_query=audit.runs_per_query,
        seed_queries=seed_queries,
    )


app = FastAPI(title="AI Brand Visibility Monitor API")


@app.on_event("startup")
async def on_startup() -> None:
    if should_auto_create_schema():
        await init_models()


@app.post("/audits", response_model=AuditCreateResponse)
async def create_audit(
    payload: AuditCreateRequest,
    session: AsyncSession = Depends(get_db_session),
) -> Any:
    try:
        return await create_audit_record(session, payload)
    except SQLAlchemyError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to persist audit.",
        ) from exc

