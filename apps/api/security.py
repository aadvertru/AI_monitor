"""Password hashing, JWT, and auth cookie utilities."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

PASSWORD_HASH_ALGORITHM = "pbkdf2_sha256"
PASSWORD_HASH_ITERATIONS = 600_000
PASSWORD_SALT_BYTES = 16
SUPPORTED_JWT_ALGORITHM = "HS256"

JWT_SECRET_ENV = "JWT_SECRET"
JWT_ALGORITHM_ENV = "JWT_ALGORITHM"
ACCESS_TOKEN_EXPIRE_MINUTES_ENV = "ACCESS_TOKEN_EXPIRE_MINUTES"
AUTH_COOKIE_NAME_ENV = "AUTH_COOKIE_NAME"
AUTH_COOKIE_HTTPONLY_ENV = "AUTH_COOKIE_HTTPONLY"
AUTH_COOKIE_SECURE_ENV = "AUTH_COOKIE_SECURE"
AUTH_COOKIE_SAMESITE_ENV = "AUTH_COOKIE_SAMESITE"
AUTH_COOKIE_PATH_ENV = "AUTH_COOKIE_PATH"
AUTH_COOKIE_MAX_AGE_SECONDS_ENV = "AUTH_COOKIE_MAX_AGE_SECONDS"
FRONTEND_ALLOWED_ORIGINS_ENV = "FRONTEND_ALLOWED_ORIGINS"

_TRUE_ENV_VALUES = {"1", "true", "yes", "on"}
_FALSE_ENV_VALUES = {"0", "false", "no", "off"}
_VALID_SAMESITE_VALUES = {"lax", "strict", "none"}
DEFAULT_FRONTEND_ALLOWED_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)

# MVP CSRF stance:
# Auth uses an httpOnly JWT cookie and SameSite defaults to "lax", which blocks most
# cross-site state-changing form posts while keeping local Vite/FastAPI development
# simple. TASK-103 defines this policy boundary only; a stricter CSRF token strategy
# can be added later if product/security requirements demand cross-site cookie use.


class AuthConfigError(ValueError):
    """Raised when auth/security configuration is invalid."""


class AuthTokenError(ValueError):
    """Raised when a JWT cannot be safely verified."""


@dataclass(frozen=True)
class AuthCookieConfig:
    name: str
    httponly: bool
    secure: bool
    samesite: str
    path: str
    max_age_seconds: int


@dataclass(frozen=True)
class CorsConfig:
    allowed_origins: tuple[str, ...]
    allow_credentials: bool = True
    allow_methods: tuple[str, ...] = ("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")
    allow_headers: tuple[str, ...] = ("Content-Type", "Authorization")


@dataclass(frozen=True)
class AuthConfig:
    jwt_secret: str
    jwt_algorithm: str = SUPPORTED_JWT_ALGORITHM
    access_token_expire_minutes: int = 30
    cookie: AuthCookieConfig = AuthCookieConfig(
        name="auth_token",
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
        max_age_seconds=30 * 60,
    )


@dataclass(frozen=True)
class TokenClaims:
    user_id: int
    role: str
    issued_at: datetime
    expires_at: datetime


def _parse_bool_env(raw_value: str, *, field_name: str) -> bool:
    normalized = raw_value.strip().lower()
    if normalized in _TRUE_ENV_VALUES:
        return True
    if normalized in _FALSE_ENV_VALUES:
        return False
    raise AuthConfigError(f"{field_name} must be a boolean value.")


def _parse_positive_int(raw_value: str, *, field_name: str) -> int:
    try:
        parsed_value = int(raw_value.strip())
    except ValueError as exc:
        raise AuthConfigError(f"{field_name} must be an integer.") from exc
    if parsed_value <= 0:
        raise AuthConfigError(f"{field_name} must be greater than 0.")
    return parsed_value


def _normalize_origins(raw_origins: str) -> tuple[str, ...]:
    origins = tuple(
        origin.strip().rstrip("/")
        for origin in raw_origins.split(",")
        if origin.strip()
    )
    if not origins:
        raise AuthConfigError("FRONTEND_ALLOWED_ORIGINS must include at least one origin.")
    if "*" in origins:
        raise AuthConfigError(
            "FRONTEND_ALLOWED_ORIGINS must not include '*' when credentials are allowed."
        )
    return origins


def load_auth_config(env: Mapping[str, str] | None = None) -> AuthConfig:
    """Load auth security settings from environment-style values."""
    source = env if env is not None else os.environ
    jwt_secret = source.get(JWT_SECRET_ENV, "").strip()
    if not jwt_secret:
        raise AuthConfigError("JWT_SECRET is required.")

    jwt_algorithm = source.get(JWT_ALGORITHM_ENV, SUPPORTED_JWT_ALGORITHM).strip()
    if jwt_algorithm != SUPPORTED_JWT_ALGORITHM:
        raise AuthConfigError("JWT_ALGORITHM must be HS256.")

    access_token_expire_minutes = _parse_positive_int(
        source.get(ACCESS_TOKEN_EXPIRE_MINUTES_ENV, "30"),
        field_name=ACCESS_TOKEN_EXPIRE_MINUTES_ENV,
    )

    cookie_name = source.get(AUTH_COOKIE_NAME_ENV, "auth_token").strip()
    if not cookie_name:
        raise AuthConfigError("AUTH_COOKIE_NAME must not be empty.")

    cookie_httponly = _parse_bool_env(
        source.get(AUTH_COOKIE_HTTPONLY_ENV, "true"),
        field_name=AUTH_COOKIE_HTTPONLY_ENV,
    )
    cookie_secure = _parse_bool_env(
        source.get(AUTH_COOKIE_SECURE_ENV, "false"),
        field_name=AUTH_COOKIE_SECURE_ENV,
    )
    cookie_samesite = source.get(AUTH_COOKIE_SAMESITE_ENV, "lax").strip().lower()
    if cookie_samesite not in _VALID_SAMESITE_VALUES:
        raise AuthConfigError("AUTH_COOKIE_SAMESITE must be lax, strict, or none.")

    cookie_path = source.get(AUTH_COOKIE_PATH_ENV, "/").strip()
    if not cookie_path.startswith("/"):
        raise AuthConfigError("AUTH_COOKIE_PATH must start with '/'.")

    cookie_max_age_seconds = _parse_positive_int(
        source.get(
            AUTH_COOKIE_MAX_AGE_SECONDS_ENV,
            str(access_token_expire_minutes * 60),
        ),
        field_name=AUTH_COOKIE_MAX_AGE_SECONDS_ENV,
    )

    return AuthConfig(
        jwt_secret=jwt_secret,
        jwt_algorithm=jwt_algorithm,
        access_token_expire_minutes=access_token_expire_minutes,
        cookie=AuthCookieConfig(
            name=cookie_name,
            httponly=cookie_httponly,
            secure=cookie_secure,
            samesite=cookie_samesite,
            path=cookie_path,
            max_age_seconds=cookie_max_age_seconds,
        ),
    )


def load_cors_config(env: Mapping[str, str] | None = None) -> CorsConfig:
    """Load credentialed CORS settings for the browser frontend."""
    source = env if env is not None else os.environ
    raw_origins = source.get(
        FRONTEND_ALLOWED_ORIGINS_ENV,
        ",".join(DEFAULT_FRONTEND_ALLOWED_ORIGINS),
    )
    return CorsConfig(allowed_origins=_normalize_origins(raw_origins))


def configure_cors(app: FastAPI, env: Mapping[str, str] | None = None) -> CorsConfig:
    """Attach FastAPI CORS middleware using the configured frontend origins."""
    cors_config = load_cors_config(env=env)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(cors_config.allowed_origins),
        allow_credentials=cors_config.allow_credentials,
        allow_methods=list(cors_config.allow_methods),
        allow_headers=list(cors_config.allow_headers),
    )
    return cors_config


def _base64url_encode(raw_value: bytes) -> str:
    return base64.urlsafe_b64encode(raw_value).decode("ascii").rstrip("=")


def _base64url_decode(raw_value: str) -> bytes:
    padding = "=" * (-len(raw_value) % 4)
    try:
        return base64.urlsafe_b64decode((raw_value + padding).encode("ascii"))
    except Exception as exc:
        raise AuthTokenError("Invalid token encoding.") from exc


def hash_password(password: str) -> str:
    """Hash a password using salted PBKDF2-SHA256."""
    salt = secrets.token_bytes(PASSWORD_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_HASH_ITERATIONS,
    )
    return "$".join(
        [
            PASSWORD_HASH_ALGORITHM,
            str(PASSWORD_HASH_ITERATIONS),
            _base64url_encode(salt),
            _base64url_encode(digest),
        ]
    )


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against a stored PBKDF2-SHA256 hash."""
    try:
        algorithm, raw_iterations, raw_salt, raw_digest = stored_hash.split("$", 3)
        iterations = int(raw_iterations)
    except ValueError:
        return False

    if algorithm != PASSWORD_HASH_ALGORITHM or iterations <= 0:
        return False

    try:
        salt = _base64url_decode(raw_salt)
        expected_digest = _base64url_decode(raw_digest)
    except AuthTokenError:
        return False

    actual_digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(actual_digest, expected_digest)


