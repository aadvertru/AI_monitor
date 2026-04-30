# Database migrations

The API uses Alembic for schema changes. The migration environment is async
SQLAlchemy compatible and enables SQLite batch mode for local and test databases.

## Apply migrations

```powershell
.\venv\Scripts\python.exe -m alembic -c apps/api/alembic.ini upgrade head
```

Set `DATABASE_URL` when targeting a non-default database:

```powershell
$env:DATABASE_URL="sqlite:///./ai_monitor.db"
.\venv\Scripts\python.exe -m alembic -c apps/api/alembic.ini upgrade head
```

## Existing local databases

If a local database was already created with `AUTO_CREATE_SCHEMA=1` and matches
the current models, mark it as being at the latest migration without recreating
tables:

```powershell
$env:DATABASE_URL="sqlite:///./ai_monitor.db"
.\venv\Scripts\python.exe -m alembic -c apps/api/alembic.ini stamp head
```

## Create a migration

Prefer autogeneration from `libs.storage.models.Base` and then review the
generated diff before committing it:

```powershell
$env:DATABASE_URL="sqlite:///./ai_monitor.db"
.\venv\Scripts\python.exe -m alembic -c apps/api/alembic.ini revision --autogenerate -m "describe change"
```

`AUTO_CREATE_SCHEMA=1` remains available as a development fallback, but planned
schema evolution should go through Alembic migrations.
