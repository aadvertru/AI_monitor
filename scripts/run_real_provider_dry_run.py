from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


async def _main() -> None:
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from apps.api.database import normalize_sqlalchemy_url
    from libs.execution.dry_run import execute_real_provider_dry_run
    from libs.execution.pilot_config import PilotConfigError, PilotPolicyError

    parser = argparse.ArgumentParser(description="Run one local OpenAI provider dry-run.")
    parser.add_argument("--audit-id", type=int, required=True)
    parser.add_argument("--db-url", default=os.getenv("DATABASE_URL", "sqlite:///./ai_monitor.db"))
    args = parser.parse_args()

    engine = create_async_engine(normalize_sqlalchemy_url(args.db_url))
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_factory() as session:
            try:
                result = await execute_real_provider_dry_run(session, args.audit_id)
            except (PilotConfigError, PilotPolicyError) as exc:
                print({"status": "blocked", "error": str(exc)})
                return
            print(result.safe_log_dict())
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
