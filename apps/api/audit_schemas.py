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
SeedQueryTypeValue = Literal[
    "brand_direct",
    "category_discovery",
    "recommendation",
    "comparison",
    "alternative",
    "problem_solution",
]
SeedQuerySourceValue = Literal["user", "ai"]
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
    audit_number: int
    brand_name: str
    brand_domain: str | None = None
    status: AuditStatusValue
    scdl_level: SCDLLevelValue = "L1"
    providers: list[str] = Field(default_factory=list)
    runs_per_query: int
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None = None


class SeedQueryItemResponse(FrontendAuditSchema):
    text: str
    type: SeedQueryTypeValue | None = None
    source: SeedQuerySourceValue = "user"


class GeneratedSeedQuerySuggestionResponse(FrontendAuditSchema):
    text: str
    type: SeedQueryTypeValue
    source: Literal["ai"] = "ai"


class GenerateSeedQuerySuggestionsResponse(FrontendAuditSchema):
    suggestions: list[GeneratedSeedQuerySuggestionResponse] = Field(default_factory=list)
    skipped_duplicates: int = 0
    skipped_limit: int = 0
    warnings: list[str] = Field(default_factory=list)


class AuditDetailResponse(FrontendAuditSchema):
    audit_id: int
    audit_number: int
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
    seed_query_items: list[SeedQueryItemResponse] = Field(default_factory=list)
    enable_query_expansion: bool = False
    enable_source_intelligence: bool = False
    follow_up_depth: int = 0
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None = None


class AuditStatusResponse(FrontendAuditSchema):
    audit_id: int
    audit_number: int
    status: AuditStatusValue
    scdl_level: SCDLLevelValue = "L1"
    total_runs: int = 0
    completed_runs: int = 0
    failed_runs: int = 0
    completion_ratio: float = 0.0
    updated_at: datetime | None = None
    provider_diagnostics: list["ProviderDiagnosticResponse"] = Field(default_factory=list)


class AuditRunTriggerResponse(FrontendAuditSchema):
    audit_id: int
    audit_number: int
    status: AuditStatusValue
    scheduled_jobs: int = 0
    total_jobs: int = 0


class AuditPipelineSchedulingResponse(FrontendAuditSchema):
    audit_id: int
    scheduled_jobs: int = 0
    total_jobs: int = 0
    fatal_error: str | None = None


class AuditPipelineExecutionErrorResponse(FrontendAuditSchema):
    job_id: int
    code: str
    message: str


class AuditPipelineExecutionResponse(FrontendAuditSchema):
    audit_id: int
    total_jobs_inspected: int = 0
    jobs_executed: int = 0
    jobs_skipped: int = 0
    success_count: int = 0
    error_count: int = 0
    timeout_count: int = 0
    rate_limited_count: int = 0
    errors: list[AuditPipelineExecutionErrorResponse] = Field(default_factory=list)
    fatal_error: str | None = None


class AuditPipelinePostProcessingErrorResponse(FrontendAuditSchema):
    run_id: int
    code: str
    message: str


class AuditPipelinePostProcessingResponse(FrontendAuditSchema):
    audit_id: int
    total_runs_inspected: int = 0
    runs_processed: int = 0
    skipped_already_processed: int = 0
    skipped_missing_raw_response: int = 0
    skipped_non_successful_run: int = 0
    audit_status: AuditStatusValue | None = None
    errors: list[AuditPipelinePostProcessingErrorResponse] = Field(default_factory=list)
    fatal_error: str | None = None


class AuditPipelineRunResponse(FrontendAuditSchema):
    audit_id: int
    scheduling: AuditPipelineSchedulingResponse
    execution: AuditPipelineExecutionResponse | None = None
    post_processing: AuditPipelinePostProcessingResponse | None = None
    final_audit_status: AuditStatusValue | None = None
    fatal_error: str | None = None
    provider_diagnostics: list["ProviderDiagnosticResponse"] = Field(default_factory=list)


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


class ProviderDiagnosticResponse(FrontendAuditSchema):
    code: str
    message: str
    provider: str
    model: str | None = None
    level: SCDLLevelValue | None = None
    retryable: bool = False
    run_id: int | None = None
    query_id: int | None = None


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
    provider_error: ProviderDiagnosticResponse | None = None


class AuditResultsResponse(FrontendAuditSchema):
    audit_id: int
    audit_number: int
    rows: list[AuditResultRowResponse] = Field(default_factory=list)
    total: int = 0
    provider_diagnostics: list[ProviderDiagnosticResponse] = Field(default_factory=list)


class CompetitorSummaryItemResponse(FrontendAuditSchema):
    name: str
    mention_count: int | None = None
    visibility_ratio: float | None = None
    average_score: float | None = None


class CriticalQueryItemResponse(FrontendAuditSchema):
    query: str
    reason: str
    query_score: float | None = None


class QueryTypeCoverageItemResponse(FrontendAuditSchema):
    type: SeedQueryTypeValue | Literal["unknown"]
    total_queries: int = 0
    processed_runs: int = 0
    failed_runs: int = 0
    brand_found_count: int = 0
    brand_found_rate: float = 0.0
    average_score: float | None = None


class AuditSummaryResponse(FrontendAuditSchema):
    audit_id: int
    audit_number: int
    status: AuditStatusValue
    total_queries: int = 0
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    completion_ratio: float = 0.0
    visibility_ratio: float = 0.0
    average_score: float | None = None
    weighted_visibility_score: float | None = None
    critical_query_count: int = 0
    provider_scores: dict[str, float | None] = Field(default_factory=dict)
    critical_queries: list[CriticalQueryItemResponse] = Field(default_factory=list)
    query_type_coverage: list[QueryTypeCoverageItemResponse] = Field(default_factory=list)
    competitors: list[CompetitorSummaryItemResponse] = Field(default_factory=list)
    sources: list[SourceSummaryItemResponse] = Field(default_factory=list)
    provider_diagnostics: list[ProviderDiagnosticResponse] = Field(default_factory=list)


class RawResponseInspectionResponse(FrontendAuditSchema):
    audit_id: int
    query: str
    provider: str
    scdl_level: SCDLLevelValue = "L1"
    run_id: int
    run_number: int
    run_status: RunStatusValue
    raw_answer: str | None = None
    citations: list[dict] | None = None
    provider_metadata: dict | None = None
    error_object: dict | None = None
    response_time: float | None = None
    created_at: datetime
