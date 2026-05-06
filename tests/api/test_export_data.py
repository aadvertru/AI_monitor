from __future__ import annotations

import unittest
from datetime import datetime, timezone
from io import BytesIO
from unittest.mock import patch
from zipfile import ZipFile

from fastapi import HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.api.export_data import build_export_report_data
from apps.api.export_docx import generate_docx_export
from apps.api.export_excel import generate_excel_export
from apps.api.main import download_audit_docx_export, download_audit_excel_export
from apps.api.security import create_access_token, load_auth_config
from libs.storage.models import (
    AnswerEvaluation,
    AnswerEvaluationVerdict,
    Audit,
    AuditStatus,
    AuditTarget,
    Base,
    Brand,
    CompetitorCandidate,
    Concept,
    ParsedResult,
    Query,
    RawResponse,
    Run,
    RunStatus,
    SCDLLevel,
    Score,
    SeedQueryType,
    User,
    UserRole,
)

NOW = datetime(2026, 5, 6, 10, 0, tzinfo=timezone.utc)
AUTH_ENV = {"JWT_SECRET": "test-secret-value"}


class ExportDataBuilderTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.auth_env = patch.dict("os.environ", AUTH_ENV, clear=True)
        self.auth_env.start()
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def asyncTearDown(self) -> None:
        await self.engine.dispose()
        self.auth_env.stop()

    def _request(self, user: User) -> Request:
        return self._request_for_user_id(user.id, user.role.value)

    def _request_for_user_id(self, user_id: int, role: str = "user") -> Request:
        config = load_auth_config(env=AUTH_ENV)
        token = create_access_token(user_id=user_id, role=role, config=config)
        return Request(
            {
                "type": "http",
                "headers": [(b"cookie", f"{config.cookie.name}={token}".encode("ascii"))],
            }
        )

    def _anonymous_request(self) -> Request:
        return Request({"type": "http", "headers": []})

    async def _create_user(self, email: str) -> User:
        async with self.session_factory() as session:
            user = User(email=email, hashed_password="hashed", role=UserRole.USER)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    async def _create_audit(
        self,
        *,
        status: AuditStatus = AuditStatus.COMPLETED,
        include_run: bool = True,
        include_sources: bool = True,
        include_evaluation: bool = True,
    ) -> Audit:
        async with self.session_factory() as session:
            user = User(
                email=f"export-{status.value}@example.com",
                hashed_password="hashed",
                role=UserRole.USER,
            )
            brand = Brand(name=f"Export {status.value}", domain="export.example")
            audit = Audit(
                brand=brand,
                user=user,
                status=status,
                providers=["openrouter"],
                runs_per_query=1,
                language="en",
                country="US",
                locale="en-US",
                scdl_level=SCDLLevel.L2,
                enable_source_intelligence=True,
                created_at=NOW,
                updated_at=NOW,
            )
            session.add(audit)
            await session.flush()
            target = AuditTarget(
                audit_id=audit.id,
                ai_family="gemini",
                execution_provider="openrouter",
                model_provider="google",
                model_id="google/gemini-2.0-flash-001",
                display_name="Gemini 2.0 Flash",
                level=SCDLLevel.L2,
                gateway=True,
                gateway_l2_experimental=True,
            )
            query = Query(
                audit_id=audit.id,
                text="best export tools",
                query_type=SeedQueryType.CATEGORY_DISCOVERY,
            )
            session.add_all([target, query])
            await session.flush()
            if include_run:
                run = Run(
                    audit_id=audit.id,
                    query_id=query.id,
                    audit_target_id=target.id,
                    provider="openrouter",
                    run_number=1,
                    status=RunStatus.SUCCESS,
                )
                session.add(run)
                await session.flush()
                parsed_sources = (
                    [{"url": "https://docs.example.com/export", "title": "Docs"}]
                    if include_sources
                    else []
                )
                session.add_all(
                    [
                        ParsedResult(
                            run_id=run.id,
                            visible_brand=True,
                            brand_position_rank=1,
                            prominence_score=0.7,
                            sentiment=0.2,
                            recommendation_score=0.6,
                            source_quality_score=0.5,
                            competitors=[{"name": "Export Rival"}],
                            sources=parsed_sources,
                            parsed_payload={"raw_prompt": "hidden"},
                        ),
                        Score(
                            run_id=run.id,
                            visibility_score=0.8,
                            prominence_score=0.7,
                            sentiment_score=0.2,
                            recommendation_score=0.6,
                            source_quality_score=0.5,
                            final_score=0.76,
                        ),
                        RawResponse(
                            run_id=run.id,
                            request_snapshot={"headers": {"authorization": "sk-hidden"}},
                            raw_answer="safe answer excerpt should be truncated from DTOs",
                            citations=parsed_sources,
                            provider_metadata={"api_key": "sk-hidden"},
                            provider_status="success",
                        ),
                    ]
                )
                if include_evaluation:
                    session.add(
                        AnswerEvaluation(
                            audit_id=audit.id,
                            run_id=run.id,
                            query_id=query.id,
                            target_id=target.id,
                            verdict=AnswerEvaluationVerdict.CORRECT,
                            rationale="The answer matches known facts.",
                            confidence=0.9,
                            evaluation_version="eval-v1",
                        )
                    )
                session.add_all(
                    [
                        Concept(
                            audit_id=audit.id,
                            text="Export Rival",
                            category="competitor",
                            count=1,
                            evidence={"run_ids": [run.id]},
                        ),
                        CompetitorCandidate(
                            audit_id=audit.id,
                            name="Export Rival",
                            domain="rival.example",
                            confidence=0.9,
                            evidence_type="known",
                            evidence_count=1,
                            evidence=[{"run_id": run.id}],
                        ),
                    ]
                )
            await session.commit()
            await session.refresh(audit)
            return audit

    async def test_builds_report_data_for_completed_audit_from_ui_dtos(self) -> None:
        audit = await self._create_audit()

        async with self.session_factory() as session:
            data = await build_export_report_data(session, audit, generated_at=NOW)

        self.assertEqual(data.audit_id, audit.id)
        self.assertEqual(data.audit_metadata.brand_domain, "export.example")
        self.assertEqual(data.summary.audit_id, audit.id)
        self.assertEqual(len(data.answer_matrix.columns), 1)
        self.assertEqual(len(data.source_domains.domains), 1)
        self.assertEqual(data.seed_queries[0].query_type, "category_discovery")

    async def test_builds_report_data_for_partial_and_missing_optional_sections(
        self,
    ) -> None:
        audit = await self._create_audit(
            status=AuditStatus.PARTIAL,
            include_sources=False,
            include_evaluation=False,
        )

        async with self.session_factory() as session:
            data = await build_export_report_data(session, audit)

        self.assertEqual(data.audit_metadata.status, "partial")
        self.assertEqual(data.source_domains.domains, [])
        self.assertIsNone(data.summary.overall.accuracy_l2)
        self.assertEqual(data.answer_matrix.rows[0].cells[0].evaluation, None)

    async def test_legacy_no_run_audit_is_safe(self) -> None:
        audit = await self._create_audit(include_run=False)

        async with self.session_factory() as session:
            data = await build_export_report_data(session, audit)

        self.assertEqual(data.summary.totals.run_count, 0)
        self.assertEqual(data.source_domains.domains, [])
        self.assertEqual(data.answer_matrix.rows[0].cells[0].status, "not_run")

    async def test_report_data_does_not_include_raw_payloads_or_secrets(self) -> None:
        audit = await self._create_audit()

        async with self.session_factory() as session:
            data = await build_export_report_data(session, audit)

        serialized = str(data.model_dump(mode="json"))
        for forbidden in [
            "raw_prompt",
            "request_snapshot",
            "headers",
            "authorization",
            "api_key",
            "sk-hidden",
        ]:
            self.assertNotIn(forbidden, serialized)

    async def test_export_regression_fixture_covers_analysis_and_diagnostics(
        self,
    ) -> None:
        audit = await self._create_audit()

        async with self.session_factory() as session:
            query = (
                await session.execute(
                    select(Query).where(Query.audit_id == audit.id).order_by(Query.id)
                )
            ).scalars().first()
            target = (
                await session.execute(
                    select(AuditTarget)
                    .where(AuditTarget.audit_id == audit.id)
                    .order_by(AuditTarget.id)
                )
            ).scalars().first()
            assert query is not None
            assert target is not None
            second_target = AuditTarget(
                audit_id=audit.id,
                ai_family="claude",
                execution_provider="openrouter",
                model_provider="anthropic",
                model_id="anthropic/claude-3.5-sonnet",
                display_name="Claude 3.5 Sonnet",
                level=SCDLLevel.L1,
                gateway=True,
                gateway_l2_experimental=False,
            )
            error_run = Run(
                audit_id=audit.id,
                query_id=query.id,
                audit_target_id=target.id,
                provider="openrouter",
                run_number=2,
                status=RunStatus.RATE_LIMITED,
            )
            session.add_all([second_target, error_run])
            await session.flush()
            session.add(
                RawResponse(
                    run_id=error_run.id,
                    request_snapshot={"headers": {"authorization": "sk-hidden"}},
                    raw_answer=None,
                    citations=[],
                    provider_metadata={"model": target.model_id, "api_key": "sk-hidden"},
                    provider_status="rate_limited",
                    error_object={"code": "RATE_LIMIT", "message": "sk-hidden raw message"},
                )
            )
            await session.commit()

        async with self.session_factory() as session:
            data = await build_export_report_data(session, audit, generated_at=NOW)

        self.assertGreaterEqual(len(data.answer_matrix.columns), 2)
        self.assertEqual(data.concepts[0].text, "Export Rival")
        self.assertEqual(data.competitor_candidates[0].name, "Export Rival")
        self.assertEqual(data.provider_diagnostics[0].code, "RATE_LIMIT")

        exported_text = _all_zip_text(generate_excel_export(data)) + _all_zip_text(
            generate_docx_export(data)
        )
        self.assertIn("Claude 3.5 Sonnet", exported_text)
        self.assertIn("Export Rival", exported_text)
        self.assertIn("OpenRouter rate limit exceeded.", exported_text)
        self.assertNotIn("sk-hidden", exported_text)

    async def test_excel_export_generates_valid_workbook_with_required_sheets(
        self,
    ) -> None:
        audit = await self._create_audit()

        async with self.session_factory() as session:
            data = await build_export_report_data(session, audit, generated_at=NOW)

        content = generate_excel_export(data)
        workbook_text = _zip_text(content, "xl/workbook.xml")
        all_text = _all_zip_text(content)

        for sheet_name in [
            "Audit Summary",
            "Model Summary",
            "Answer Matrix",
            "Source Domains",
            "Concepts Competitors",
            "Diagnostics",
        ]:
            self.assertIn(sheet_name, workbook_text)
        self.assertIn("best export tools", all_text)
        self.assertIn("google/gemini-2.0-flash-001", all_text)
        self.assertIn("docs.example.com", all_text)
        self.assert_no_unsafe_export_text(all_text)

    async def test_excel_export_handles_partial_no_sources_and_no_evaluation(
        self,
    ) -> None:
        audit = await self._create_audit(
            status=AuditStatus.PARTIAL,
            include_sources=False,
            include_evaluation=False,
        )

        async with self.session_factory() as session:
            data = await build_export_report_data(session, audit)

        all_text = _all_zip_text(generate_excel_export(data))
        self.assertIn("partial", all_text)
        self.assertIn("Answer Matrix", _zip_text(generate_excel_export(data), "xl/workbook.xml"))
        self.assert_no_unsafe_export_text(all_text)

    async def test_docx_export_generates_valid_document_with_required_sections(
        self,
    ) -> None:
        audit = await self._create_audit()

        async with self.session_factory() as session:
            data = await build_export_report_data(session, audit, generated_at=NOW)

        content = generate_docx_export(data)
        document_text = _zip_text(content, "word/document.xml")

        for heading in [
            "Audit report:",
            "Audit metadata",
            "General summary",
            "Model summary",
            "Answer matrix summary",
            "Source domains",
            "Concepts",
            "Competitor candidates",
            "Provider diagnostics",
            "Methodology notes",
        ]:
            self.assertIn(heading, document_text)
        self.assertIn("best export tools", document_text)
        self.assertIn("Gemini 2.0 Flash", document_text)
        self.assert_no_unsafe_export_text(document_text)

    async def test_docx_export_handles_legacy_no_data_audit(self) -> None:
        audit = await self._create_audit(include_run=False)

        async with self.session_factory() as session:
            data = await build_export_report_data(session, audit)

        document_text = _zip_text(generate_docx_export(data), "word/document.xml")
        self.assertIn("No source domains available.", document_text)
        self.assertIn("No provider diagnostics.", document_text)
        self.assert_no_unsafe_export_text(document_text)

    async def test_export_download_endpoints_require_auth_and_ownership(self) -> None:
        audit = await self._create_audit()
        assert audit.user_id is not None
        other = await self._create_user("other-export@example.com")

        async with self.session_factory() as session:
            with self.assertRaises(HTTPException) as unauth_context:
                await download_audit_excel_export(
                    audit_id=audit.id,
                    request=self._anonymous_request(),
                    session=session,
                )
            with self.assertRaises(HTTPException) as other_context:
                await download_audit_docx_export(
                    audit_id=audit.id,
                    request=self._request(other),
                    session=session,
                )

        self.assertEqual(unauth_context.exception.status_code, 401)
        self.assertEqual(other_context.exception.status_code, 404)

    async def test_owner_can_download_excel_and_docx_with_safe_headers(self) -> None:
        audit = await self._create_audit()
        assert audit.user_id is not None

        async with self.session_factory() as session:
            excel_response = await download_audit_excel_export(
                audit_id=audit.id,
                request=self._request_for_user_id(audit.user_id),
                session=session,
            )
            docx_response = await download_audit_docx_export(
                audit_id=audit.id,
                request=self._request_for_user_id(audit.user_id),
                session=session,
            )

        self.assertEqual(
            excel_response.media_type,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertEqual(
            docx_response.media_type,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        self.assertRegex(
            excel_response.headers["content-disposition"],
            rf'audit-{audit.id}-summary-\d{{8}}-\d{{6}}\.xlsx',
        )
        self.assertRegex(
            docx_response.headers["content-disposition"],
            rf'audit-{audit.id}-report-\d{{8}}-\d{{6}}\.docx',
        )
        self.assertIn("Audit Summary", _zip_text(excel_response.body, "xl/workbook.xml"))
        self.assertIn("Audit report:", _zip_text(docx_response.body, "word/document.xml"))
        self.assert_no_unsafe_export_text(_all_zip_text(excel_response.body))
        self.assert_no_unsafe_export_text(_all_zip_text(docx_response.body))

    def assert_no_unsafe_export_text(self, text: str) -> None:
        for forbidden in [
            "raw_prompt",
            "request_snapshot",
            "headers",
            "authorization",
            "api_key",
            "sk-hidden",
        ]:
            self.assertNotIn(forbidden, text)


def _zip_text(content: bytes, member: str) -> str:
    with ZipFile(BytesIO(content)) as archive:
        return archive.read(member).decode("utf-8")


def _all_zip_text(content: bytes) -> str:
    with ZipFile(BytesIO(content)) as archive:
        return "\n".join(
            archive.read(name).decode("utf-8", errors="ignore")
            for name in archive.namelist()
            if name.endswith(".xml")
        )


if __name__ == "__main__":
    unittest.main()
