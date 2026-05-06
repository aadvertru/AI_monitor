"""Shared export data builder for audit reports."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.audit_schemas import (
    AnswerMatrixResponse,
    AuditSummaryV2Response,
    SourceDomainsResponse,
)
from libs.storage.models import Audit, Brand, Query


class ExportAuditMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    audit_id: int
    brand_name: str
    brand_domain: str | None = None
    status: str
    language: str | None = None
    country: str | None = None
    locale: str | None = None
    providers: list[str] = Field(default_factory=list)
    runs_per_query: int
    scdl_level: str
    max_queries: int | None = None
    enable_query_expansion: bool = False
    enable_source_intelligence: bool = False
    created_at: datetime
    updated_at: datetime


class ExportSeedQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    text: str
    query_type: str | None = None
    source: str = "user"


class ExportReportData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    audit_id: int
    generated_at: datetime
    audit_metadata: ExportAuditMetadata
    seed_queries: list[ExportSeedQuery] = Field(default_factory=list)
    summary: AuditSummaryV2Response
    answer_matrix: AnswerMatrixResponse
    source_domains: SourceDomainsResponse

    @property
    def provider_diagnostics(self):
        return self.summary.provider_diagnostics or self.answer_matrix.provider_diagnostics

    @property
    def concepts(self):
        return self.summary.concepts

    @property
    def competitor_candidates(self):
        return self.summary.competitor_candidates


async def build_export_report_data(
    session: AsyncSession,
    audit: Audit,
    *,
    generated_at: datetime | None = None,
) -> ExportReportData:
    """Build report data from existing UI DTO builders only."""
    # Lazy import avoids making apps.api.main import itself when export endpoints load.
    from apps.api.main import (  # noqa: PLC0415
        _scdl_level_value,
        _status_value,
        build_answer_matrix_response,
        build_audit_summary_v2_response,
        build_source_domains_response,
    )

    brand = (
        await session.execute(select(Brand).where(Brand.id == audit.brand_id))
    ).scalar_one()
    query_rows = (
        await session.execute(
            select(Query).where(Query.audit_id == audit.id).order_by(Query.id)
        )
    ).scalars().all()

    summary = await build_audit_summary_v2_response(session, audit)
    answer_matrix = await build_answer_matrix_response(session, audit)
    source_domains = await build_source_domains_response(session, audit)

    return ExportReportData(
        audit_id=audit.id,
        generated_at=generated_at or datetime.now(tz=timezone.utc),
        audit_metadata=ExportAuditMetadata(
            audit_id=audit.id,
            brand_name=brand.name,
            brand_domain=brand.domain,
            status=_status_value(audit.status),
            language=audit.language,
            country=audit.country,
            locale=audit.locale,
            providers=list(audit.providers or []),
            runs_per_query=audit.runs_per_query,
            scdl_level=_scdl_level_value(audit.scdl_level),
            max_queries=audit.max_queries,
            enable_query_expansion=audit.enable_query_expansion,
            enable_source_intelligence=audit.enable_source_intelligence,
            created_at=audit.created_at,
            updated_at=audit.updated_at,
        ),
        seed_queries=[
            ExportSeedQuery(
                id=query.id,
                text=query.text,
                query_type=query.query_type.value if query.query_type else None,
                source=query.source.value if query.source else "user",
            )
            for query in query_rows
        ],
        summary=summary,
        answer_matrix=answer_matrix,
        source_domains=source_domains,
    )