def _json_base64url(value: dict[str, Any]) -> str:
    encoded = json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return _base64url_encode(encoded)


def _sign_token(signing_input: str, *, secret: str) -> str:
    signature = hmac.new(
        secret.encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return _base64url_encode(signature)


def create_access_token(
    *,
    user_id: int,
    role: str,
    config: AuthConfig,
    now: datetime | None = None,
) -> str:
    """Create an HS256 JWT with user id and role claims."""
    issued_at = now or datetime.now(tz=timezone.utc)
    issued_at = issued_at.astimezone(timezone.utc)
    expires_at = issued_at + timedelta(minutes=config.access_token_expire_minutes)
    header = {"alg": config.jwt_algorithm, "typ": "JWT"}
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    signing_input = f"{_json_base64url(header)}.{_json_base64url(payload)}"
    return f"{signing_input}.{_sign_token(signing_input, secret=config.jwt_secret)}"


def verify_access_token(
    token: str,
    *,
    config: AuthConfig,
    now: datetime | None = None,
) -> TokenClaims:
    """Verify an HS256 JWT and return typed token claims."""
    try:
        raw_header, raw_payload, raw_signature = token.split(".", 2)
    except ValueError as exc:
        raise AuthTokenError("Invalid token structure.") from exc

    signing_input = f"{raw_header}.{raw_payload}"
    expected_signature = _sign_token(signing_input, secret=config.jwt_secret)
    if not hmac.compare_digest(raw_signature, expected_signature):
        raise AuthTokenError("Invalid token signature.")

    try:
        header = json.loads(_base64url_decode(raw_header))
        payload = json.loads(_base64url_decode(raw_payload))
    except (json.JSONDecodeError, AuthTokenError) as exc:
        raise AuthTokenError("Invalid token payload.") from exc

    if header.get("alg") != config.jwt_algorithm:
        raise AuthTokenError("Invalid token algorithm.")

    try:
        user_id = int(payload["sub"])
        role = str(payload["role"])
        issued_at_seconds = int(payload["iat"])
        expires_at_seconds = int(payload["exp"])
    except (KeyError, TypeError, ValueError) as exc:
        raise AuthTokenError("Invalid token claims.") from exc

    verified_at = now or datetime.now(tz=timezone.utc)
    verified_at = verified_at.astimezone(timezone.utc)
    if int(verified_at.timestamp()) >= expires_at_seconds:
        raise AuthTokenError("Token has expired.")

    return TokenClaims(
        user_id=user_id,
        role=role,
        issued_at=datetime.fromtimestamp(issued_at_seconds, tz=timezone.utc),
        expires_at=datetime.fromtimestamp(expires_at_seconds, tz=timezone.utc),
    )
