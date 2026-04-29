from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.security import (
    AuthConfigError,
    AuthTokenError,
    configure_cors,
    create_access_token,
    hash_password,
    load_auth_config,
    load_cors_config,
    verify_access_token,
    verify_password,
)


class SecurityUtilityTests(unittest.TestCase):
    def _auth_config(self):
        return load_auth_config(
            env={
                "JWT_SECRET": "test-secret-value",
                "ACCESS_TOKEN_EXPIRE_MINUTES": "15",
            }
        )

    def test_hash_and_verify_valid_password(self) -> None:
        password = "correct horse battery staple"

        stored_hash = hash_password(password)

        self.assertTrue(verify_password(password, stored_hash))

    def test_password_hash_is_not_plain_password(self) -> None:
        password = "plain-password"

        stored_hash = hash_password(password)

        self.assertNotEqual(stored_hash, password)
        self.assertTrue(stored_hash.startswith("pbkdf2_sha256$"))

    def test_verify_password_rejects_invalid_password(self) -> None:
        stored_hash = hash_password("valid-password")

        self.assertFalse(verify_password("invalid-password", stored_hash))
        self.assertFalse(verify_password("valid-password", "not-a-supported-hash"))

    def test_create_and_verify_access_token_roundtrip(self) -> None:
        config = self._auth_config()
        issued_at = datetime(2026, 4, 28, 10, 0, tzinfo=timezone.utc)

        token = create_access_token(
            user_id=42,
            role="admin",
            config=config,
            now=issued_at,
        )
        claims = verify_access_token(
            token,
            config=config,
            now=issued_at + timedelta(minutes=1),
        )

        self.assertEqual(claims.user_id, 42)
        self.assertEqual(claims.role, "admin")
        self.assertEqual(claims.issued_at, issued_at)
        self.assertEqual(claims.expires_at, issued_at + timedelta(minutes=15))

    def test_verify_access_token_rejects_invalid_token(self) -> None:
        config = self._auth_config()

        with self.assertRaises(AuthTokenError):
            verify_access_token("not-a-jwt", config=config)

        valid_token = create_access_token(
            user_id=1,
            role="user",
            config=config,
            now=datetime(2026, 4, 28, 10, 0, tzinfo=timezone.utc),
        )
        tampered_token = f"{valid_token[:-1]}x"

        with self.assertRaises(AuthTokenError):
            verify_access_token(tampered_token, config=config)

    def test_verify_access_token_rejects_expired_token(self) -> None:
        config = load_auth_config(
            env={
                "JWT_SECRET": "test-secret-value",
                "ACCESS_TOKEN_EXPIRE_MINUTES": "1",
            }
        )
        issued_at = datetime(2026, 4, 28, 10, 0, tzinfo=timezone.utc)
        token = create_access_token(
            user_id=1,
            role="user",
            config=config,
            now=issued_at,
        )

        with self.assertRaises(AuthTokenError):
            verify_access_token(
                token,
                config=config,
                now=issued_at + timedelta(minutes=1),
            )

    def test_auth_config_loads_from_environment_values(self) -> None:
        config = load_auth_config(
            env={
                "JWT_SECRET": "configured-secret",
                "JWT_ALGORITHM": "HS256",
                "ACCESS_TOKEN_EXPIRE_MINUTES": "45",
                "AUTH_COOKIE_NAME": "session",
                "AUTH_COOKIE_HTTPONLY": "true",
                "AUTH_COOKIE_SECURE": "true",
                "AUTH_COOKIE_SAMESITE": "strict",
            }
        )

        self.assertEqual(config.jwt_secret, "configured-secret")
        self.assertEqual(config.jwt_algorithm, "HS256")
        self.assertEqual(config.access_token_expire_minutes, 45)
        self.assertEqual(config.cookie.name, "session")
        self.assertTrue(config.cookie.httponly)
        self.assertTrue(config.cookie.secure)
        self.assertEqual(config.cookie.samesite, "strict")
        self.assertEqual(config.cookie.path, "/")
        self.assertEqual(config.cookie.max_age_seconds, 45 * 60)

    def test_auth_config_requires_jwt_secret(self) -> None:
        with self.assertRaises(AuthConfigError):
            load_auth_config(env={})

    def test_auth_cookie_config_exposes_httponly_default(self) -> None:
        config = self._auth_config()

        self.assertEqual(config.cookie.name, "auth_token")
        self.assertTrue(config.cookie.httponly)
        self.assertFalse(config.cookie.secure)
        self.assertEqual(config.cookie.samesite, "lax")
        self.assertEqual(config.cookie.path, "/")
        self.assertEqual(config.cookie.max_age_seconds, 15 * 60)

    def test_auth_cookie_path_and_max_age_can_be_configured(self) -> None:
        config = load_auth_config(
            env={
                "JWT_SECRET": "test-secret-value",
                "AUTH_COOKIE_PATH": "/api",
                "AUTH_COOKIE_MAX_AGE_SECONDS": "120",
            }
        )

        self.assertEqual(config.cookie.path, "/api")
        self.assertEqual(config.cookie.max_age_seconds, 120)

    def test_cors_config_loads_allowed_origins_from_environment(self) -> None:
        cors_config = load_cors_config(
            env={
                "FRONTEND_ALLOWED_ORIGINS": (
                    "http://localhost:5173, https://app.example.com/"
                )
            }
        )

        self.assertEqual(
            cors_config.allowed_origins,
            ("http://localhost:5173", "https://app.example.com"),
        )
        self.assertTrue(cors_config.allow_credentials)

    def test_cors_config_rejects_wildcard_with_credentials(self) -> None:
        with self.assertRaises(AuthConfigError):
            load_cors_config(env={"FRONTEND_ALLOWED_ORIGINS": "*"})

    def test_cors_config_has_local_development_defaults(self) -> None:
        cors_config = load_cors_config(env={})

        self.assertEqual(
            cors_config.allowed_origins,
            ("http://localhost:5173", "http://127.0.0.1:5173"),
        )
        self.assertTrue(cors_config.allow_credentials)

    def test_configure_cors_attaches_credentialed_middleware(self) -> None:
        app = FastAPI()

        cors_config = configure_cors(
            app,
            env={"FRONTEND_ALLOWED_ORIGINS": "http://localhost:5173"},
        )

        self.assertEqual(cors_config.allowed_origins, ("http://localhost:5173",))
        self.assertEqual(len(app.user_middleware), 1)
        middleware = app.user_middleware[0]
        self.assertIs(middleware.cls, CORSMiddleware)
        self.assertEqual(middleware.kwargs["allow_origins"], ["http://localhost:5173"])
        self.assertTrue(middleware.kwargs["allow_credentials"])


if __name__ == "__main__":
    unittest.main()
