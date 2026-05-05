"""API entrypoint for audit lifecycle operations."""

from __future__ import annotations

import os
import re
from collections import Counter, defaultdict
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)
from sqlalchemy import delete, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.audit_schemas import (
    AuditDetailResponse,
    AuditListItemResponse,
    AuditPipelineRunResponse,
    AuditResultRowResponse,
    AuditResultsResponse,
    AuditRunTriggerResponse,
    AuditStatusResponse,
    AuditSummaryResponse,
    AuditTargetResponse,
    CompetitorSummaryItemResponse,
    ComponentScoresResponse,
    CriticalQueryItemResponse,
    GeneratedSeedQuerySuggestionResponse,
    GenerateSeedQuerySuggestionsResponse,
    ProviderDiagnosticResponse,
    QueryTypeCoverageItemResponse,
    RawResponseInspectionResponse,
    SeedQueryItemResponse,
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
from apps.api.services.seed_query_generation import (
    GenerateSeedQueriesInput,
    SeedQueryDraft,
    SeedQueryGenerationConfigError,
    SeedQueryGenerationUnavailable,
    generate_seed_query_suggestions,
)
from libs.analysis.aggregation import (
    build_audit_summary,
    compute_query_type_coverage,
    find_critical_queries,
)
from libs.control.job_scheduler import schedule_jobs_for_audit
from libs.control.query_deduplication import deduplicate_queries
from libs.execution.openrouter_model_catalog import (
    ModelCatalogResponse,
    get_openrouter_model_catalog,
)
from libs.execution.pilot_config import (
    PilotConfigError,
    PilotPolicyError,
    validate_audit_against_pilot_config,
)
from libs.execution.pipeline import run_audit_pipeline
from libs.execution.provider_errors import (
    ProviderErrorCode,
    configuration_error,
    no_api_key_error,
    normalize_provider_error_dict,
    provider_disabled_error,
    unknown_provider_error,
    unsupported_l2_error,
)
from libs.storage.models import (
    Audit,
    AuditStatus,
    AuditTarget,
    Brand,
    Job,
    ParsedResult,
    Query,
    RawResponse,
    Run,
    RunStatus,
    SCDLLevel,
    Score,
    SeedQuerySource,
    SeedQueryType,
    User,
    UserRole,
)

SUPPORTED_PROVIDERS = frozenset({"mock", "openai", "anthropic", "gemini"})
MAX_BRAND_NAME_LENGTH = 255
MAX_BRAND_DESCRIPTION_LENGTH = 500
MAX_SEED_QUERY_COUNT = 20
MIN_SEED_QUERY_LENGTH = 3
MAX_SEED_QUERY_LENGTH = 300
DEFAULT_MAX_AUDIT_TARGETS = 10
DEFAULT_MAX_MODELS_PER_AUDIT = 5
DEFAULT_MAX_QUERIES_PER_AUDIT = 20
DEFAULT_MAX_TOTAL_RUNS_PER_AUDIT = 100
MAX_EMAIL_LENGTH = 255
BRAND_DOMAIN_PATTERN = re.compile(
    r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$"
)
DB_SESSION_DEPENDENCY = Depends(get_db_session)
UNAUTHORIZED_DETAIL = "Invalid authentication credentials."
AUDIT_NOT_FOUND_DETAIL = "Audit was not found."
AUDIT_RUNNING_DETAIL = "Audit is already running."
AUDIT_NOT_TRIGGERABLE_DETAIL = "Audit can only be triggered from the created state."
AUDIT_NOT_EDITABLE_DETAIL = "Audit can only be edited before it starts running."
AUDIT_DELETE_ACTIVE_DETAIL = "Only archived audits can be deleted permanently."
AUDIT_NOT_RUNNABLE_DETAIL = "Audit has no runnable query/provider combinations."
RAW_RESPONSE_NOT_FOUND_DETAIL = "Raw response was not found."
RAW_RESPONSE_FORBIDDEN_DETAIL = "Raw response inspection requires admin access."
DEV_PIPELINE_FORBIDDEN_DETAIL = "Pipeline execution requires admin access."
SENSITIVE_RAW_RESPONSE_KEYS = frozenset(
    {
        "api_key",
        "apikey",
        "authorization",
        "bearer",
        "cookie",
        "headers",
        "jwt",
        "openai_api_key",
        "password",
        "secret",
        "token",
    }
)
SENSITIVE_PIPELINE_RESPONSE_KEYS = SENSITIVE_RAW_RESPONSE_KEYS | frozenset(
    {
        "prompt",
        "prompts",
        "raw_answer",
        "request_snapshot",
    }
)


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


def normalize_brand_domain(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.strip().lower().rstrip("/")
    if not normalized:
        return None
    if "://" in normalized or "/" in normalized or "?" in normalized or "#" in normalized:
        raise ValueError("Invalid domain format")
    if not BRAND_DOMAIN_PATTERN.fullmatch(normalized):
        raise ValueError("Invalid domain format")
    return normalized


def normalize_seed_query_text(value: str) -> str:
    normalized = " ".join(value.strip().split())
    if not normalized:
        raise ValueError("seed query text must not be empty.")
    if len(normalized) < MIN_SEED_QUERY_LENGTH:
        raise ValueError(f"seed query text min length is {MIN_SEED_QUERY_LENGTH}.")
    if len(normalized) > MAX_SEED_QUERY_LENGTH:
        raise ValueError(f"seed query text max length is {MAX_SEED_QUERY_LENGTH}.")
    return normalized


class SeedQueryItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    type: Literal[
        "brand_direct",
        "category_discovery",
        "recommendation",
        "comparison",
        "alternative",
        "problem_solution",
    ] | None = None
    source: Literal["user", "ai"] = "user"

    @field_validator("text")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return normalize_seed_query_text(value)

    @model_validator(mode="after")
    def validate_ai_query_type(self) -> SeedQueryItemRequest:
        if self.source == "ai" and self.type is None:
            raise ValueError("seed query type is required when source is ai.")
        return self


class AuditTargetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ai_family: str
    execution_provider: str
    model_provider: str
    model_id: str
    display_name: str
    level: Literal["L1", "L2"]
    gateway: bool = False
    gateway_l2_experimental: bool = False

    @field_validator(
        "ai_family",
        "execution_provider",
        "model_provider",
        "model_id",
        "display_name",
    )
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("audit target fields must not be empty.")
        return normalized

    @field_validator("ai_family", "execution_provider", "model_provider")
    @classmethod
    def normalize_code_fields(cls, value: str) -> str:
        return value.strip().lower()

    @model_validator(mode="after")
    def validate_gateway_l2_flag(self) -> AuditTargetRequest:
        if self.level == "L1" and self.gateway_l2_experimental:
            raise ValueError("gateway_l2_experimental is valid only for L2 targets.")
        return self


class AuditCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    brand_name: str
    providers: list[str] | None = None
    runs_per_query: int = Field(ge=1, le=5)

    brand_domain: str | None = None
    brand_description: str | None = Field(default=None, max_length=MAX_BRAND_DESCRIPTION_LENGTH)

    language: str | None = None
    country: str | None = None
    locale: str | None = None
    max_queries: int | None = None
    seed_queries: list[str] | None = None
    seed_query_items: list[SeedQueryItemRequest] | None = None
    model_targets: list[AuditTargetRequest] | None = None
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
    def validate_providers(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
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

    @field_validator("model_targets")
    @classmethod
    def validate_model_targets(
        cls, value: list[AuditTargetRequest] | None
    ) -> list[AuditTargetRequest] | None:
        if value is None:
            return None
        if not value:
            raise ValueError("model_targets must contain at least one target.")
        seen: set[tuple[str, str, str]] = set()
        for target in value:
            key = (target.execution_provider, target.model_id, target.level)
            if key in seen:
                raise ValueError("model_targets contains duplicate targets.")
            seen.add(key)
        return value

    @field_validator("brand_domain")
    @classmethod
    def validate_brand_domain(cls, value: str | None) -> str | None:
        return normalize_brand_domain(value)

    @field_validator("brand_description", "language", "country", "locale")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("seed_queries")
    @classmethod
    def normalize_seed_queries(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        if len(value) > MAX_SEED_QUERY_COUNT:
            raise ValueError(f"seed_queries max length is {MAX_SEED_QUERY_COUNT}.")
        normalized = [normalize_seed_query_text(query) for query in value]
        deduplicated = deduplicate_queries(normalized)
        return deduplicated or None

    @field_validator("seed_query_items")
    @classmethod
    def validate_seed_query_items(
        cls, value: list[SeedQueryItemRequest] | None
    ) -> list[SeedQueryItemRequest] | None:
        if value is None:
            return None
        if len(value) > MAX_SEED_QUERY_COUNT:
            raise ValueError(f"seed_query_items max length is {MAX_SEED_QUERY_COUNT}.")
        return value

    @model_validator(mode="after")
    def validate_seed_query_fields(self) -> AuditCreateRequest:
        if "seed_queries" in self.model_fields_set and "seed_query_items" in self.model_fields_set:
            raise ValueError("Provide either seed_queries or seed_query_items, not both.")
        has_legacy_queries = self.seed_queries is not None and len(self.seed_queries) > 0
        has_typed_queries = self.seed_query_items is not None and len(self.seed_query_items) > 0
        if not has_legacy_queries and not has_typed_queries:
            raise ValueError("At least one seed query is required.")
        return self

    @model_validator(mode="after")
    def validate_target_fields(self) -> AuditCreateRequest:
        has_targets = self.model_targets is not None
        has_legacy_providers = "providers" in self.model_fields_set
        has_legacy_level = "scdl_level" in self.model_fields_set
        if has_targets and (has_legacy_providers or has_legacy_level):
            raise ValueError(
                "Provide either model_targets or legacy providers/scdl_level, not both."
            )
        if not has_targets and not self.providers:
            raise ValueError("providers must contain at least one supported provider.")
        return self

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
    seed_query_items: list[SeedQueryItemResponse] = Field(default_factory=list)
    model_targets: list[AuditTargetResponse] = Field(default_factory=list)


class AuditCapsResponse(BaseModel):
    max_audit_targets: int
    max_models_per_audit: int
    max_queries_per_audit: int
    max_total_runs_per_audit: int


class AuditCapViolationResponse(BaseModel):
    code: str
    message: str


class AuditEstimateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    seed_queries: list[str] | None = None
    seed_query_items: list[SeedQueryItemRequest] | None = None
    model_targets: list[AuditTargetRequest] | None = None
    providers: list[str] | None = None
    scdl_level: Literal["L1", "L2"] = "L1"
    runs_per_query: int = Field(default=1, ge=1, le=5)

    @field_validator("seed_queries")
    @classmethod
    def normalize_seed_queries(cls, value: list[str] | None) -> list[str] | None:
        return AuditCreateRequest.normalize_seed_queries(value)

    @field_validator("seed_query_items")
    @classmethod
    def validate_seed_query_items(
        cls, value: list[SeedQueryItemRequest] | None
    ) -> list[SeedQueryItemRequest] | None:
        return AuditCreateRequest.validate_seed_query_items(value)

    @field_validator("providers")
    @classmethod
    def validate_providers(cls, value: list[str] | None) -> list[str] | None:
        return AuditCreateRequest.validate_providers(value)

    @field_validator("model_targets")
    @classmethod
    def validate_model_targets(
        cls, value: list[AuditTargetRequest] | None
    ) -> list[AuditTargetRequest] | None:
        return AuditCreateRequest.validate_model_targets(value)

    @model_validator(mode="after")
    def validate_estimate_fields(self) -> AuditEstimateRequest:
        if "seed_queries" in self.model_fields_set and "seed_query_items" in self.model_fields_set:
            raise ValueError("Provide either seed_queries or seed_query_items, not both.")
        has_queries = bool(self.seed_queries) or bool(self.seed_query_items)
        if not has_queries:
            raise ValueError("At least one seed query is required.")

        has_targets = self.model_targets is not None
        has_legacy_providers = "providers" in self.model_fields_set
        has_legacy_level = "scdl_level" in self.model_fields_set
        if has_targets and (has_legacy_providers or has_legacy_level):
            raise ValueError(
                "Provide either model_targets or legacy providers/scdl_level, not both."
            )
        if not has_targets and not self.providers:
            raise ValueError("providers must contain at least one supported provider.")
        return self


class AuditEstimateResponse(BaseModel):
    query_count: int
    target_count: int
    model_count: int
    estimated_runs: int
    caps: AuditCapsResponse
    over_cap: bool = False
    violations: list[AuditCapViolationResponse] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class GenerateSeedQuerySuggestionsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    brand_name: str | None = None
    brand_domain: str | None = None
    brand_description: str | None = None
    use_domain: bool = False
    use_description: bool = False
    count: int = Field(default=10, ge=1, le=10)
    existing_queries: list[SeedQueryItemRequest] = Field(default_factory=list)

    @field_validator("brand_name", "brand_description")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("brand_domain")
    @classmethod
    def normalize_domain(cls, value: str | None) -> str | None:
        return normalize_brand_domain(value)


class AuditActionResponse(BaseModel):
    audit_id: int
    status: str
    archived_at: datetime | None = None


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


def build_seed_query_items(
    payload: AuditCreateRequest | AuditEstimateRequest,
) -> list[SeedQueryItemRequest]:
    if payload.seed_query_items is not None:
        return payload.seed_query_items
    return [
        SeedQueryItemRequest(text=query_text, source="user", type=None)
        for query_text in payload.seed_queries or []
    ]


def build_audit_target_requests(
    payload: AuditCreateRequest | AuditEstimateRequest,
) -> list[AuditTargetRequest]:
    if payload.model_targets is not None:
        return payload.model_targets
    return [
        AuditTargetRequest(
            ai_family=provider,
            execution_provider=provider,
            model_provider=provider,
            model_id=provider,
            display_name=provider.title(),
            level=payload.scdl_level,
            gateway=False,
            gateway_l2_experimental=False,
        )
        for provider in payload.providers or []
    ]


def derive_legacy_providers(targets: list[AuditTargetRequest]) -> list[str]:
    providers: list[str] = []
    seen: set[str] = set()
    for target in targets:
        provider = target.execution_provider
        if provider not in seen:
            seen.add(provider)
            providers.append(provider)
    return providers


def derive_legacy_scdl_level(targets: list[AuditTargetRequest]) -> str:
    if any(target.level == "L2" for target in targets):
        return "L2"
    return "L1"


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        parsed = int(raw)
    except ValueError:
        return default
    return parsed if parsed > 0 else default


def audit_caps() -> AuditCapsResponse:
    return AuditCapsResponse(
        max_audit_targets=_env_int("MAX_AUDIT_TARGETS", DEFAULT_MAX_AUDIT_TARGETS),
        max_models_per_audit=_env_int(
            "MAX_MODELS_PER_AUDIT",
            DEFAULT_MAX_MODELS_PER_AUDIT,
        ),
        max_queries_per_audit=_env_int(
            "MAX_QUERIES_PER_AUDIT",
            DEFAULT_MAX_QUERIES_PER_AUDIT,
        ),
        max_total_runs_per_audit=_env_int(
            "MAX_TOTAL_RUNS_PER_AUDIT",
            DEFAULT_MAX_TOTAL_RUNS_PER_AUDIT,
        ),
    )


def estimate_audit_payload(
    payload: AuditCreateRequest | AuditEstimateRequest,
) -> AuditEstimateResponse:
    seed_query_items = build_seed_query_items(payload)
    targets = build_audit_target_requests(payload)
    query_count = len(seed_query_items)
    target_count = len(targets)
    model_count = len(
        {(target.execution_provider, target.model_id) for target in targets}
    )
    estimated_runs = query_count * target_count * payload.runs_per_query
    caps = audit_caps()
    violations: list[AuditCapViolationResponse] = []
    if target_count > caps.max_audit_targets:
        violations.append(
            AuditCapViolationResponse(
                code="MAX_AUDIT_TARGETS_EXCEEDED",
                message="Audit target count exceeds the configured limit.",
            )
        )
    if model_count > caps.max_models_per_audit:
        violations.append(
            AuditCapViolationResponse(
                code="MAX_MODELS_PER_AUDIT_EXCEEDED",
                message="Audit model count exceeds the configured limit.",
            )
        )
    if query_count > caps.max_queries_per_audit:
        violations.append(
            AuditCapViolationResponse(
                code="MAX_QUERIES_PER_AUDIT_EXCEEDED",
                message="Audit query count exceeds the configured limit.",
            )
        )
    if estimated_runs > caps.max_total_runs_per_audit:
        violations.append(
            AuditCapViolationResponse(
                code="MAX_TOTAL_RUNS_EXCEEDED",
                message="Estimated audit runs exceed the configured limit.",
            )
        )
    return AuditEstimateResponse(
        query_count=query_count,
        target_count=target_count,
        model_count=model_count,
        estimated_runs=estimated_runs,
        caps=caps,
        over_cap=bool(violations),
        violations=violations,
    )


def enforce_audit_caps(payload: AuditCreateRequest) -> None:
    estimate = estimate_audit_payload(payload)
    if estimate.over_cap:
        raise HTTPException(
            status_code=422,
            detail=[violation.model_dump() for violation in estimate.violations],
        )


def add_seed_query_records(
    session: AsyncSession,
    audit_id: int,
    seed_query_items: list[SeedQueryItemRequest],
) -> None:
    for item in seed_query_items:
        session.add(
            Query(
                audit_id=audit_id,
                text=item.text,
                query_type=SeedQueryType(item.type) if item.type is not None else None,
                source=SeedQuerySource(item.source),
            )
        )


def add_audit_target_records(
    session: AsyncSession,
    audit_id: int,
    targets: list[AuditTargetRequest],
) -> None:
    for target in targets:
        session.add(
            AuditTarget(
                audit_id=audit_id,
                ai_family=target.ai_family,
                execution_provider=target.execution_provider,
                model_provider=target.model_provider,
                model_id=target.model_id,
                display_name=target.display_name,
                level=SCDLLevel(target.level),
                gateway=target.gateway,
                gateway_l2_experimental=target.gateway_l2_experimental,
            )
        )


def build_seed_query_item_response(query: Query) -> SeedQueryItemResponse:
    return SeedQueryItemResponse(
        text=query.text,
        type=query.query_type.value if query.query_type is not None else None,
        source=query.source.value,
    )


def build_audit_target_response(target: AuditTarget) -> AuditTargetResponse:
    return AuditTargetResponse(
        target_id=target.id,
        ai_family=target.ai_family,
        execution_provider=target.execution_provider,
        model_provider=target.model_provider,
        model_id=target.model_id,
        display_name=target.display_name,
        level=_scdl_level_value(target.level),
        gateway=target.gateway,
        gateway_l2_experimental=target.gateway_l2_experimental,
    )


async def create_audit_record(
    session: AsyncSession,
    payload: AuditCreateRequest,
    user_id: int,
) -> AuditCreateResponse:
    enforce_audit_caps(payload)
    brand = await get_or_create_brand_for_audit(session, payload)
    target_requests = build_audit_target_requests(payload)
    providers = derive_legacy_providers(target_requests)
    scdl_level = derive_legacy_scdl_level(target_requests)

    audit = Audit(
        user_id=user_id,
        brand=brand,
        status=AuditStatus.CREATED,
        providers=providers,
        runs_per_query=payload.runs_per_query,
        language=payload.language,
        country=payload.country,
        locale=payload.locale,
        max_queries=payload.max_queries,
        enable_query_expansion=payload.enable_query_expansion,
        enable_source_intelligence=payload.enable_source_intelligence,
        follow_up_depth=payload.follow_up_depth,
        scdl_level=SCDLLevel(scdl_level),
    )
    session.add(audit)
    await session.flush()

    seed_query_items = build_seed_query_items(payload)
    add_seed_query_records(session, audit.id, seed_query_items)
    add_audit_target_records(session, audit.id, target_requests)
    seed_queries = [item.text for item in seed_query_items]

    await session.commit()
    await session.refresh(audit)
    audit_number = await get_relative_audit_number(session, audit)

    target_rows = (
        await session.execute(
            select(AuditTarget).where(AuditTarget.audit_id == audit.id).order_by(AuditTarget.id)
        )
    ).scalars().all()

    return AuditCreateResponse(
        audit_id=audit.id,
        audit_number=audit_number,
        brand_id=audit.brand_id,
        status=audit.status.value,
        providers=audit.providers,
        runs_per_query=audit.runs_per_query,
        scdl_level=audit.scdl_level.value,
        seed_queries=seed_queries,
        seed_query_items=[
            SeedQueryItemResponse(
                text=item.text,
                type=item.type,
                source=item.source,
            )
            for item in seed_query_items
        ],
        model_targets=[build_audit_target_response(target) for target in target_rows],
    )


async def get_or_create_brand_for_audit(
    session: AsyncSession,
    payload: AuditCreateRequest,
) -> Brand:
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

    return brand


async def update_audit_record(
    session: AsyncSession,
    audit: Audit,
    payload: AuditCreateRequest,
) -> AuditDetailResponse:
    if audit.status != AuditStatus.CREATED:
        raise HTTPException(status_code=409, detail=AUDIT_NOT_EDITABLE_DETAIL)
    enforce_audit_caps(payload)

    brand = await get_or_create_brand_for_audit(session, payload)
    target_requests = build_audit_target_requests(payload)
    audit.brand = brand
    audit.providers = derive_legacy_providers(target_requests)
    audit.runs_per_query = payload.runs_per_query
    audit.language = payload.language
    audit.country = payload.country
    audit.locale = payload.locale
    audit.max_queries = payload.max_queries
    audit.enable_query_expansion = payload.enable_query_expansion
    audit.enable_source_intelligence = payload.enable_source_intelligence
    audit.follow_up_depth = payload.follow_up_depth
    audit.scdl_level = SCDLLevel(derive_legacy_scdl_level(target_requests))

    await session.execute(delete(Query).where(Query.audit_id == audit.id))
    await session.execute(delete(AuditTarget).where(AuditTarget.audit_id == audit.id))
    add_seed_query_records(session, audit.id, build_seed_query_items(payload))
    add_audit_target_records(session, audit.id, target_requests)

    await session.commit()
    await session.refresh(audit)
    return await build_audit_detail_response(session, audit, brand)


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


def _redact_sensitive_value(value: object) -> object:
    if isinstance(value, dict):
        redacted: dict[str, object] = {}
        for key, child in value.items():
            normalized_key = str(key).strip().lower()
            if normalized_key in SENSITIVE_RAW_RESPONSE_KEYS or normalized_key.endswith("_key"):
                redacted[str(key)] = "***"
            else:
                redacted[str(key)] = _redact_sensitive_value(child)
        return redacted
    if isinstance(value, list):
        return [_redact_sensitive_value(item) for item in value]
    return value


def _redact_pipeline_summary_value(value: object, key: str | None = None) -> object:
    if key is not None and _is_sensitive_pipeline_key(key):
        return "***"
    if isinstance(value, dict):
        return {
            str(item_key): _redact_pipeline_summary_value(item_value, str(item_key))
            for item_key, item_value in value.items()
        }
    if isinstance(value, list):
        return [_redact_pipeline_summary_value(item) for item in value]
    if isinstance(value, str):
        return _redact_sensitive_string(value)
    return value


def _is_sensitive_pipeline_key(key: str) -> bool:
    normalized = key.strip().lower()
    return normalized in SENSITIVE_PIPELINE_RESPONSE_KEYS or normalized.endswith("_key")


def _redact_sensitive_string(value: str) -> str:
    redacted = value
    for marker in ("sk-", "Bearer "):
        index = redacted.find(marker)
        if index < 0:
            continue
        end = redacted.find(" ", index + len(marker))
        if end < 0:
            end = len(redacted)
        redacted = f"{redacted[:index]}***{redacted[end:]}"
    return redacted


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
            select(Query).where(Query.audit_id == audit.id).order_by(Query.id)
        )
    ).scalars().all()
    targets = (
        await session.execute(
            select(AuditTarget).where(AuditTarget.audit_id == audit.id).order_by(AuditTarget.id)
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
        seed_queries=[query.text for query in queries],
        seed_query_items=[build_seed_query_item_response(query) for query in queries],
        model_targets=[build_audit_target_response(target) for target in targets],
        enable_query_expansion=audit.enable_query_expansion,
        enable_source_intelligence=audit.enable_source_intelligence,
        follow_up_depth=audit.follow_up_depth,
        created_at=audit.created_at,
        updated_at=audit.updated_at,
        archived_at=audit.archived_at,
    )


async def list_audit_records(
    session: AsyncSession,
    current_user: UserResponse,
    *,
    archived: bool = False,
) -> list[AuditListItemResponse]:
    stmt = (
        select(Audit, Brand)
        .join(Brand, Audit.brand_id == Brand.id)
        .order_by(Audit.created_at.desc(), Audit.id.desc())
    )
    stmt = stmt.where(Audit.archived_at.is_not(None) if archived else Audit.archived_at.is_(None))
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
            archived_at=audit.archived_at,
        )
        for audit, brand in rows
    ]


async def archive_audit_record(session: AsyncSession, audit: Audit) -> AuditActionResponse:
    if audit.archived_at is None:
        audit.archived_at = datetime.now(tz=timezone.utc)
        await session.commit()
        await session.refresh(audit)
    return AuditActionResponse(
        audit_id=audit.id,
        status=_status_value(audit.status),
        archived_at=audit.archived_at,
    )


async def restore_audit_record(session: AsyncSession, audit: Audit) -> AuditActionResponse:
    if audit.archived_at is not None:
        audit.archived_at = None
        await session.commit()
        await session.refresh(audit)
    return AuditActionResponse(
        audit_id=audit.id,
        status=_status_value(audit.status),
        archived_at=audit.archived_at,
    )


async def delete_archived_audit_record(session: AsyncSession, audit: Audit) -> None:
    if audit.archived_at is None:
        raise HTTPException(status_code=409, detail=AUDIT_DELETE_ACTIVE_DETAIL)
    await session.delete(audit)
    await session.commit()


async def get_expected_run_count(session: AsyncSession, audit: Audit) -> int:
    query_count = await get_effective_query_count(session, audit)
    target_count = (
        await session.execute(
            select(func.count())
            .select_from(AuditTarget)
            .where(AuditTarget.audit_id == audit.id)
        )
    ).scalar_one()
    provider_count = target_count or len(audit.providers or [])
    return query_count * provider_count * audit.runs_per_query


async def get_effective_query_count(session: AsyncSession, audit: Audit) -> int:
    query_stmt = select(Query.id).where(Query.audit_id == audit.id).order_by(Query.id)
    query_ids = list((await session.execute(query_stmt)).scalars().all())
    if audit.max_queries is not None:
        query_ids = query_ids[: audit.max_queries]
    return len(query_ids)


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
    targets = (
        await session.execute(
            select(AuditTarget).where(AuditTarget.audit_id == audit.id).order_by(AuditTarget.id)
        )
    ).scalars().all()

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
        model_targets=[build_audit_target_response(target) for target in targets],
        provider_diagnostics=await _provider_diagnostics_for_audit(session, audit),
    )


