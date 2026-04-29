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
    audit_id: int, query_id: int, provider: str, run_number: int
) -> str:
    """Build a stable idempotency key for job scheduling records."""
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


class Query(Base):
    __tablename__ = "queries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    audit_id: Mapped[int] = mapped_column(
        ForeignKey("audits.id", ondelete="CASCADE"), nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
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


class Run(Base):
    __tablename__ = "runs"
    __table_args__ = (
        CheckConstraint("run_number >= 1"),
        UniqueConstraint(
            "audit_id",
            "query_id",
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
