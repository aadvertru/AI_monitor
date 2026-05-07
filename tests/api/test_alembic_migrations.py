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
        "user_preferences",
        "brand_facts",
        "answer_evaluations",
        "concepts",
        "competitor_candidates",
        "background_jobs",
        "audits",
        "queries",
        "jobs",
        "runs",
        "audit_targets",
        "parsed_results",
        "raw_responses",
        "scores",
    }.issubset(table_names)

    assert "role" in _column_names(inspector, "users")
    assert {
        "user_id",
        "locale",
        "email_notifications",
        "audit_completed_notifications",
        "provider_error_notifications",
    }.issubset(_column_names(inspector, "user_preferences"))
    assert {"user_id", "scdl_level", "archived_at"}.issubset(
        _column_names(inspector, "audits")
    )
    assert {"query_type", "source"}.issubset(_column_names(inspector, "queries"))
    assert "audit_target_id" in _column_names(inspector, "jobs")
    assert {
        "audit_id",
        "ai_family",
        "execution_provider",
        "model_provider",
        "model_id",
        "display_name",
        "level",
        "gateway",
        "gateway_l2_experimental",
    }.issubset(_column_names(inspector, "audit_targets"))
    assert {"status", "audit_target_id"}.issubset(_column_names(inspector, "runs"))
    assert "sources" in _column_names(inspector, "parsed_results")
    assert {
        "audit_id",
        "brand_id",
        "fact_text",
        "fact_type",
        "source",
        "confidence",
        "created_at",
    }.issubset(_column_names(inspector, "brand_facts"))

    audit_checks = " ".join(
        check["sqltext"] for check in inspector.get_check_constraints("audits")
    )
    assert "follow_up_depth" in audit_checks
    assert "runs_per_query" in audit_checks

    assert "uq_jobs_idempotency_key" in _unique_names(inspector, "jobs")
    assert "uq_runs_execution_identity" in _unique_names(inspector, "runs")
    assert "uq_user_preferences_user_id" in _unique_names(inspector, "user_preferences")
    fact_checks = " ".join(
        check["sqltext"] for check in inspector.get_check_constraints("brand_facts")
    )
    assert "fact_type" in fact_checks
    assert "source" in fact_checks
    assert "confidence" in fact_checks
    assert {
        "audit_id",
        "run_id",
        "query_id",
        "target_id",
        "verdict",
        "rationale",
        "confidence",
        "evaluation_version",
        "evaluated_at",
        "evaluator_provider",
        "evaluator_model",
        "facts_version",
        "created_at",
        "updated_at",
    }.issubset(_column_names(inspector, "answer_evaluations"))
    evaluation_checks = " ".join(
        check["sqltext"]
        for check in inspector.get_check_constraints("answer_evaluations")
    )
    assert "verdict" in evaluation_checks
    assert "confidence" in evaluation_checks
    assert "uq_answer_evaluations_run_id" in _unique_names(
        inspector, "answer_evaluations"
    )
    assert {
        "audit_id",
        "run_id",
        "query_id",
        "target_id",
        "text",
        "category",
        "count",
        "evidence_count",
        "evidence",
        "created_at",
        "updated_at",
    }.issubset(_column_names(inspector, "concepts"))
    concept_checks = " ".join(
        check["sqltext"] for check in inspector.get_check_constraints("concepts")
    )
    assert "count" in concept_checks
    assert "evidence_count" in concept_checks
    assert {
        "audit_id",
        "name",
        "domain",
        "confidence",
        "evidence_type",
        "evidence_count",
        "evidence",
        "created_at",
        "updated_at",
    }.issubset(_column_names(inspector, "competitor_candidates"))
    candidate_checks = " ".join(
        check["sqltext"]
        for check in inspector.get_check_constraints("competitor_candidates")
    )
    assert "confidence" in candidate_checks
    assert "evidence_count" in candidate_checks
    assert {
        "job_type",
        "audit_id",
        "user_id",
        "status",
        "created_at",
        "started_at",
        "finished_at",
        "error_code",
        "error_message_safe",
        "progress_metadata",
        "cancel_requested_at",
    }.issubset(_column_names(inspector, "background_jobs"))
    background_job_checks = " ".join(
        check["sqltext"] for check in inspector.get_check_constraints("background_jobs")
    )
    assert "cancel_requested" in background_job_checks
    assert "cancelled" in background_job_checks
    preference_checks = " ".join(
        check["sqltext"]
        for check in inspector.get_check_constraints("user_preferences")
    )
    assert "locale" in preference_checks
    target_checks = " ".join(
        check["sqltext"] for check in inspector.get_check_constraints("audit_targets")
    )
    assert "level" in target_checks
    assert "gateway_l2_experimental" in target_checks

    with sqlite3.connect(db_path) as connection:
        version = connection.execute("SELECT version_num FROM alembic_version").fetchone()

    assert version == ("1a2b3c4d5e6f",)


def _column_names(inspector, table_name: str) -> set[str]:
    return {column["name"] for column in inspector.get_columns(table_name)}


def _unique_names(inspector, table_name: str) -> set[str]:
    return {
        constraint["name"]
        for constraint in inspector.get_unique_constraints(table_name)
        if constraint["name"]
    }
