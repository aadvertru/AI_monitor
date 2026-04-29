from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from apps.api.audit_schemas import (
    AuditDetailResponse,
    AuditListItemResponse,
    AuditResultRowResponse,
    AuditResultsResponse,
    AuditStatusResponse,
    AuditSummaryResponse,
    CompetitorSummaryItemResponse,
    ComponentScoresResponse,
    CriticalQueryItemResponse,
    SourceSummaryItemResponse,
)

NOW = datetime(2026, 4, 29, 9, 30, tzinfo=timezone.utc)
SENSITIVE_KEYS = {
    "user_id",
    "email",
    "password",
    "hashed_password",
    "raw_answer",
    "provider_secret",
    "api_key",
}


def _dump_json(model) -> dict:
    return model.model_dump(mode="json")


def _assert_no_sensitive_keys(value) -> None:
    if isinstance(value, dict):
        assert SENSITIVE_KEYS.isdisjoint(value)
        for item in value.values():
            _assert_no_sensitive_keys(item)
    elif isinstance(value, list):
        for item in value:
            _assert_no_sensitive_keys(item)


def test_audit_list_item_serializes_dashboard_fields() -> None:
    payload = _dump_json(
        AuditListItemResponse(
            audit_id=42,
            audit_number=3,
            brand_name="Acme AI",
            brand_domain="acme.example",
            status="running",
            providers=["mock", "openai"],
            runs_per_query=2,
            created_at=NOW,
            updated_at=NOW,
        )
    )

    assert payload == {
        "audit_id": 42,
        "audit_number": 3,
        "brand_name": "Acme AI",
        "brand_domain": "acme.example",
        "status": "running",
        "scdl_level": "L1",
        "providers": ["mock", "openai"],
        "runs_per_query": 2,
        "created_at": "2026-04-29T09:30:00Z",
        "updated_at": "2026-04-29T09:30:00Z",
    }
    _assert_no_sensitive_keys(payload)


def test_audit_detail_serializes_metadata_and_optional_fields() -> None:
    payload = _dump_json(
        AuditDetailResponse(
            audit_id=42,
            audit_number=3,
            brand_id=7,
            brand_name="Acme AI",
            status="created",
            providers=["mock"],
            runs_per_query=1,
            language=None,
            country=None,
            locale=None,
            max_queries=None,
            seed_queries=["best ai visibility monitor"],
            enable_query_expansion=False,
            enable_source_intelligence=True,
            follow_up_depth=1,
            created_at=NOW,
            updated_at=NOW,
        )
    )

    assert payload["audit_id"] == 42
    assert payload["audit_number"] == 3
    assert payload["brand_id"] == 7
    assert payload["brand_domain"] is None
    assert payload["scdl_level"] == "L1"
    assert payload["seed_queries"] == ["best ai visibility monitor"]
    assert payload["enable_source_intelligence"] is True
    _assert_no_sensitive_keys(payload)


def test_audit_status_serializes_without_internal_job_details() -> None:
    payload = _dump_json(
        AuditStatusResponse(
            audit_id=42,
            audit_number=3,
            status="partial",
            total_runs=4,
            completed_runs=2,
            failed_runs=2,
            completion_ratio=0.5,
            updated_at=NOW,
        )
    )

    assert payload == {
        "audit_id": 42,
        "audit_number": 3,
        "status": "partial",
        "scdl_level": "L1",
        "total_runs": 4,
        "completed_runs": 2,
        "failed_runs": 2,
        "completion_ratio": 0.5,
        "updated_at": "2026-04-29T09:30:00Z",
    }
    assert "jobs" not in payload
    _assert_no_sensitive_keys(payload)


def test_audit_result_row_serializes_query_provider_run_shape() -> None:
    payload = _dump_json(
        AuditResultRowResponse(
            audit_id=42,
            query_id=10,
            query="best ai visibility monitor",
            provider="mock",
            run_id=99,
            run_number=2,
            run_status="success",
            visible_brand=True,
            brand_position_rank=1,
            final_score=0.91,
            component_scores=ComponentScoresResponse(
                visibility_score=1.0,
                prominence_score=0.88,
                sentiment_score=0.75,
                recommendation_score=0.9,
                source_quality_score=0.6,
            ),
            competitors=["Other Monitor"],
            sources=[
                SourceSummaryItemResponse(
                    title="Industry Review",
                    url="https://example.test/review",
                    domain="example.test",
                    provider="mock",
                    citation_count=1,
                    source_quality_score=0.7,
                )
            ],
            raw_answer_ref=501,
        )
    )

    assert payload["query"] == "best ai visibility monitor"
    assert payload["provider"] == "mock"
    assert payload["run_number"] == 2
    assert payload["run_status"] == "success"
    assert payload["scdl_level"] == "L1"
    assert payload["component_scores"]["visibility_score"] == 1.0
    assert payload["raw_answer_ref"] == 501
    assert "raw_answer" not in payload
    _assert_no_sensitive_keys(payload)


