from __future__ import annotations

import io
import json
import subprocess
import sys
import unittest
from argparse import Namespace
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from sqlalchemy.ext.asyncio import AsyncSession

from libs.execution.pipeline import AuditPipelineSummary, AuditSchedulingSummary
from scripts.run_audit_pipeline import build_arg_parser, run_cli

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_audit_pipeline.py"


class RunAuditPipelineCliTests(unittest.IsolatedAsyncioTestCase):
    def test_valid_audit_id_argument_is_parsed(self) -> None:
        args = build_arg_parser().parse_args(["--audit-id", "8"])

        self.assertEqual(args.audit_id, 8)
        self.assertEqual(args.db_url, "sqlite:///./ai_monitor.db")

    def test_invalid_audit_id_argument_exits_non_zero(self) -> None:
        with self.assertRaises(SystemExit) as context:
            build_arg_parser().parse_args(["--audit-id", "not-an-int"])

        self.assertEqual(context.exception.code, 2)

    def test_missing_audit_id_argument_exits_non_zero(self) -> None:
        with self.assertRaises(SystemExit) as context:
            build_arg_parser().parse_args([])

        self.assertEqual(context.exception.code, 2)

    def test_script_import_path_works_from_repository_root(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--help"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("--audit-id", result.stdout)

    async def test_cli_calls_pipeline_service_and_prints_success_summary(self) -> None:
        calls: list[int] = []

        async def fake_service(
            _session: AsyncSession,
            audit_id: int,
        ) -> AuditPipelineSummary:
            calls.append(audit_id)
            return AuditPipelineSummary(
                audit_id=audit_id,
                scheduling=AuditSchedulingSummary(
                    audit_id=audit_id,
                    scheduled_jobs=1,
                    total_jobs=1,
                ),
                final_audit_status="completed",
            )

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = await run_cli(
                Namespace(audit_id=8, db_url="sqlite:///:memory:"),
                service=fake_service,
            )

        payload = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(calls, [8])
        self.assertEqual(payload["audit_id"], 8)
        self.assertEqual(payload["final_audit_status"], "completed")
        self.assertEqual(payload["scheduling"]["scheduled_jobs"], 1)

    async def test_cli_returns_non_zero_for_service_fatal_error(self) -> None:
        async def fake_service(
            _session: AsyncSession,
            audit_id: int,
        ) -> AuditPipelineSummary:
            return AuditPipelineSummary(
                audit_id=audit_id,
                scheduling=AuditSchedulingSummary(audit_id=audit_id),
                final_audit_status="failed",
                fatal_error="Audit with id=404 was not found.",
            )

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = await run_cli(
                Namespace(audit_id=404, db_url="sqlite:///:memory:"),
                service=fake_service,
            )

        payload = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 1)
        self.assertIn("was not found", payload["fatal_error"])

    async def test_cli_output_does_not_include_raw_answers_prompts_or_secrets(self) -> None:
        async def fake_service(
            _session: AsyncSession,
            audit_id: int,
        ) -> AuditPipelineSummary:
            return AuditPipelineSummary(
                audit_id=audit_id,
                scheduling=AuditSchedulingSummary(audit_id=audit_id),
                final_audit_status="completed",
            )

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            await run_cli(
                Namespace(audit_id=8, db_url="sqlite:///:memory:"),
                service=fake_service,
            )

        output = stdout.getvalue()
        self.assertNotIn("raw_answer", output)
        self.assertNotIn("prompt", output.lower())
        self.assertNotIn("sk-", output)
        self.assertNotIn("secret", output.lower())
        self.assertNotIn("cookie", output.lower())

    async def test_cli_does_not_call_openai_provider_when_service_is_mocked(self) -> None:
        async def fake_service(
            _session: AsyncSession,
            audit_id: int,
        ) -> AuditPipelineSummary:
            return AuditPipelineSummary(
                audit_id=audit_id,
                scheduling=AuditSchedulingSummary(audit_id=audit_id),
            )

        with patch(
            "libs.execution.openai_provider.OpenAIProviderAdapter.query",
            side_effect=AssertionError("provider should not be called"),
        ) as provider_mock:
            await run_cli(
                Namespace(audit_id=8, db_url="sqlite:///:memory:"),
                service=fake_service,
            )

        provider_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
