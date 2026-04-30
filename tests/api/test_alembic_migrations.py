from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import patch

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_alembic_upgrade_head_creates_current_schema() -> None:
    temp_dir = Path("testtmp")
    temp_dir.mkdir(exist_ok=True)
    db_path = temp_dir / "alembic_upgrade.db"
    if db_path.exists():
        db_path.unlink()

    db_url = f"sqlite:///{db_path.as_posix()}"

    config = Config("apps/api/alembic.ini")
    with patch.dict("os.environ", {"DATABASE_URL": db_url}):
        command.upgrade(config, "head")

    engine = create_engine(db_url)
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    assert {
        "alembic_version",
        "brands",
        "users",
        "audits",
        "queries",
        "jobs",
        "runs",
        "parsed_results",
        "raw_responses",
        "scores",
    }.issubset(table_names)

    assert "role" in _column_names(inspector, "users")
    assert {"user_id", "scdl_level"}.issubset(_column_names(inspector, "audits"))
    assert "status" in _column_names(inspector, "runs")
    assert "sources" in _column_names(inspector, "parsed_results")

    audit_checks = " ".join(
        check["sqltext"] for check in inspector.get_check_constraints("audits")
    )
    assert "follow_up_depth" in audit_checks
    assert "runs_per_query" in audit_checks

    assert "uq_jobs_idempotency_key" in _unique_names(inspector, "jobs")
    assert "uq_runs_execution_identity" in _unique_names(inspector, "runs")

    with sqlite3.connect(db_path) as connection:
        version = connection.execute("SELECT version_num FROM alembic_version").fetchone()

    assert version == ("0bd42c15e942",)


def _column_names(inspector, table_name: str) -> set[str]:
    return {column["name"] for column in inspector.get_columns(table_name)}


def _unique_names(inspector, table_name: str) -> set[str]:
    return {
        constraint["name"]
        for constraint in inspector.get_unique_constraints(table_name)
        if constraint["name"]
    }
