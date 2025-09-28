from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import pytest
import pytest_asyncio
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from hex_commerce_service.app.adapters.outbound.sqlalchemy_repositories import SqlAlchemyOrderRepository, SqlAlchemyProductRepository
from hex_commerce_service.app.domain.value_objects import Money, Sku
from tests.factories.domain_builders import OrderFactory, ProductFactory

if os.getenv("GITHUB_ACTIONS") == "true":
    pytest.skip("Skip DB migration test on GitHub Actions CI", allow_module_level=True)

pytestmark = pytest.mark.asyncio

DB_URL = os.getenv("DATABASE_URL")


@pytest.fixture(scope="module")
def require_db() -> None:
    if not DB_URL:
        pytest.skip("DATABASE_URL not set; skip DB integration tests")


@pytest_asyncio.fixture()
async def session(require_db: None) -> AsyncGenerator[AsyncSession, None]:
    assert DB_URL is not None, "DATABASE_URL must be set"
    engine = create_async_engine(DB_URL)
    sm: async_sessionmaker[AsyncSession] = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with sm() as s:
        # clean DB per test (CASCADE)
        await s.execute(text("TRUNCATE TABLE order_lines, orders, inventory_items, inventory_locations, products RESTART IDENTITY CASCADE"))
        await s.commit()
        yield s
    await engine.dispose()


@asynccontextmanager
async def count_queries(session: AsyncSession) -> AsyncGenerator[dict[str, int], None]:
    """engine.sync_engineにフックして発行SQL数をカウントする。"""
    count = {"n": 0}

    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):  # type: ignore[no-untyped-def]
        count["n"] += 1

    engine = session.get_bind().engine
    event.listen(engine, "before_cursor_execute", before_cursor_execute)
    try:
        yield count
    finally:
        event.remove(engine, "before_cursor_execute", before_cursor_execute)


async def _prepare_orders(session: AsyncSession, num_orders: int, lines_per_order: int) -> None:
    prod_repo = SqlAlchemyProductRepository(session)
    pf = ProductFactory()
    # 先に十分な商品を投入
    products = [pf.build() for _ in range(lines_per_order)]
    for p in products:
        await prod_repo.add(p)
    await session.commit()

    # 注文を大量生成
    of = OrderFactory(currency="USD")
    orders = []
    for _ in range(num_orders):
        lines: list[tuple[Sku, int, Money]] = []
        for p in products:
            lines.append((p.sku, 2, p.unit_price))
        orders.append(of.build(lines))

    orp = SqlAlchemyOrderRepository(session)
    for o in orders:
        await orp.add(o)
    await session.commit()


async def test_order_list_uses_selectinload_to_avoid_n_plus_one(session: AsyncSession) -> None:
    # データ準備：50件の注文 x 3行
    await _prepare_orders(session, num_orders=50, lines_per_order=3)

    repo = SqlAlchemyOrderRepository(session)

    # repo.list() 実行時のSQL数を計測（期待：orders + order_lines の2クエリ程度）
    async with count_queries(session) as cq:
        orders = list(await repo.list())
    assert len(orders) == 50
    assert cq["n"] <= 3, f"too many queries: {cq['n']} (selectinload not applied?)"