def test_empty_results_response_serializes_stable_shape() -> None:
    payload = _dump_json(AuditResultsResponse(audit_id=42, audit_number=3))

    assert payload == {
        "audit_id": 42,
        "audit_number": 3,
        "rows": [],
        "total": 0,
    }
    _assert_no_sensitive_keys(payload)


def test_audit_summary_serializes_metrics_competitors_sources_and_critical_queries() -> None:
    payload = _dump_json(
        AuditSummaryResponse(
            audit_id=42,
            audit_number=3,
            status="completed",
            total_queries=2,
            total_runs=4,
            successful_runs=3,
            failed_runs=1,
            completion_ratio=0.75,
            visibility_ratio=0.67,
            average_score=0.62,
            critical_query_count=1,
            provider_scores={"mock": 0.62, "openai": None},
            critical_queries=[
                CriticalQueryItemResponse(
                    query="best ai visibility monitor",
                    reason="low_score",
                    query_score=0.22,
                )
            ],
            competitors=[
                CompetitorSummaryItemResponse(
                    name="Other Monitor",
                    mention_count=2,
                    visibility_ratio=0.5,
                    average_score=0.48,
                )
            ],
            sources=[
                SourceSummaryItemResponse(
                    domain="example.test",
                    provider="mock",
                    source_type="citation",
                    citation_count=3,
                    related_query_count=2,
                )
            ],
        )
    )

    assert payload["completion_ratio"] == 0.75
    assert payload["audit_number"] == 3
    assert payload["visibility_ratio"] == 0.67
    assert payload["critical_queries"][0]["reason"] == "low_score"
    assert payload["competitors"][0]["name"] == "Other Monitor"
    assert payload["sources"][0]["citation_count"] == 3
    _assert_no_sensitive_keys(payload)


def test_partial_or_failed_summary_shape_serializes_missing_optional_metrics() -> None:
    payload = _dump_json(
        AuditSummaryResponse(
            audit_id=42,
            audit_number=3,
            status="failed",
            total_queries=1,
            total_runs=2,
            successful_runs=0,
            failed_runs=2,
            completion_ratio=0.0,
            visibility_ratio=0.0,
            average_score=None,
            critical_query_count=1,
            provider_scores={"mock": None},
            critical_queries=[
                CriticalQueryItemResponse(
                    query="best ai visibility monitor",
                    reason="no_successful_runs",
                    query_score=None,
                )
            ],
        )
    )

    assert payload["status"] == "failed"
    assert payload["average_score"] is None
    assert payload["provider_scores"] == {"mock": None}
    assert payload["competitors"] == []
    assert payload["sources"] == []
    _assert_no_sensitive_keys(payload)


def test_audit_response_schemas_reject_sensitive_auth_or_raw_fields() -> None:
    with pytest.raises(ValidationError):
        AuditListItemResponse(
            audit_id=42,
            audit_number=3,
            brand_name="Acme AI",
            status="created",
            providers=["mock"],
            runs_per_query=1,
            created_at=NOW,
            updated_at=NOW,
            user_id=3,
        )

    with pytest.raises(ValidationError):
        AuditResultRowResponse(
            audit_id=42,
            query_id=10,
            query="best ai visibility monitor",
            provider="mock",
            run_id=99,
            run_number=1,
            run_status="success",
            raw_answer="full model output",
        )


def test_audit_result_row_rejects_run_status_not_backed_by_storage_enum() -> None:
    with pytest.raises(ValidationError):
        AuditResultRowResponse(
            audit_id=42,
            query_id=10,
            query="best ai visibility monitor",
            provider="mock",
            run_id=99,
            run_number=1,
            run_status="skipped",
        )
