"""Frontend-facing audit API response contracts.

These schemas are intentionally separate from the SQLAlchemy models and pipeline
objects. Endpoint tasks should map stored data into these DTOs instead of
returning ORM instances directly.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# SCDL mapping: L1 = no web access; L2 = web access.
SCDLLevelValue = Literal["L1", "L2"]
AuditStatusValue = Literal[
    "created",
    "running",
    "partial",
    "completed",
    "failed",
    "cancelled",
]
SeedQueryTypeValue = Literal[
    "brand_direct",
    "category_discovery",
    "recommendation",
    "comparison",
    "alternative",
    "problem_solution",
]
SeedQuerySourceValue = Literal["user", "ai", "paa"]
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


class AuditTargetResponse(FrontendAuditSchema):
    target_id: int
    ai_family: str
    execution_provider: str
    model_provider: str
    model_id: str
    display_name: str
    level: SCDLLevelValue
    gateway: bool = False
    gateway_l2_experimental: bool = False


class BrandFactResponse(FrontendAuditSchema):
    id: int
    audit_id: int
    brand_id: int | None = None
    fact_text: str
    fact_type: Literal[
        "brand_name",
        "official_domain",
        "description_claim",
        "user_provided",
        "domain_analysis_future",
    ]
    source: Literal[
        "brand_name",
        "brand_domain",
        "brand_description",
        "user",
        "system",
    ]
    confidence: float | None = None
    created_at: datetime


EvaluationVerdictValue = Literal[
    "correct",
    "partial",
    "incorrect",
    "unknown",
    "not_applicable",
]


class AnswerEvaluationResponse(FrontendAuditSchema):
    verdict: EvaluationVerdictValue
    rationale: str | None = None
    confidence: float | None = None
    evaluation_version: str
    evaluated_at: datetime


class AnswerEvaluationVerdictCountsResponse(FrontendAuditSchema):
    correct: int = 0
    partial: int = 0
    incorrect: int = 0
    unknown: int = 0
    not_applicable: int = 0


class AnswerEvaluationRerunResponse(FrontendAuditSchema):
    audit_id: int
    evaluated_runs: int = 0
    skipped_runs: int = 0
    status: Literal["completed"] = "completed"
    warnings: list[str] = Field(default_factory=list)


class GeneratedSeedQuerySuggestionResponse(FrontendAuditSchema):
    text: str
    type: SeedQueryTypeValue
    source: Literal["ai", "paa"] = "ai"
    metadata: dict[str, Any] = Field(default_factory=dict)


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
    model_targets: list[AuditTargetResponse] = Field(default_factory=list)
    concepts: list["ConceptResponse"] = Field(default_factory=list)
    competitor_candidates: list["CompetitorCandidateResponse"] = Field(
        default_factory=list
    )
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
    model_targets: list[AuditTargetResponse] = Field(default_factory=list)
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


class AuditPipelineEnqueueResponse(FrontendAuditSchema):
    audit_id: int
    audit_number: int
    job_id: int
    status: AuditStatusValue
    background_job_status: Literal[
        "queued",
        "running",
        "completed",
        "failed",
        "cancel_requested",
        "cancelled",
    ]


class AuditProgressResponse(FrontendAuditSchema):
    audit_id: int
    status: AuditStatusValue
    total_runs: int = 0
    queued_runs: int = 0
    running_runs: int = 0
    completed_runs: int = 0
    failed_runs: int = 0
    skipped_runs: int = 0
    percent_complete: float = 0.0
    current_job_id: int | None = None
    provider_diagnostics: list["ProviderDiagnosticResponse"] = Field(default_factory=list)


class AuditCancelResponse(FrontendAuditSchema):
    audit_id: int
    status: Literal["cancel_requested"]
    audit_status: AuditStatusValue
    cancelled_jobs: int = 0
    completed_runs_preserved: int = 0
    background_job_id: int | None = None


class AuditRetryFailedResponse(FrontendAuditSchema):
    audit_id: int
    retry_run_count: int
    job_id: int
    status: AuditStatusValue
    background_job_status: Literal[
        "queued",
        "running",
        "completed",
        "failed",
        "cancel_requested",
        "cancelled",
    ]


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
    target_id: int | None = None
    target: AuditTargetResponse | None = None
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
    concepts: list["ConceptResponse"] = Field(default_factory=list)
    competitor_candidates: list["CompetitorCandidateResponse"] = Field(default_factory=list)
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


class MentionabilityMetricResponse(FrontendAuditSchema):
    percentage: float | None = None
    found: int = 0
    total: int = 0


class ToneBreakdownResponse(FrontendAuditSchema):
    positive: int = 0
    neutral: int = 0
    negative: int = 0
    unknown: int = 0


class ConceptResponse(FrontendAuditSchema):
    text: str
    type: Literal["concept"] = "concept"
    category: str | None = None
    count: int = 0
    evidence_count: int = 0


class CompetitorCandidateResponse(FrontendAuditSchema):
    name: str
    domain: str | None = None
    confidence: float | None = None
    evidence_type: str | None = None
    evidence_count: int = 0


class AuditSummaryV2TotalsResponse(FrontendAuditSchema):
    query_count: int = 0
    target_count: int = 0
    run_count: int = 0
    completed_runs: int = 0
    failed_runs: int = 0
    partial_runs: int = 0
    levels: list[SCDLLevelValue] = Field(default_factory=list)


class AuditSummaryV2OverallResponse(FrontendAuditSchema):
    mentionability_l1: MentionabilityMetricResponse = Field(
        default_factory=MentionabilityMetricResponse
    )
    mentionability_l2: MentionabilityMetricResponse = Field(
        default_factory=MentionabilityMetricResponse
    )
    accuracy_l1: float | None = None
    accuracy_l2: float | None = None
    verdict_counts: AnswerEvaluationVerdictCountsResponse = Field(
        default_factory=AnswerEvaluationVerdictCountsResponse
    )
    tone: ToneBreakdownResponse = Field(default_factory=ToneBreakdownResponse)


class AuditSummaryV2ModelSummaryResponse(FrontendAuditSchema):
    target_group_label: str
    ai_family: str | None = None
    execution_provider: str
    model_provider: str | None = None
    model_id: str
    mr_l1: float | None = None
    mr_l2: float | None = None
    delta_mr: float | None = None
    accuracy_l1: float | None = None
    accuracy_l2: float | None = None
    delta_accuracy: float | None = None
    verdict_counts: AnswerEvaluationVerdictCountsResponse = Field(
        default_factory=AnswerEvaluationVerdictCountsResponse
    )
    tone_l1: Literal["positive", "neutral", "negative", "unknown"] | None = None
    tone_l2: Literal["positive", "neutral", "negative", "unknown"] | None = None
    concepts: list[ConceptResponse] = Field(default_factory=list)
    competitor_candidates: list[CompetitorCandidateResponse] = Field(default_factory=list)


class AuditSummaryV2Response(FrontendAuditSchema):
    audit_id: int
    status: AuditStatusValue
    totals: AuditSummaryV2TotalsResponse
    overall: AuditSummaryV2OverallResponse
    model_summaries: list[AuditSummaryV2ModelSummaryResponse] = Field(default_factory=list)
    concepts: list[ConceptResponse] = Field(default_factory=list)
    competitor_candidates: list[CompetitorCandidateResponse] = Field(default_factory=list)
    provider_diagnostics: list[ProviderDiagnosticResponse] = Field(default_factory=list)


class ComparisonCandidateSummaryResponse(FrontendAuditSchema):
    mentionability_l1: float | None = None
    mentionability_l2: float | None = None
    accuracy_l1: float | None = None
    accuracy_l2: float | None = None


class ComparisonCandidateResponse(FrontendAuditSchema):
    audit_id: int
    audit_number: int
    created_at: datetime
    completed_at: datetime | None = None
    status: AuditStatusValue
    query_count: int = 0
    target_count: int = 0
    summary: ComparisonCandidateSummaryResponse = Field(
        default_factory=ComparisonCandidateSummaryResponse
    )
    warnings: list[str] = Field(default_factory=list)


class ComparisonCandidatesResponse(FrontendAuditSchema):
    audit_id: int
    candidates: list[ComparisonCandidateResponse] = Field(default_factory=list)


class MetricDeltaResponse(FrontendAuditSchema):
    current: float | int | None = None
    previous: float | int | None = None
    delta: float | int | None = None


class ModelDeltaResponse(FrontendAuditSchema):
    model_id: str
    label: str | None = None
    current_mentionability: float | None = None
    previous_mentionability: float | None = None
    mentionability_delta: float | None = None
    current_accuracy: float | None = None
    previous_accuracy: float | None = None
    accuracy_delta: float | None = None
    status: Literal["added", "removed", "persisted"] = "persisted"


class LongitudinalChangeItemResponse(FrontendAuditSchema):
    key: str
    label: str | None = None
    current_count: int | None = None
    previous_count: int | None = None
    delta: int | None = None
    status: Literal["added", "removed", "persisted", "increased", "decreased"]


class AuditComparisonResponse(FrontendAuditSchema):
    current_audit_id: int
    previous_audit_id: int
    overall_delta: dict[str, MetricDeltaResponse] = Field(default_factory=dict)
    model_deltas: list[ModelDeltaResponse] = Field(default_factory=list)
    source_domain_changes: list[LongitudinalChangeItemResponse] = Field(default_factory=list)
    concept_changes: list[LongitudinalChangeItemResponse] = Field(default_factory=list)
    competitor_changes: list[LongitudinalChangeItemResponse] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class AuditTrendPointResponse(FrontendAuditSchema):
    audit_id: int
    audit_number: int
    completed_at: datetime | None = None
    status: AuditStatusValue
    mentionability_l1: float | None = None
    mentionability_l2: float | None = None
    accuracy_l1: float | None = None
    accuracy_l2: float | None = None
    run_count: int = 0
    target_count: int = 0
    query_count: int = 0


class AuditTrendsResponse(FrontendAuditSchema):
    brand_id: int
    points: list[AuditTrendPointResponse] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


AnswerMatrixCellStatusValue = Literal[
    "completed",
    "failed",
    "partial",
    "not_run",
    "processing",
    "missing",
]


class AnswerMatrixColumnResponse(FrontendAuditSchema):
    target_id: str
    label: str
    ai_family: str | None = None
    execution_provider: str
    model_provider: str | None = None
    model_id: str
    level: SCDLLevelValue
    gateway: bool = False
    gateway_l2_experimental: bool = False


class AnswerMatrixCellResponse(FrontendAuditSchema):
    target_id: str
    run_id: int | None = None
    status: AnswerMatrixCellStatusValue
    answer_excerpt: str | None = None
    brand_mentioned: bool | None = None
    score: float | None = None
    evaluation: AnswerEvaluationResponse | None = None
    sources_count: int = 0
    provider_error: ProviderDiagnosticResponse | None = None
    concepts: list[ConceptResponse] = Field(default_factory=list)
    competitor_candidates: list[CompetitorCandidateResponse] = Field(default_factory=list)


class AnswerMatrixRowResponse(FrontendAuditSchema):
    query_id: str
    query_text: str
    query_type: SeedQueryTypeValue | Literal["unknown"] | None = None
    cells: list[AnswerMatrixCellResponse] = Field(default_factory=list)


class AnswerMatrixResponse(FrontendAuditSchema):
    audit_id: int
    columns: list[AnswerMatrixColumnResponse] = Field(default_factory=list)
    rows: list[AnswerMatrixRowResponse] = Field(default_factory=list)
    provider_diagnostics: list[ProviderDiagnosticResponse] = Field(default_factory=list)


class SourceDomainUrlResponse(FrontendAuditSchema):
    url: str
    normalized_url: str
    title: str | None = None
    snippet: str | None = None
    query_id: str | None = None
    query_text: str | None = None
    target_id: str | None = None
    model_id: str | None = None
    model_provider: str | None = None
    execution_provider: str | None = None
    level: SCDLLevelValue | None = None
    source_type: str | None = None
    gateway: bool = False
    gateway_l2_experimental: bool = False


class SourceDomainGroupResponse(FrontendAuditSchema):
    domain: str
    source_count: int = 0
    unique_url_count: int = 0
    query_count: int = 0
    target_count: int = 0
    levels: list[SCDLLevelValue] = Field(default_factory=list)
    models: list[str] = Field(default_factory=list)
    providers: list[str] = Field(default_factory=list)
    urls: list[SourceDomainUrlResponse] = Field(default_factory=list)


class SourceDomainsResponse(FrontendAuditSchema):
    audit_id: int
    domains: list[SourceDomainGroupResponse] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


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