async def trigger_audit_run_record(
    session: AsyncSession,
    audit: Audit,
) -> AuditRunTriggerResponse:
    audit_number = await get_relative_audit_number(session, audit)
    await validate_audit_pipeline_triggerable(session, audit)

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


async def validate_audit_pipeline_triggerable(
    session: AsyncSession,
    audit: Audit,
) -> None:
    if audit.status == AuditStatus.RUNNING:
        raise HTTPException(status_code=409, detail=AUDIT_RUNNING_DETAIL)
    if audit.status != AuditStatus.CREATED:
        raise HTTPException(status_code=409, detail=AUDIT_NOT_TRIGGERABLE_DETAIL)

    expected_runs = await get_expected_run_count(session, audit)
    if expected_runs == 0:
        raise HTTPException(status_code=400, detail=AUDIT_NOT_RUNNABLE_DETAIL)

    try:
        validate_audit_against_pilot_config(
            providers=audit.providers or [],
            query_count=await get_effective_query_count(session, audit),
            runs_per_query=audit.runs_per_query,
            scdl_level=_scdl_level_value(audit.scdl_level),
        )
    except (PilotConfigError, PilotPolicyError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def build_pipeline_run_response(
    summary: object,
    *,
    provider_diagnostics: list[ProviderDiagnosticResponse] | None = None,
) -> AuditPipelineRunResponse:
    safe_summary = _redact_pipeline_summary_value(summary.safe_log_dict())
    safe_summary["provider_diagnostics"] = provider_diagnostics or []
    return AuditPipelineRunResponse.model_validate(safe_summary)


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


def _provider_model_from_metadata(provider_metadata: object) -> str | None:
    if isinstance(provider_metadata, dict):
        model = provider_metadata.get("model_id") or provider_metadata.get("model")
        return model if isinstance(model, str) else None
    return None


def _target_level(target: AuditTarget | None, audit: Audit) -> str:
    if target is not None:
        return _scdl_level_value(target.level)
    return _scdl_level_value(audit.scdl_level)


def _provider_diagnostic_response(
    *,
    error_object: object,
    provider: str,
    run_status: object,
    model: str | None,
    level: str | None,
    run_id: int | None = None,
    query_id: int | None = None,
) -> ProviderDiagnosticResponse | None:
    run_status_value = _run_status_value(run_status)
    if run_status_value == RunStatus.SUCCESS.value and error_object is None:
        return None
    if run_status_value == RunStatus.PENDING.value and error_object is None:
        return None

    if isinstance(error_object, dict):
        diagnostic = normalize_provider_error_dict(
            error_object,
            provider=provider,
            model=model,
            level=level,
            fallback_code=ProviderErrorCode.UNKNOWN_PROVIDER_ERROR,
        )
    else:
        diagnostic = unknown_provider_error(provider, model, level).to_error_dict()

    safe_diagnostic = _safe_provider_diagnostic_dict(diagnostic)
    safe_diagnostic["run_id"] = run_id
    safe_diagnostic["query_id"] = query_id
    return ProviderDiagnosticResponse.model_validate(safe_diagnostic)


def _safe_provider_diagnostic_dict(diagnostic: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "code",
        "message",
        "provider",
        "model",
        "level",
        "retryable",
    }
    return {key: diagnostic.get(key) for key in allowed}


async def _provider_diagnostics_for_audit(
    session: AsyncSession,
    audit: Audit,
) -> list[ProviderDiagnosticResponse]:
    stmt = (
        select(Run, RawResponse, AuditTarget)
        .outerjoin(RawResponse, RawResponse.run_id == Run.id)
        .outerjoin(AuditTarget, AuditTarget.id == Run.audit_target_id)
        .where(Run.audit_id == audit.id)
        .order_by(Run.id)
    )
    diagnostics: list[ProviderDiagnosticResponse] = []
    for run, raw_response, target in (await session.execute(stmt)).all():
        error_object = raw_response.error_object if raw_response is not None else None
        provider_metadata = (
            raw_response.provider_metadata if raw_response is not None else None
        )
        diagnostic = _provider_diagnostic_response(
            error_object=error_object,
            provider=run.provider,
            run_status=run.status,
            model=_provider_model_from_metadata(provider_metadata),
            level=_target_level(target, audit),
            run_id=run.id,
            query_id=run.query_id,
        )
        if diagnostic is not None:
            diagnostics.append(diagnostic)
    return diagnostics


def _dedupe_provider_diagnostics(
    diagnostics: list[ProviderDiagnosticResponse],
) -> list[ProviderDiagnosticResponse]:
    seen: set[tuple[object, ...]] = set()
    deduped: list[ProviderDiagnosticResponse] = []
    for diagnostic in diagnostics:
        key = (
            diagnostic.code,
            diagnostic.message,
            diagnostic.provider,
            diagnostic.model,
            diagnostic.level,
            diagnostic.retryable,
            diagnostic.run_id,
            diagnostic.query_id,
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(diagnostic)
    return deduped


def _provider_diagnostic_from_pipeline_error(
    *,
    fatal_error: str | None,
    audit: Audit,
) -> ProviderDiagnosticResponse | None:
    if not fatal_error:
        return None

    provider = (audit.providers or ["unknown"])[0]
    level = _scdl_level_value(audit.scdl_level)
    normalized = fatal_error.lower()
    if "disabled" in normalized:
        error = provider_disabled_error(provider, level=level)
    elif "api key" in normalized or "openai_api_key" in normalized:
        error = no_api_key_error(provider, level=level)
    elif "l2" in normalized and "unsupported" in normalized:
        error = unsupported_l2_error(provider)
    else:
        error = configuration_error(provider, level=level)

    return ProviderDiagnosticResponse.model_validate(
        _safe_provider_diagnostic_dict(error.to_error_dict())
    )


async def _pipeline_provider_diagnostics(
    session: AsyncSession,
    audit: Audit,
    summary: object,
) -> list[ProviderDiagnosticResponse]:
    diagnostics = await _provider_diagnostics_for_audit(session, audit)
    fatal_messages = [
        getattr(summary, "fatal_error", None),
        getattr(getattr(summary, "scheduling", None), "fatal_error", None),
        getattr(getattr(summary, "execution", None), "fatal_error", None),
        getattr(getattr(summary, "post_processing", None), "fatal_error", None),
    ]
    for fatal_error in fatal_messages:
        diagnostic = _provider_diagnostic_from_pipeline_error(
            fatal_error=fatal_error,
            audit=audit,
        )
        if diagnostic is not None:
            diagnostics.append(diagnostic)
    return _dedupe_provider_diagnostics(diagnostics)


async def build_audit_results_response(
    session: AsyncSession,
    audit: Audit,
) -> AuditResultsResponse:
    audit_number = await get_relative_audit_number(session, audit)
    stmt = (
        select(Run, Query, ParsedResult, Score, RawResponse, AuditTarget)
        .join(Query, Run.query_id == Query.id)
        .outerjoin(ParsedResult, ParsedResult.run_id == Run.id)
        .outerjoin(Score, Score.run_id == Run.id)
        .outerjoin(RawResponse, RawResponse.run_id == Run.id)
        .outerjoin(AuditTarget, AuditTarget.id == Run.audit_target_id)
        .where(Run.audit_id == audit.id)
        .order_by(Query.id, AuditTarget.id, Run.provider, Run.run_number, Run.id)
    )

    rows: list[AuditResultRowResponse] = []
    for run, query, parsed_result, score, raw_response, target in (
        await session.execute(stmt)
    ).all():
        sources = []
        if parsed_result is not None and isinstance(parsed_result.sources, list):
            sources = [
                _source_item_from_value(value, provider=run.provider)
                for value in parsed_result.sources
            ]
        provider_error = _provider_diagnostic_response(
            error_object=raw_response.error_object if raw_response is not None else None,
            provider=run.provider,
            run_status=run.status,
            model=_provider_model_from_metadata(
                raw_response.provider_metadata if raw_response is not None else None
            ),
            level=_target_level(target, audit),
            run_id=run.id,
            query_id=query.id,
        )

        rows.append(
            AuditResultRowResponse(
                audit_id=audit.id,
                scdl_level=_target_level(target, audit),
                target_id=target.id if target is not None else None,
                target=build_audit_target_response(target) if target is not None else None,
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
                provider_error=provider_error,
            )
        )

    return AuditResultsResponse(
        audit_id=audit.id,
        audit_number=audit_number,
        rows=rows,
        total=len(rows),
        provider_diagnostics=_dedupe_provider_diagnostics(
            [row.provider_error for row in rows if row.provider_error is not None]
        ),
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


async def _query_types_by_id(
    session: AsyncSession,
    audit_id: int,
) -> dict[int, str | None]:
    rows = (
        await session.execute(select(Query.id, Query.query_type).where(Query.audit_id == audit_id))
    ).all()
    return {
        query_id: query_type.value if query_type is not None else None
        for query_id, query_type in rows
    }


def _run_results_with_query_types(
    results: AuditResultsResponse,
    query_types_by_id: dict[int, str | None],
) -> list[dict[str, Any]]:
    run_results = _run_results_for_summary(results)
    for index, row in enumerate(results.rows):
        run_results[index]["query_type"] = query_types_by_id.get(row.query_id)
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
    query_types_by_id = await _query_types_by_id(session, audit.id)
    run_results = _run_results_with_query_types(results, query_types_by_id)
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
        weighted_visibility_score=summary["weighted_visibility_score"],
        critical_query_count=summary["critical_query_count"],
        provider_scores=summary["provider_scores"],
        critical_queries=critical_queries,
        query_type_coverage=[
            QueryTypeCoverageItemResponse(**item)
            for item in compute_query_type_coverage(run_results)
        ],
        competitors=_competitor_summary_items(results),
        sources=_source_summary_items(results),
        provider_diagnostics=results.provider_diagnostics,
    )


async def build_raw_response_inspection_response(
    session: AsyncSession,
    audit: Audit,
    run_id: int,
) -> RawResponseInspectionResponse:
    stmt = (
        select(Run, Query, RawResponse)
        .join(Query, Run.query_id == Query.id)
        .outerjoin(RawResponse, RawResponse.run_id == Run.id)
        .where(Run.audit_id == audit.id, Run.id == run_id)
    )
    row = (await session.execute(stmt)).first()
    if row is None:
        raise HTTPException(status_code=404, detail=RAW_RESPONSE_NOT_FOUND_DETAIL)

    run, query, raw_response = row
    if raw_response is None:
        raise HTTPException(status_code=404, detail=RAW_RESPONSE_NOT_FOUND_DETAIL)

    return RawResponseInspectionResponse(
        audit_id=audit.id,
        query=query.text,
        provider=run.provider,
        scdl_level=_scdl_level_value(audit.scdl_level),
        run_id=run.id,
        run_number=run.run_number,
        run_status=_run_status_value(run.status),
        raw_answer=raw_response.raw_answer,
        citations=raw_response.citations,
        provider_metadata=_redact_sensitive_value(raw_response.provider_metadata),
        error_object=_redact_sensitive_value(raw_response.error_object),
        response_time=raw_response.response_time,
        created_at=raw_response.created_at,
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


@app.post(
    "/audit-seed-query-suggestions",
    response_model=GenerateSeedQuerySuggestionsResponse,
)
async def suggest_seed_queries(
    payload: GenerateSeedQuerySuggestionsRequest,
    request: Request,
    session: AsyncSession = DB_SESSION_DEPENDENCY,
) -> GenerateSeedQuerySuggestionsResponse:
    try:
        await get_authenticated_user_from_request(session, request)
        result = await generate_seed_query_suggestions(
            GenerateSeedQueriesInput(
                brand_name=payload.brand_name,
                brand_domain=payload.brand_domain,
                brand_description=payload.brand_description,
                use_domain=payload.use_domain,
                use_description=payload.use_description,
                count=payload.count,
                existing_queries=[
                    SeedQueryDraft(
                        text=query.text,
                        type=query.type,
                        source=query.source,
                    )
                    for query in payload.existing_queries
                ],
            )
        )
        return GenerateSeedQuerySuggestionsResponse(
            suggestions=[
                GeneratedSeedQuerySuggestionResponse(
                    text=suggestion.text,
                    type=suggestion.type,
                    source=suggestion.source,
                )
                for suggestion in result.suggestions
            ],
            skipped_duplicates=result.skipped_duplicates,
            skipped_limit=result.skipped_limit,
            warnings=result.warnings,
        )
    except HTTPException:
        raise
    except SeedQueryGenerationConfigError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except SeedQueryGenerationUnavailable as exc:
        raise HTTPException(
            status_code=503,
            detail="Seed query generation is unavailable.",
        ) from exc


@app.get("/audits", response_model=list[AuditListItemResponse])
async def list_audits(
    request: Request,
    archived: bool = False,
    session: AsyncSession = DB_SESSION_DEPENDENCY,
) -> list[AuditListItemResponse]:
    try:
        current_user = await get_authenticated_user_from_request(session, request)
        return await list_audit_records(session, current_user, archived=archived)
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail="Failed to load audits.") from exc


@app.post("/audits/estimate", response_model=AuditEstimateResponse)
async def estimate_audit(
    payload: AuditEstimateRequest,
    request: Request,
    session: AsyncSession = DB_SESSION_DEPENDENCY,
) -> AuditEstimateResponse:
    try:
        await get_authenticated_user_from_request(session, request)
        return estimate_audit_payload(payload)
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail="Failed to estimate audit.") from exc


@app.get(
    "/model-catalog",
    response_model=ModelCatalogResponse,
    response_model_exclude_none=True,
)
async def get_model_catalog_endpoint(
    request: Request,
    session: AsyncSession = DB_SESSION_DEPENDENCY,
) -> ModelCatalogResponse:
    try:
        await get_authenticated_user_from_request(session, request)
        result = await get_openrouter_model_catalog()
        if result.diagnostic is not None and not result.families:
            raise HTTPException(status_code=503, detail=result.diagnostic)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to load model catalog.") from exc


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


@app.put("/audits/{audit_id}", response_model=AuditDetailResponse)
async def update_audit(
    audit_id: int,
    payload: AuditCreateRequest,
    request: Request,
    session: AsyncSession = DB_SESSION_DEPENDENCY,
) -> AuditDetailResponse:
    try:
        current_user = await get_authenticated_user_from_request(session, request)
        audit, _brand = await load_accessible_audit(session, audit_id, current_user)
        return await update_audit_record(session, audit, payload)
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Failed to update audit.") from exc


@app.post("/audits/{audit_id}/archive", response_model=AuditActionResponse)
async def archive_audit(
    audit_id: int,
    request: Request,
    session: AsyncSession = DB_SESSION_DEPENDENCY,
) -> AuditActionResponse:
    try:
        current_user = await get_authenticated_user_from_request(session, request)
        audit, _brand = await load_accessible_audit(session, audit_id, current_user)
        return await archive_audit_record(session, audit)
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Failed to archive audit.") from exc


@app.post("/audits/{audit_id}/restore", response_model=AuditActionResponse)
async def restore_audit(
    audit_id: int,
    request: Request,
    session: AsyncSession = DB_SESSION_DEPENDENCY,
) -> AuditActionResponse:
    try:
        current_user = await get_authenticated_user_from_request(session, request)
        audit, _brand = await load_accessible_audit(session, audit_id, current_user)
        return await restore_audit_record(session, audit)
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Failed to restore audit.") from exc


@app.delete("/audits/{audit_id}", status_code=204)
async def delete_audit(
    audit_id: int,
    request: Request,
    session: AsyncSession = DB_SESSION_DEPENDENCY,
) -> Response:
    try:
        current_user = await get_authenticated_user_from_request(session, request)
        audit, _brand = await load_accessible_audit(session, audit_id, current_user)
        await delete_archived_audit_record(session, audit)
        return Response(status_code=204)
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete audit.") from exc


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


@app.post("/dev/audits/{audit_id}/run-pipeline", response_model=AuditPipelineRunResponse)
async def run_audit_pipeline_dev(
    audit_id: int,
    request: Request,
    session: AsyncSession = DB_SESSION_DEPENDENCY,
) -> AuditPipelineRunResponse:
    try:
        current_user = await get_authenticated_user_from_request(session, request)
        if not _is_admin(current_user):
            raise HTTPException(status_code=403, detail=DEV_PIPELINE_FORBIDDEN_DETAIL)
        audit, _brand = await load_accessible_audit(session, audit_id, current_user)
        summary = await run_audit_pipeline(session, audit.id)
        return build_pipeline_run_response(
            summary,
            provider_diagnostics=await _pipeline_provider_diagnostics(
                session,
                audit,
                summary,
            ),
        )
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Failed to run audit pipeline.") from exc


@app.post("/audits/{audit_id}/run-pipeline", response_model=AuditPipelineRunResponse)
async def run_audit_pipeline_owner(
    audit_id: int,
    request: Request,
    session: AsyncSession = DB_SESSION_DEPENDENCY,
) -> AuditPipelineRunResponse:
    try:
        current_user = await get_authenticated_user_from_request(session, request)
        audit, _brand = await load_accessible_audit(session, audit_id, current_user)
        await validate_audit_pipeline_triggerable(session, audit)
        summary = await run_audit_pipeline(session, audit.id)
        return build_pipeline_run_response(
            summary,
            provider_diagnostics=await _pipeline_provider_diagnostics(
                session,
                audit,
                summary,
            ),
        )
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Failed to run audit pipeline.") from exc


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


@app.get(
    "/audits/{audit_id}/runs/{run_id}/raw",
    response_model=RawResponseInspectionResponse,
)
async def get_raw_response_inspection(
    audit_id: int,
    run_id: int,
    request: Request,
    session: AsyncSession = DB_SESSION_DEPENDENCY,
) -> RawResponseInspectionResponse:
    try:
        current_user = await get_authenticated_user_from_request(session, request)
        if not _is_admin(current_user):
            raise HTTPException(status_code=403, detail=RAW_RESPONSE_FORBIDDEN_DETAIL)
        audit, _brand = await load_accessible_audit(session, audit_id, current_user)
        return await build_raw_response_inspection_response(session, audit, run_id)
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to inspect raw response.",
        ) from exc

