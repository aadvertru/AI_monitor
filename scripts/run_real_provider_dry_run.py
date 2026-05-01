from __future__ import annotations

import argparse
import asyncio
import os

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.api.database import normalize_sqlalchemy_url
from libs.execution.dry_run import execute_real_provider_dry_run


async def _main() -> None:
    parser = argparse.ArgumentParser(description="Run one local OpenAI provider dry-run.")
    parser.add_argument("--audit-id", type=int, required=True)
    parser.add_argument("--db-url", default=os.getenv("DATABASE_URL", "sqlite:///./ai_monitor.db"))
    args = parser.parse_args()

    engine = create_async_engine(normalize_sqlalchemy_url(args.db_url))
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_factory() as session:
            result = await execute_real_provider_dry_run(session, args.audit_id)
            print(result.safe_log_dict())
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
