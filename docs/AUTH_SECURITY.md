# Auth Security Policy

## Local frontend/backend origins

The FastAPI backend supports credentialed browser requests from explicit frontend
origins only. Configure them with:

```text
FRONTEND_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Do not use `*` with credentialed CORS. The backend rejects wildcard origins for
this policy boundary.

## Auth cookie policy

JWT auth is intended to use an httpOnly cookie. The policy is configured in
`apps/api/security.py` through environment variables:

```text
AUTH_COOKIE_NAME=auth_token
AUTH_COOKIE_HTTPONLY=true
AUTH_COOKIE_SECURE=false
AUTH_COOKIE_SAMESITE=lax
AUTH_COOKIE_PATH=/
AUTH_COOKIE_MAX_AGE_SECONDS=1800
```

Use `AUTH_COOKIE_SECURE=true` for HTTPS deployments. Local development may keep
it `false` so the browser can send cookies over `http://localhost`.

## MVP CSRF stance

For MVP, CSRF risk is bounded by httpOnly JWT cookies, explicit credentialed CORS
origins, and `SameSite=lax` by default. A dedicated CSRF token strategy is not
introduced in TASK-103 because no cross-site cookie flow is required yet.
