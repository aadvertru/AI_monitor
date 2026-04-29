"""API entrypoint for audit lifecycle operations."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, Literal

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.audit_schemas import (
    AuditDetailResponse,
    AuditListItemResponse,
    AuditResultRowResponse,
    AuditResultsResponse,
    AuditRunTriggerResponse,
    AuditStatusResponse,
    AuditSummaryResponse,
    CompetitorSummaryItemResponse,
    ComponentScoresResponse,
    CriticalQueryItemResponse,
    SourceSummaryItemResponse,
)
from apps.api.database import get_db_session, init_models, should_auto_create_schema
from apps.api.security import (
    AuthConfig,
    AuthConfigError,
    AuthTokenError,
    configure_cors,
    create_access_token,
    hash_password,
    load_auth_config,
    verify_access_token,
    verify_password,
)
from libs.analysis.aggregation import build_audit_summary, find_critical_queries
from libs.control.job_scheduler import schedule_jobs_for_audit
from libs.control.query_capping import cap_queries
from libs.control.query_deduplication import deduplicate_queries
from libs.control.query_normalization import normalize_seed_queries
from libs.storage.models import (
    Audit,
    AuditStatus,
    Brand,
    Job,
    ParsedResult,
    Query,
    RawResponse,
    Run,
    RunStatus,
    SCDLLevel,
    Score,
    User,
    UserRole,
)

SUPPORTED_PROVIDERS = frozenset({"mock", "openai", "anthropic", "gemini"})
MAX_BRAND_NAME_LENGTH = 255
MAX_EMAIL_LENGTH = 255
DB_SESSION_DEPENDENCY = Depends(get_db_session)
UNAUTHORIZED_DETAIL = "Invalid authentication credentials."
AUDIT_NOT_FOUND_DETAIL = "Audit was not found."
AUDIT_RUNNING_DETAIL = "Audit is already running."
AUDIT_NOT_TRIGGERABLE_DETAIL = "Audit can only be triggered from the created state."
AUDIT_NOT_RUNNABLE_DETAIL = "Audit has no runnable query/provider combinations."


def normalize_email(value: str) -> str:
    normalized = value.strip().lower()
    if not normalized:
        raise ValueError("email must not be empty.")
    if len(normalized) > MAX_EMAIL_LENGTH:
        raise ValueError(f"email max length is {MAX_EMAIL_LENGTH}.")
    if "@" not in normalized:
        raise ValueError("email must be valid.")
    local_part, domain = normalized.rsplit("@", 1)
    if not local_part or "." not in domain or domain.startswith(".") or domain.endswith("."):
        raise ValueError("email must be valid.")
    return normalized


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
    scdl_level: Literal["L1", "L2"] = "L1"

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
    audit_number: int
    brand_id: int
    status: str
    providers: list[str]
    runs_per_query: int
    scdl_level: str
    seed_queries: list[str]


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return normalize_email(value)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not value:
            raise ValueError("password must not be empty.")
        return value


class UserResponse(BaseModel):
    id: int
    email: str
    role: str


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return normalize_email(value)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not value:
            raise ValueError("password must not be empty.")
        return value


class LogoutResponse(BaseModel):
    status: str


def build_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        role=user.role.value,
    )


async def create_audit_record(
    session: AsyncSession,
    payload: AuditCreateRequest,
    user_id: int,
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
        user_id=user_id,
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
        scdl_level=SCDLLevel(payload.scdl_level),
    )
    session.add(audit)
    await session.flush()

    seed_queries = payload.seed_queries or []
    for query_text in seed_queries:
        session.add(Query(audit_id=audit.id, text=query_text))

    await session.commit()
    await session.refresh(audit)
    audit_number = await get_relative_audit_number(session, audit)

    return AuditCreateResponse(
        audit_id=audit.id,
        audit_number=audit_number,
        brand_id=audit.brand_id,
        status=audit.status.value,
        providers=audit.providers,
        runs_per_query=audit.runs_per_query,
        scdl_level=audit.scdl_level.value,
        seed_queries=seed_queries,
    )


async def register_user_record(
    session: AsyncSession,
    payload: RegisterRequest,
) -> UserResponse:
    existing_user_stmt = select(User).where(User.email == payload.email)
    existing_user = (await session.execute(existing_user_stmt)).scalars().first()
    if existing_user is not None:
        raise HTTPException(status_code=409, detail="Email is already registered.")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=UserRole.USER,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return build_user_response(user)


def set_auth_cookie(response: Response, token: str, config: AuthConfig) -> None:
    response.set_cookie(
        key=config.cookie.name,
        value=token,
        max_age=config.cookie.max_age_seconds,
        httponly=config.cookie.httponly,
        secure=config.cookie.secure,
        samesite=config.cookie.samesite,
        path=config.cookie.path,
    )


def clear_auth_cookie(response: Response, config: AuthConfig) -> None:
    response.delete_cookie(
        key=config.cookie.name,
        path=config.cookie.path,
        secure=config.cookie.secure,
        httponly=config.cookie.httponly,
        samesite=config.cookie.samesite,
    )


async def login_user_record(
    session: AsyncSession,
    payload: LoginRequest,
    response: Response,
    config: AuthConfig,
) -> UserResponse:
    user_stmt = select(User).where(User.email == payload.email)
    user = (await session.execute(user_stmt)).scalars().first()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail=UNAUTHORIZED_DETAIL)

    token = create_access_token(
        user_id=user.id,
        role=user.role.value,
        config=config,
    )
    set_auth_cookie(response=response, token=token, config=config)
    return build_user_response(user)


async def get_current_user_record(
    session: AsyncSession,
    token: str | None,
    config: AuthConfig,
) -> UserResponse:
    if not token:
        raise HTTPException(status_code=401, detail=UNAUTHORIZED_DETAIL)

    try:
        claims = verify_access_token(token, config=config)
    except AuthTokenError as exc:
        raise HTTPException(status_code=401, detail=UNAUTHORIZED_DETAIL) from exc

    user = await session.get(User, claims.user_id)
    if user is None:
        raise HTTPException(status_code=401, detail=UNAUTHORIZED_DETAIL)
    return build_user_response(user)


async def get_authenticated_user_from_request(
    session: AsyncSession,
    request: Request,
) -> UserResponse:
    config = get_runtime_auth_config()
    return await get_current_user_record(
        session=session,
        token=request.cookies.get(config.cookie.name),
        config=config,
    )


def get_runtime_auth_config() -> AuthConfig:
    try:
        return load_auth_config()
    except AuthConfigError as exc:
        raise HTTPException(status_code=500, detail="Auth configuration is invalid.") from exc


def _is_admin(user: UserResponse) -> bool:
    return user.role == UserRole.ADMIN.value


def _status_value(status: object) -> str:
    return status.value if hasattr(status, "value") else str(status)


def _run_status_value(status: object) -> str:
    return status.value if hasattr(status, "value") else str(status)


def _scdl_level_value(level: object) -> str:
    return level.value if hasattr(level, "value") else str(level)


async def get_relative_audit_number(session: AsyncSession, audit: Audit) -> int:
    owner_filter = (
        Audit.user_id.is_(None) if audit.user_id is None else Audit.user_id == audit.user_id
    )
    return (
        await session.execute(
            select(func.count()).select_from(Audit).where(owner_filter, Audit.id <= audit.id)
        )
    ).scalar_one()


def relative_audit_numbers(audits: list[Audit]) -> dict[int, int]:
    grouped: dict[int | None, list[Audit]] = defaultdict(list)
    for audit in audits:
        grouped[audit.user_id].append(audit)

    numbers: dict[int, int] = {}
    for owner_audits in grouped.values():
        for index, audit in enumerate(sorted(owner_audits, key=lambda item: item.id), start=1):
            numbers[audit.id] = index
    return numbers


async def load_accessible_audit(
    session: AsyncSession,
    audit_id: int,
    current_user: UserResponse,
) -> tuple[Audit, Brand]:
    stmt = select(Audit, Brand).join(Brand, Audit.brand_id == Brand.id).where(
        Audit.id == audit_id
    )
    if not _is_admin(current_user):
        stmt = stmt.where(Audit.user_id == current_user.id)

    row = (await session.execute(stmt)).first()
    if row is None:
        raise HTTPException(status_code=404, detail=AUDIT_NOT_FOUND_DETAIL)
    audit, brand = row
    return audit, brand


async def build_audit_detail_response(
    session: AsyncSession,
    audit: Audit,
    brand: Brand,
) -> AuditDetailResponse:
    audit_number = await get_relative_audit_number(session, audit)
    queries = (
        await session.execute(
            select(Query.text).where(Query.audit_id == audit.id).order_by(Query.id)
        )
    ).scalars().all()
    return AuditDetailResponse(
        audit_id=audit.id,
        audit_number=audit_number,
        brand_id=brand.id,
        brand_name=brand.name,
        brand_domain=brand.domain,
        brand_description=brand.description,
        status=_status_value(audit.status),
        scdl_level=_scdl_level_value(audit.scdl_level),
        providers=audit.providers,
        runs_per_query=audit.runs_per_query,
        language=audit.language,
        country=audit.country,
        locale=audit.locale,
        max_queries=audit.max_queries,
        seed_queries=list(queries),
        enable_query_expansion=audit.enable_query_expansion,
        enable_source_intelligence=audit.enable_source_intelligence,
        follow_up_depth=audit.follow_up_depth,
        created_at=audit.created_at,
        updated_at=audit.updated_at,
    )


async def list_audit_records(
    session: AsyncSession,
    current_user: UserResponse,
) -> list[AuditListItemResponse]:
    stmt = (
        select(Audit, Brand)
        .join(Brand, Audit.brand_id == Brand.id)
        .order_by(Audit.created_at.desc(), Audit.id.desc())
    )
    if not _is_admin(current_user):
        stmt = stmt.where(Audit.user_id == current_user.id)

    rows = (await session.execute(stmt)).all()
    audit_numbers = relative_audit_numbers([audit for audit, _brand in rows])
    return [
        AuditListItemResponse(
            audit_id=audit.id,
            audit_number=audit_numbers[audit.id],
            brand_name=brand.name,
            brand_domain=brand.domain,
            status=_status_value(audit.status),
            scdl_level=_scdl_level_value(audit.scdl_level),
            providers=audit.providers,
            runs_per_query=audit.runs_per_query,
            created_at=audit.created_at,
            updated_at=audit.updated_at,
        )
        for audit, brand in rows
    ]


async def get_expected_run_count(session: AsyncSession, audit: Audit) -> int:
    query_stmt = select(Query.id).where(Query.audit_id == audit.id).order_by(Query.id)
    query_ids = list((await session.execute(query_stmt)).scalars().all())
    if audit.max_queries is not None:
        query_ids = query_ids[: audit.max_queries]
    return len(query_ids) * len(audit.providers or []) * audit.runs_per_query


async def build_audit_status_response(
    session: AsyncSession,
    audit: Audit,
) -> AuditStatusResponse:
    audit_number = await get_relative_audit_number(session, audit)
    run_statuses = list(
        (
            await session.execute(
                select(Run.status).where(Run.audit_id == audit.id).order_by(Run.id)
            )
        ).scalars().all()
    )
    expected_runs = await get_expected_run_count(session, audit)
    total_runs = max(expected_runs, len(run_statuses))
    terminal_statuses = {
        RunStatus.SUCCESS,
        RunStatus.ERROR,
        RunStatus.TIMEOUT,
        RunStatus.RATE_LIMITED,
    }
    failed_statuses = {RunStatus.ERROR, RunStatus.TIMEOUT, RunStatus.RATE_LIMITED}
    completed_runs = sum(1 for status in run_statuses if status in terminal_statuses)
    failed_runs = sum(1 for status in run_statuses if status in failed_statuses)
    completion_ratio = completed_runs / total_runs if total_runs else 0.0

    return AuditStatusResponse(
        audit_id=audit.id,
        audit_number=audit_number,
        status=_status_value(audit.status),
        scdl_level=_scdl_level_value(audit.scdl_level),
        total_runs=total_runs,
        completed_runs=completed_runs,
        failed_runs=failed_runs,
        completion_ratio=round(completion_ratio, 4),
        updated_at=audit.updated_at,
    )


async def trigger_audit_run_record(
    session: AsyncSession,
    audit: Audit,
) -> AuditRunTriggerResponse:
    audit_number = await get_relative_audit_number(session, audit)
    if audit.status == AuditStatus.RUNNING:
        raise HTTPException(status_code=409, detail=AUDIT_RUNNING_DETAIL)
    if audit.status != AuditStatus.CREATED:
        raise HTTPException(status_code=409, detail=AUDIT_NOT_TRIGGERABLE_DETAIL)

    expected_runs = await get_expected_run_count(session, audit)
    if expected_runs == 0:
        raise HTTPException(status_code=400, detail=AUDIT_NOT_RUNNABLE_DETAIL)

    scheduled_jobs = await session.run_sync(
        lambda sync_session: len(
            schedule_jobs_for_audit(sync_session, audit.id, commit=False)
        )
    )

    audit.status = AuditStatus.RUNNING
    await session.commit()
    await session.refresh(audit)

    total_jobs = (
        await session.execute(select(func.count()).select_from(Job).where(Job.audit_id == audit.id))
    ).scalar_one()
    return AuditRunTriggerResponse(
        audit_id=audit.id,
        audit_number=audit_number,
        status=_status_value(audit.status),
        scheduled_jobs=scheduled_jobs,
        total_jobs=total_jobs,
    )


def _source_item_from_value(
    value: object,
    provider: str | None = None,
) -> SourceSummaryItemResponse:
    if not isinstance(value, dict):
        return SourceSummaryItemResponse(title=str(value), provider=provider)

    return SourceSummaryItemResponse(
        title=value.get("title"),
        url=value.get("url"),
        domain=value.get("domain"),
        provider=provider,
        source_type=value.get("source_type"),
        citation_count=value.get("citation_count"),
        related_query_count=value.get("related_query_count"),
        source_quality_score=value.get("source_quality_score"),
    )


def _competitor_names(values: object) -> list[str]:
    if not isinstance(values, list):
        return []

    names: list[str] = []
    for value in values:
        if isinstance(value, str):
            names.append(value)
        elif isinstance(value, dict):
            name = value.get("name") or value.get("brand") or value.get("competitor")
            if isinstance(name, str):
                names.append(name)
    return names


def _component_scores(
    parsed_result: ParsedResult | None,
    score: Score | None,
) -> ComponentScoresResponse | None:
    if score is not None:
        return ComponentScoresResponse(
            visibility_score=score.visibility_score,
            prominence_score=score.prominence_score,
            sentiment_score=score.sentiment_score,
            recommendation_score=score.recommendation_score,
            source_quality_score=score.source_quality_score,
        )
    if parsed_result is not None:
        return ComponentScoresResponse(
            prominence_score=parsed_result.prominence_score,
            sentiment_score=parsed_result.sentiment,
            recommendation_score=parsed_result.recommendation_score,
            source_quality_score=parsed_result.source_quality_score,
        )
    return None


def _error_code(error_object: object) -> str | None:
    if isinstance(error_object, dict):
        code = error_object.get("code")
        return code if isinstance(code, str) else None
    return None


def _error_message(error_object: object) -> str | None:
    if isinstance(error_object, dict):
        message = error_object.get("message")
        return message if isinstance(message, str) else None
    return None


async def build_audit_results_response(
    session: AsyncSession,
    audit: Audit,
) -> AuditResultsResponse:
    audit_number = await get_relative_audit_number(session, audit)
    stmt = (
        select(Run, Query, ParsedResult, Score, RawResponse)
        .join(Query, Run.query_id == Query.id)
        .outerjoin(ParsedResult, ParsedResult.run_id == Run.id)
        .outerjoin(Score, Score.run_id == Run.id)
        .outerjoin(RawResponse, RawResponse.run_id == Run.id)
        .where(Run.audit_id == audit.id)
        .order_by(Query.id, Run.provider, Run.run_number, Run.id)
    )

    rows: list[AuditResultRowResponse] = []
    for run, query, parsed_result, score, raw_response in (await session.execute(stmt)).all():
        sources = []
        if parsed_result is not None and isinstance(parsed_result.sources, list):
            sources = [
                _source_item_from_value(value, provider=run.provider)
                for value in parsed_result.sources
            ]

        rows.append(
            AuditResultRowResponse(
                audit_id=audit.id,
                scdl_level=_scdl_level_value(audit.scdl_level),
                query_id=query.id,
                query=query.text,
                provider=run.provider,
                run_id=run.id,
                run_number=run.run_number,
                run_status=_run_status_value(run.status),
                visible_brand=(
                    parsed_result.visible_brand if parsed_result is not None else None
                ),
                brand_position_rank=(
                    parsed_result.brand_position_rank
                    if parsed_result is not None
                    else None
                ),
                final_score=score.final_score if score is not None else None,
                component_scores=_component_scores(parsed_result, score),
                competitors=_competitor_names(
                    parsed_result.competitors if parsed_result is not None else []
                ),
                sources=sources,
                raw_answer_ref=raw_response.id if raw_response is not None else None,
                error_code=(
                    _error_code(raw_response.error_object)
                    if raw_response is not None
                    else None
                ),
                error_message=(
                    _error_message(raw_response.error_object)
                    if raw_response is not None
                    else None
                ),
            )
        )

    return AuditResultsResponse(
        audit_id=audit.id,
        audit_number=audit_number,
        rows=rows,
        total=len(rows),
    )


def _run_results_for_summary(results: AuditResultsResponse) -> list[dict[str, Any]]:
    run_results: list[dict[str, Any]] = []
    for row in results.rows:
        run_results.append(
            {
                "query": row.query,
                "provider": row.provider,
                "status": row.run_status,
                "visible_brand": row.visible_brand is True,
                "final_score": row.final_score if row.final_score is not None else 0.0,
            }
        )
    return run_results


def _competitor_summary_items(
    results: AuditResultsResponse,
) -> list[CompetitorSummaryItemResponse]:
    mention_counts: Counter[str] = Counter()
    score_totals: dict[str, float] = defaultdict(float)
    score_counts: Counter[str] = Counter()
    total_runs = max(results.total, 1)

    for row in results.rows:
        for competitor in row.competitors:
            mention_counts[competitor] += 1
            if row.final_score is not None:
                score_totals[competitor] += row.final_score
                score_counts[competitor] += 1

    items: list[CompetitorSummaryItemResponse] = []
    for name, mention_count in sorted(
        mention_counts.items(),
        key=lambda item: (-item[1], item[0]),
    ):
        average_score = (
            round(score_totals[name] / score_counts[name], 4)
            if score_counts[name]
            else None
        )
        items.append(
            CompetitorSummaryItemResponse(
                name=name,
                mention_count=mention_count,
                visibility_ratio=round(mention_count / total_runs, 4),
                average_score=average_score,
            )
        )
    return items


def _source_summary_items(results: AuditResultsResponse) -> list[SourceSummaryItemResponse]:
    grouped: dict[tuple[str | None, str | None], dict[str, Any]] = {}
    related_queries: dict[tuple[str | None, str | None], set[str]] = defaultdict(set)

    for row in results.rows:
        for source in row.sources:
            key = (source.url, source.domain)
            if key not in grouped:
                grouped[key] = {
                    "title": source.title,
                    "url": source.url,
                    "domain": source.domain,
                    "provider": source.provider,
                    "source_type": source.source_type,
                    "citation_count": 0,
                    "source_quality_score": source.source_quality_score,
                }
            grouped[key]["citation_count"] += source.citation_count or 1
            related_queries[key].add(row.query)

    items: list[SourceSummaryItemResponse] = []
    for key, item in grouped.items():
        item["related_query_count"] = len(related_queries[key])
        items.append(SourceSummaryItemResponse(**item))

    return sorted(
        items,
        key=lambda item: (-(item.citation_count or 0), item.domain or "", item.url or ""),
    )


async def build_audit_summary_response(
    session: AsyncSession,
    audit: Audit,
) -> AuditSummaryResponse:
    results = await build_audit_results_response(session, audit)
    run_results = _run_results_for_summary(results)
    summary = build_audit_summary(run_results)
    critical_queries = [
        CriticalQueryItemResponse(
            query=item["query"],
            reason=item["reason"],
            query_score=item["query_score"],
        )
        for item in find_critical_queries(run_results)
    ]

    return AuditSummaryResponse(
        audit_id=audit.id,
        audit_number=await get_relative_audit_number(session, audit),
        status=_status_value(audit.status),
        total_queries=summary["total_queries"],
        total_runs=summary["total_runs"],
        successful_runs=summary["successful_runs"],
        failed_runs=summary["failed_runs"],
        completion_ratio=summary["completion_ratio"],
        visibility_ratio=summary["visibility_ratio"],
        average_score=summary["average_score"],
        critical_query_count=summary["critical_query_count"],
        provider_scores=summary["provider_scores"],
        critical_queries=critical_queries,
        competitors=_competitor_summary_items(results),
        sources=_source_summary_items(results),
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    if should_auto_create_schema():
        await init_models()
    yield


app = FastAPI(title="AI Brand Visibility Monitor API", lifespan=lifespan)
configure_cors(app)


@app.post("/auth/register", response_model=UserResponse, status_code=201)
async def register_user(
    payload: RegisterRequest,
    session: AsyncSession = DB_SESSION_DEPENDENCY,
) -> UserResponse:
    try:
        return await register_user_record(session=session, payload=payload)
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to register user.",
        ) from exc


@app.post("/auth/login", response_model=UserResponse)
async def login_user(
    payload: LoginRequest,
    response: Response,
    session: AsyncSession = DB_SESSION_DEPENDENCY,
) -> UserResponse:
    try:
        return await login_user_record(
            session=session,
            payload=payload,
            response=response,
            config=get_runtime_auth_config(),
        )
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail="Failed to log in.") from exc


@app.post("/auth/logout", response_model=LogoutResponse)
async def logout_user(response: Response) -> LogoutResponse:
    clear_auth_cookie(response=response, config=get_runtime_auth_config())
    return LogoutResponse(status="logged_out")


@app.get("/auth/me", response_model=UserResponse)
async def get_current_user(
    request: Request,
    session: AsyncSession = DB_SESSION_DEPENDENCY,
) -> UserResponse:
    config = get_runtime_auth_config()
    try:
        return await get_current_user_record(
            session=session,
            token=request.cookies.get(config.cookie.name),
            config=config,
        )
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail="Failed to load current user.") from exc


@app.get("/audits", response_model=list[AuditListItemResponse])
async def list_audits(
    request: Request,
    session: AsyncSession = DB_SESSION_DEPENDENCY,
) -> list[AuditListItemResponse]:
    try:
        current_user = await get_authenticated_user_from_request(session, request)
        return await list_audit_records(session, current_user)
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail="Failed to load audits.") from exc


@app.post("/audits", response_model=AuditCreateResponse)
async def create_audit(
    payload: AuditCreateRequest,
    request: Request,
    session: AsyncSession = DB_SESSION_DEPENDENCY,
) -> Any:
    config = get_runtime_auth_config()
    try:
        current_user = await get_current_user_record(
            session=session,
            token=request.cookies.get(config.cookie.name),
            config=config,
        )
        return await create_audit_record(session, payload, user_id=current_user.id)
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to persist audit.",
        ) from exc


@app.get("/audits/{audit_id}", response_model=AuditDetailResponse)
async def get_audit_detail(
    audit_id: int,
    request: Request,
    session: AsyncSession = DB_SESSION_DEPENDENCY,
) -> AuditDetailResponse:
    try:
        current_user = await get_authenticated_user_from_request(session, request)
        audit, brand = await load_accessible_audit(session, audit_id, current_user)
        return await build_audit_detail_response(session, audit, brand)
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail="Failed to load audit.") from exc


@app.get("/audits/{audit_id}/status", response_model=AuditStatusResponse)
async def get_audit_status(
    audit_id: int,
    request: Request,
    session: AsyncSession = DB_SESSION_DEPENDENCY,
) -> AuditStatusResponse:
    try:
        current_user = await get_authenticated_user_from_request(session, request)
        audit, _brand = await load_accessible_audit(session, audit_id, current_user)
        return await build_audit_status_response(session, audit)
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail="Failed to load audit status.") from exc


@app.post("/audits/{audit_id}/run", response_model=AuditRunTriggerResponse)
async def run_audit(
    audit_id: int,
    request: Request,
    session: AsyncSession = DB_SESSION_DEPENDENCY,
) -> AuditRunTriggerResponse:
    try:
        current_user = await get_authenticated_user_from_request(session, request)
        audit, _brand = await load_accessible_audit(session, audit_id, current_user)
        return await trigger_audit_run_record(session, audit)
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Failed to trigger audit run.") from exc


@app.get("/audits/{audit_id}/results", response_model=AuditResultsResponse)
async def get_audit_results(
    audit_id: int,
    request: Request,
    session: AsyncSession = DB_SESSION_DEPENDENCY,
) -> AuditResultsResponse:
    try:
        current_user = await get_authenticated_user_from_request(session, request)
        audit, _brand = await load_accessible_audit(session, audit_id, current_user)
        return await build_audit_results_response(session, audit)
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail="Failed to load audit results.") from exc


@app.get("/audits/{audit_id}/summary", response_model=AuditSummaryResponse)
async def get_audit_summary(
    audit_id: int,
    request: Request,
    session: AsyncSession = DB_SESSION_DEPENDENCY,
) -> AuditSummaryResponse:
    try:
        current_user = await get_authenticated_user_from_request(session, request)
        audit, _brand = await load_accessible_audit(session, audit_id, current_user)
        return await build_audit_summary_response(session, audit)
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail="Failed to load audit summary.") from exc

