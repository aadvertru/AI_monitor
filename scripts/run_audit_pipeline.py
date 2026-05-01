from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from collections.abc import Awaitable, Callable
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from apps.api.database import normalize_sqlalchemy_url  # noqa: E402
from libs.execution.pipeline import AuditPipelineSummary, run_audit_pipeline  # noqa: E402

PipelineService = Callable[[AsyncSession, int], Awaitable[AuditPipelineSummary]]


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the full backend audit pipeline for one audit."
    )
    parser.add_argument("--audit-id", type=int, required=True)
    parser.add_argument(
        "--db-url",
        default=os.getenv("DATABASE_URL", "sqlite:///./ai_monitor.db"),
    )
    return parser


async def run_cli(
    args: argparse.Namespace,
    *,
    service: PipelineService = run_audit_pipeline,
) -> int:
    engine = create_async_engine(normalize_sqlalchemy_url(args.db_url))
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_factory() as session:
            summary = await service(session, args.audit_id)
    finally:
        await engine.dispose()

    print(json.dumps(summary.safe_log_dict(), ensure_ascii=False, sort_keys=True))
    return 1 if summary.fatal_error else 0


async def _main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    return await run_cli(args)


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
