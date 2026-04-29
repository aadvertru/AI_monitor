"""Frontend-facing audit API response contracts.

These schemas are intentionally separate from the SQLAlchemy models and pipeline
objects. Endpoint tasks should map stored data into these DTOs instead of
returning ORM instances directly.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# SCDL mapping: L1 = no web access; L2 = web access.
SCDLLevelValue = Literal["L1", "L2"]
AuditStatusValue = Literal["created", "running", "partial", "completed", "failed"]
RunStatusValue = Literal[
    "pending",
    "success",
    "error",
    "timeout",
    "rate_limited",
]


class FrontendAuditSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AuditListItemResponse(FrontendAuditSchema):
    audit_id: int
    brand_name: str
    brand_domain: str | None = None
    status: AuditStatusValue
    scdl_level: SCDLLevelValue = "L1"
    providers: list[str] = Field(default_factory=list)
    runs_per_query: int
    created_at: datetime
    updated_at: datetime


class AuditDetailResponse(FrontendAuditSchema):
    audit_id: int
    brand_id: int
    brand_name: str
    brand_domain: str | None = None
    brand_description: str | None = None
    status: AuditStatusValue
    scdl_level: SCDLLevelValue = "L1"
    providers: list[str] = Field(default_factory=list)
    runs_per_query: int
    language: str | None = None
    country: str | None = None
    locale: str | None = None
    max_queries: int | None = None
    seed_queries: list[str] = Field(default_factory=list)
    enable_query_expansion: bool = False
    enable_source_intelligence: bool = False
    follow_up_depth: int = 0
    created_at: datetime
    updated_at: datetime


class AuditStatusResponse(FrontendAuditSchema):
    audit_id: int
    status: AuditStatusValue
    scdl_level: SCDLLevelValue = "L1"
    total_runs: int = 0
    completed_runs: int = 0
    failed_runs: int = 0
    completion_ratio: float = 0.0
    updated_at: datetime | None = None


class AuditRunTriggerResponse(FrontendAuditSchema):
    audit_id: int
    status: AuditStatusValue
    scheduled_jobs: int = 0
    total_jobs: int = 0


class ComponentScoresResponse(FrontendAuditSchema):
    visibility_score: float | None = None
    prominence_score: float | None = None
    sentiment_score: float | None = None
    recommendation_score: float | None = None
    source_quality_score: float | None = None


class SourceSummaryItemResponse(FrontendAuditSchema):
    title: str | None = None
    url: str | None = None
    domain: str | None = None
    provider: str | None = None
    source_type: str | None = None
    citation_count: int | None = None
    related_query_count: int | None = None
    source_quality_score: float | None = None


class AuditResultRowResponse(FrontendAuditSchema):
    audit_id: int
    scdl_level: SCDLLevelValue = "L1"
    query_id: int
    query: str
    provider: str
    run_id: int
    run_number: int
    run_status: RunStatusValue
    visible_brand: bool | None = None
    brand_position_rank: int | None = None
    final_score: float | None = None
    component_scores: ComponentScoresResponse | None = None
    competitors: list[str] = Field(default_factory=list)
    sources: list[SourceSummaryItemResponse] = Field(default_factory=list)
    raw_answer_ref: int | None = None
    error_code: str | None = None
    error_message: str | None = None


class AuditResultsResponse(FrontendAuditSchema):
    audit_id: int
    rows: list[AuditResultRowResponse] = Field(default_factory=list)
    total: int = 0


class CompetitorSummaryItemResponse(FrontendAuditSchema):
    name: str
    mention_count: int | None = None
    visibility_ratio: float | None = None
    average_score: float | None = None


class CriticalQueryItemResponse(FrontendAuditSchema):
    query: str
    reason: str
    query_score: float | None = None


class AuditSummaryResponse(FrontendAuditSchema):
    audit_id: int
    status: AuditStatusValue
    total_queries: int = 0
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    completion_ratio: float = 0.0
    visibility_ratio: float = 0.0
    average_score: float | None = None
    critical_query_count: int = 0
    provider_scores: dict[str, float | None] = Field(default_factory=dict)
    critical_queries: list[CriticalQueryItemResponse] = Field(default_factory=list)
    competitors: list[CompetitorSummaryItemResponse] = Field(default_factory=list)
    sources: list[SourceSummaryItemResponse] = Field(default_factory=list)
