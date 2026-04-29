"""API entrypoint for audit lifecycle operations."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

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
from libs.control.query_capping import cap_queries
from libs.control.query_deduplication import deduplicate_queries
from libs.control.query_normalization import normalize_seed_queries
from libs.storage.models import Audit, AuditStatus, Brand, Query, User, UserRole

SUPPORTED_PROVIDERS = frozenset({"mock", "openai", "anthropic", "gemini"})
MAX_BRAND_NAME_LENGTH = 255
MAX_EMAIL_LENGTH = 255
DB_SESSION_DEPENDENCY = Depends(get_db_session)
UNAUTHORIZED_DETAIL = "Invalid authentication credentials."


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


def get_runtime_auth_config() -> AuthConfig:
    try:
        return load_auth_config()
    except AuthConfigError as exc:
        raise HTTPException(status_code=500, detail="Auth configuration is invalid.") from exc


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

