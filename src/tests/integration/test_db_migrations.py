from __future__ import annotations

import os
import asyncio

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

if os.getenv("GITHUB_ACTIONS") == "true":
    pytest.skip("Skip DB migration test on GitHub Actions CI", allow_module_level=True)

REQUIRED_TABLES = {
    "products",
    "orders",
    "order_lines",
    "inventory_locations",
    "inventory_items",
}


@pytest.mark.skipif(
    not os.getenv("DATABASE_URL"),
    reason="DATABASE_URL not set; skip DB integration test",
)
def test_tables_exist_after_migration() -> None:
    asyncio.run(_run())


async def _run() -> None:
    engine = create_async_engine(os.environ["DATABASE_URL"])
    async with engine.begin() as conn:
        # smoke
        one = await conn.scalar(text("select 1"))
        assert one == 1

        rows = await conn.execute(
            text(
                "select tablename from pg_tables where schemaname = 'public' "
                "and tablename = any(:names)"
            ),
            dict(names=list(REQUIRED_TABLES)),
        )
        found = {r[0] for r in rows}
        assert REQUIRED_TABLES.issubset(found)
    await engine.dispose()
