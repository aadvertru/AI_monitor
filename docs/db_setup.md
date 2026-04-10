# DB Setup (T2)

## Environment variables

- `DATABASE_URL` (required): Postgres DSN, for example `postgresql://user:pass@host:5432/dbname`
- `DB_CONNECT_TIMEOUT_SECONDS` (optional): numeric connection timeout in seconds, default `5`
- `AUTO_CREATE_SCHEMA` (optional): enables `Base.metadata.create_all` only for local dev/test when set to `1/true/yes/on`

## Schema management

- By default, API startup does **not** auto-create tables.
- Production schema changes should be applied via Alembic migrations, not `create_all`.
- `AUTO_CREATE_SCHEMA` is intended only for local development/testing convenience.

## Failure behavior

- Missing `DATABASE_URL` -> raises `DBConfigError("DATABASE_URL is required.")`
- Non-Postgres `DATABASE_URL` scheme -> raises `DBConfigError`
- Invalid timeout value (`non-numeric` or `<= 0`) -> raises `DBConfigError`
- Connection/query failure -> raises `DBConnectionError`

