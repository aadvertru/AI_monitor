"""Core storage models for the MVP domain."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def build_job_idempotency_key(
    audit_id: int,
    query_id: int,
    provider: str,
    run_number: int,
    audit_target_id: int | None = None,
) -> str:
    """Build a stable idempotency key for job scheduling records."""
    if audit_target_id is not None:
        return f"{audit_id}:{query_id}:target:{audit_target_id}:{provider}:{run_number}"
    return f"{audit_id}:{query_id}:{provider}:{run_number}"


class Base(DeclarativeBase):
    """Declarative base for storage models."""


class AuditStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    PARTIAL = "partial"
    COMPLETED = "completed"
    FAILED = "failed"


class RunStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class SCDLLevel(str, Enum):
    # L1 = no web access; L2 = web access.
    L1 = "L1"
    L2 = "L2"


class SeedQueryType(str, Enum):
    BRAND_DIRECT = "brand_direct"
    CATEGORY_DISCOVERY = "category_discovery"
    RECOMMENDATION = "recommendation"
    COMPARISON = "comparison"
    ALTERNATIVE = "alternative"
    PROBLEM_SOLUTION = "problem_solution"


class SeedQuerySource(str, Enum):
    USER = "user"
    AI = "ai"
    PAA = "paa"


class BrandFactType(str, Enum):
    BRAND_NAME = "brand_name"
    OFFICIAL_DOMAIN = "official_domain"
    DESCRIPTION_CLAIM = "description_claim"
    USER_PROVIDED = "user_provided"
    DOMAIN_ANALYSIS_FUTURE = "domain_analysis_future"


class BrandFactSource(str, Enum):
    BRAND_NAME = "brand_name"
    BRAND_DOMAIN = "brand_domain"
    BRAND_DESCRIPTION = "brand_description"
    USER = "user"
    SYSTEM = "system"


class AnswerEvaluationVerdict(str, Enum):
    CORRECT = "correct"
    PARTIAL = "partial"
    INCORRECT = "incorrect"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, native_enum=False), nullable=False, default=UserRole.USER
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, onupdate=_utc_now, nullable=False
    )

    audits: Mapped[list["Audit"]] = relationship(back_populates="user")
    preferences: Mapped["UserPreference | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )


class UserPreference(Base):
    __tablename__ = "user_preferences"
    __table_args__ = (
        CheckConstraint("locale IN ('en', 'ru')", name="ck_user_preferences_locale"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    locale: Mapped[str] = mapped_column(String(16), nullable=False, default="en")
    email_notifications: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    audit_completed_notifications: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    provider_error_notifications: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, onupdate=_utc_now, nullable=False
    )

    user: Mapped[User] = relationship(back_populates="preferences")


class Brand(Base):
    __tablename__ = "brands"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False
    )

    audits: Mapped[list["Audit"]] = relationship(back_populates="brand")


class Audit(Base):
    __tablename__ = "audits"
    __table_args__ = (
        CheckConstraint("runs_per_query >= 1 AND runs_per_query <= 5"),
        CheckConstraint("follow_up_depth IN (0, 1)"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    brand_id: Mapped[int] = mapped_column(
        ForeignKey("brands.id", ondelete="RESTRICT"), nullable=False
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    status: Mapped[AuditStatus] = mapped_column(
        SQLEnum(AuditStatus, native_enum=False),
        nullable=False,
        default=AuditStatus.CREATED,
    )

    providers: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    runs_per_query: Mapped[int] = mapped_column(Integer, nullable=False)
    language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    country: Mapped[str | None] = mapped_column(String(8), nullable=True)
    locale: Mapped[str | None] = mapped_column(String(16), nullable=True)
    max_queries: Mapped[int | None] = mapped_column(Integer, nullable=True)
    enable_query_expansion: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    enable_source_intelligence: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    follow_up_depth: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    scdl_level: Mapped[SCDLLevel] = mapped_column(
        SQLEnum(SCDLLevel, native_enum=False),
        nullable=False,
        default=SCDLLevel.L1,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, onupdate=_utc_now, nullable=False
    )
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped[User | None] = relationship(back_populates="audits")
    brand: Mapped[Brand] = relationship(back_populates="audits")
    queries: Mapped[list["Query"]] = relationship(
        back_populates="audit", cascade="all, delete-orphan"
    )
    jobs: Mapped[list["Job"]] = relationship(
        back_populates="audit", cascade="all, delete-orphan"
    )
    runs: Mapped[list["Run"]] = relationship(
        back_populates="audit", cascade="all, delete-orphan"
    )
    targets: Mapped[list["AuditTarget"]] = relationship(
        back_populates="audit", cascade="all, delete-orphan"
    )
    brand_facts: Mapped[list["BrandFact"]] = relationship(
        back_populates="audit", cascade="all, delete-orphan"
    )
    concepts: Mapped[list["Concept"]] = relationship(
        back_populates="audit", cascade="all, delete-orphan"
    )
    competitor_candidates: Mapped[list["CompetitorCandidate"]] = relationship(
        back_populates="audit", cascade="all, delete-orphan"
    )


class BrandFact(Base):
    __tablename__ = "brand_facts"
    __table_args__ = (
        CheckConstraint(
            "fact_type IN ('brand_name', 'official_domain', 'description_claim', "
            "'user_provided', 'domain_analysis_future')",
            name="ck_brand_facts_fact_type",
        ),
        CheckConstraint(
            "source IN ('brand_name', 'brand_domain', 'brand_description', "
            "'user', 'system')",
            name="ck_brand_facts_source",
        ),
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_brand_facts_confidence_range",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    audit_id: Mapped[int] = mapped_column(
        ForeignKey("audits.id", ondelete="CASCADE"), nullable=False
    )
    brand_id: Mapped[int | None] = mapped_column(
        ForeignKey("brands.id", ondelete="SET NULL"), nullable=True
    )
    fact_text: Mapped[str] = mapped_column(Text, nullable=False)
    fact_type: Mapped[BrandFactType] = mapped_column(
        SQLEnum(
            BrandFactType,
            values_callable=lambda enum: [item.value for item in enum],
            native_enum=False,
        ),
        nullable=False,
    )
    source: Mapped[BrandFactSource] = mapped_column(
        SQLEnum(
            BrandFactSource,
            values_callable=lambda enum: [item.value for item in enum],
            native_enum=False,
        ),
        nullable=False,
    )
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False
    )

    audit: Mapped[Audit] = relationship(back_populates="brand_facts")
    brand: Mapped[Brand | None] = relationship()


class AuditTarget(Base):
    __tablename__ = "audit_targets"
    __table_args__ = (
        CheckConstraint("level IN ('L1', 'L2')", name="ck_audit_targets_level"),
        CheckConstraint(
            "NOT (gateway_l2_experimental AND level = 'L1')",
            name="ck_audit_targets_l2_gateway_only",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    audit_id: Mapped[int] = mapped_column(
        ForeignKey("audits.id", ondelete="CASCADE"), nullable=False
    )
    ai_family: Mapped[str] = mapped_column(String(64), nullable=False)
    execution_provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model_provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model_id: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    level: Mapped[SCDLLevel] = mapped_column(
        SQLEnum(SCDLLevel, native_enum=False),
        nullable=False,
    )
    gateway: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    gateway_l2_experimental: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    provider_config_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    model_display_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    capability_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, onupdate=_utc_now, nullable=False
    )

    audit: Mapped[Audit] = relationship(back_populates="targets")


class Query(Base):
    __tablename__ = "queries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    audit_id: Mapped[int] = mapped_column(
        ForeignKey("audits.id", ondelete="CASCADE"), nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    query_type: Mapped[SeedQueryType | None] = mapped_column(
        SQLEnum(
            SeedQueryType,
            values_callable=lambda enum: [item.value for item in enum],
            native_enum=False,
        ),
        nullable=True,
    )
    source: Mapped[SeedQuerySource] = mapped_column(
        SQLEnum(
            SeedQuerySource,
            values_callable=lambda enum: [item.value for item in enum],
            native_enum=False,
        ),
        nullable=False,
        default=SeedQuerySource.USER,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False
    )

    audit: Mapped[Audit] = relationship(back_populates="queries")
    jobs: Mapped[list["Job"]] = relationship(
        back_populates="query", cascade="all, delete-orphan"
    )
    runs: Mapped[list["Run"]] = relationship(
        back_populates="query", cascade="all, delete-orphan"
    )


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        CheckConstraint("run_number >= 1"),
        UniqueConstraint("idempotency_key", name="uq_jobs_idempotency_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    audit_id: Mapped[int] = mapped_column(
        ForeignKey("audits.id", ondelete="CASCADE"), nullable=False
    )
    query_id: Mapped[int] = mapped_column(
        ForeignKey("queries.id", ondelete="CASCADE"), nullable=False
    )
    audit_target_id: Mapped[int | None] = mapped_column(
        ForeignKey("audit_targets.id", ondelete="CASCADE"), nullable=True
    )
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    run_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[JobStatus] = mapped_column(
        SQLEnum(JobStatus, native_enum=False), nullable=False, default=JobStatus.PENDING
    )
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, onupdate=_utc_now, nullable=False
    )

    audit: Mapped[Audit] = relationship(back_populates="jobs")
    query: Mapped[Query] = relationship(back_populates="jobs")
    audit_target: Mapped[AuditTarget | None] = relationship()


class Run(Base):
    __tablename__ = "runs"
    __table_args__ = (
        CheckConstraint("run_number >= 1"),
        UniqueConstraint(
            "audit_id",
            "query_id",
            "audit_target_id",
            "provider",
            "run_number",
            name="uq_runs_execution_identity",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    audit_id: Mapped[int] = mapped_column(
        ForeignKey("audits.id", ondelete="CASCADE"), nullable=False
    )
    query_id: Mapped[int] = mapped_column(
        ForeignKey("queries.id", ondelete="CASCADE"), nullable=False
    )
    audit_target_id: Mapped[int | None] = mapped_column(
        ForeignKey("audit_targets.id", ondelete="CASCADE"), nullable=True
    )
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    run_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[RunStatus] = mapped_column(
        SQLEnum(RunStatus, native_enum=False), nullable=False, default=RunStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False
    )

    audit: Mapped[Audit] = relationship(back_populates="runs")
    query: Mapped[Query] = relationship(back_populates="runs")
    audit_target: Mapped[AuditTarget | None] = relationship()
    raw_response: Mapped["RawResponse | None"] = relationship(
        back_populates="run",
        uselist=False,
        cascade="all, delete-orphan",
    )
    parsed_result: Mapped["ParsedResult | None"] = relationship(
        back_populates="run",
        uselist=False,
        cascade="all, delete-orphan",
    )
    score: Mapped["Score | None"] = relationship(
        back_populates="run",
        uselist=False,
        cascade="all, delete-orphan",
    )
    answer_evaluation: Mapped["AnswerEvaluation | None"] = relationship(
        back_populates="run",
        uselist=False,
        cascade="all, delete-orphan",
    )


class AnswerEvaluation(Base):
    __tablename__ = "answer_evaluations"
    __table_args__ = (
        CheckConstraint(
            "verdict IN ('correct', 'partial', 'incorrect', 'unknown', "
            "'not_applicable')",
            name="ck_answer_evaluations_verdict",
        ),
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_answer_evaluations_confidence_range",
        ),
        UniqueConstraint("run_id", name="uq_answer_evaluations_run_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    audit_id: Mapped[int] = mapped_column(
        ForeignKey("audits.id", ondelete="CASCADE"), nullable=False
    )
    run_id: Mapped[int] = mapped_column(
        ForeignKey("runs.id", ondelete="CASCADE"), nullable=False
    )
    query_id: Mapped[int] = mapped_column(
        ForeignKey("queries.id", ondelete="CASCADE"), nullable=False
    )
    target_id: Mapped[int | None] = mapped_column(
        ForeignKey("audit_targets.id", ondelete="CASCADE"), nullable=True
    )
    verdict: Mapped[AnswerEvaluationVerdict] = mapped_column(
        SQLEnum(
            AnswerEvaluationVerdict,
            values_callable=lambda enum: [item.value for item in enum],
            native_enum=False,
        ),
        nullable=False,
    )
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    evaluation_version: Mapped[str] = mapped_column(String(64), nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False
    )
    evaluator_provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    evaluator_model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    facts_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, onupdate=_utc_now, nullable=False
    )

    run: Mapped[Run] = relationship(back_populates="answer_evaluation")
    audit: Mapped[Audit] = relationship()
    query: Mapped[Query] = relationship()
    target: Mapped[AuditTarget | None] = relationship()


class Concept(Base):
    __tablename__ = "concepts"
    __table_args__ = (
        CheckConstraint("count >= 0", name="ck_concepts_count_non_negative"),
        CheckConstraint(
            "evidence_count >= 0", name="ck_concepts_evidence_count_non_negative"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    audit_id: Mapped[int] = mapped_column(
        ForeignKey("audits.id", ondelete="CASCADE"), nullable=False
    )
    run_id: Mapped[int | None] = mapped_column(
        ForeignKey("runs.id", ondelete="CASCADE"), nullable=True
    )
    query_id: Mapped[int | None] = mapped_column(
        ForeignKey("queries.id", ondelete="CASCADE"), nullable=True
    )
    target_id: Mapped[int | None] = mapped_column(
        ForeignKey("audit_targets.id", ondelete="CASCADE"), nullable=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    evidence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    evidence: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, onupdate=_utc_now, nullable=False
    )

    audit: Mapped[Audit] = relationship(back_populates="concepts")
    run: Mapped[Run | None] = relationship()
    query: Mapped[Query | None] = relationship()
    target: Mapped[AuditTarget | None] = relationship()


class CompetitorCandidate(Base):
    __tablename__ = "competitor_candidates"
    __table_args__ = (
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_competitor_candidates_confidence_range",
        ),
        CheckConstraint(
            "evidence_count >= 0",
            name="ck_competitor_candidates_evidence_count_non_negative",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    audit_id: Mapped[int] = mapped_column(
        ForeignKey("audits.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    evidence_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    evidence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    evidence: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, onupdate=_utc_now, nullable=False
    )

    audit: Mapped[Audit] = relationship(back_populates="competitor_candidates")


class RawResponse(Base):
    __tablename__ = "raw_responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("runs.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    request_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    raw_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    citations: Mapped[list | None] = mapped_column(JSON, nullable=True)
    provider_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    provider_status: Mapped[str] = mapped_column(String(32), nullable=False)
    response_time: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_object: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False
    )

    run: Mapped[Run] = relationship(back_populates="raw_response")


class ParsedResult(Base):
    __tablename__ = "parsed_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("runs.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    visible_brand: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    brand_position_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prominence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sentiment: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    recommendation_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    source_quality_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    competitors: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    sources: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    parsed_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False
    )

    run: Mapped[Run] = relationship(back_populates="parsed_result")


class Score(Base):
    __tablename__ = "scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("runs.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    visibility_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    prominence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sentiment_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    recommendation_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    source_quality_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    final_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False
    )

    run: Mapped[Run] = relationship(back_populates="score")
