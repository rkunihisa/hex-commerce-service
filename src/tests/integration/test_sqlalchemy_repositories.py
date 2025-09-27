from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from hex_commerce_service.app.adapters.outbound.sqlalchemy_repositories import (
    SqlAlchemyInventoryRepository,
    SqlAlchemyOrderRepository,
    SqlAlchemyProductRepository,
)
from hex_commerce_service.app.domain.entities import Inventory, Order, OrderLine, Product
from hex_commerce_service.app.domain.value_objects import Money, OrderId, Sku

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

async def test_product_repository_crud(session: AsyncSession) -> None:
    repo = SqlAlchemyProductRepository(session)

    p1 = Product(sku=Sku("ABC-1"), name="Widget", unit_price=Money.from_major(Decimal("12.50"), "USD"))
    p2 = Product(sku=Sku("ABC-2"), name="Gadget", unit_price=Money.from_major(Decimal("7.25"), "USD"))

    await repo.add(p1)
    await repo.add(p2)
    await session.commit()

    got = await repo.get_by_sku(Sku("ABC-2"))
    assert got is not None
    assert got.name == "Gadget"
    assert str(got.unit_price) == "USD 7.25"

    lst = list(await repo.list())
    assert [p.sku.value for p in lst] == ["ABC-1", "ABC-2"]


async def test_order_repository_persist_and_load(session: AsyncSession) -> None:
    # seed products (FK)
    prod_repo = SqlAlchemyProductRepository(session)
    await prod_repo.add(Product(sku=Sku("ABC-1"), name="W", unit_price=Money.from_major(10, "USD")))
    await prod_repo.add(Product(sku=Sku("ABC-2"), name="G", unit_price=Money.from_major(5, "USD")))
    await session.commit()

    repo = SqlAlchemyOrderRepository(session)
    oid = OrderId.parse(str(OrderId.new()))
    order = Order(id=oid, currency="USD")
    order.add_line(OrderLine(sku=Sku("ABC-1"), quantity=2, unit_price=Money.from_major(10, "USD")))
    order.add_line(OrderLine(sku=Sku("ABC-2"), quantity=3, unit_price=Money.from_major(5, "USD")))

    await repo.add(order)
    await session.commit()

    loaded = await repo.get(oid)
    assert loaded is not None
    assert str(loaded.total) == "USD 35.00"
    assert [ln.quantity for ln in loaded.lines] == [2, 3]

    all_orders = list(await repo.list())
    assert len(all_orders) == 1
    assert str(all_orders[0].total) == "USD 35.00"


async def test_inventory_repository_upsert_and_get(session: AsyncSession) -> None:
    # seed products for FK
    prod_repo = SqlAlchemyProductRepository(session)
    await prod_repo.add(Product(sku=Sku("ABC-1"), name="W", unit_price=Money.from_major(1, "USD")))
    await prod_repo.add(Product(sku=Sku("ABC-2"), name="G", unit_price=Money.from_major(1, "USD")))
    await prod_repo.add(Product(sku=Sku("ABC-3"), name="H", unit_price=Money.from_major(1, "USD")))
    await session.commit()

    repo = SqlAlchemyInventoryRepository(session)

    inv = Inventory(location="tokyo")
    inv.set_on_hand(Sku("ABC-1"), 5)
    inv.set_on_hand(Sku("ABC-2"), 3)
    await repo.upsert(inv)
    await session.commit()

    got = await repo.get("tokyo")
    assert got is not None
    assert got.available(Sku("ABC-1")) == 5
    assert got.available(Sku("ABC-2")) == 3
    assert got.available(Sku("ABC-3")) == 0

    # update (replace contents)
    inv.set_on_hand(Sku("ABC-1"), 7)
    inv.set_on_hand(Sku("ABC-3"), 9)
    # remove ABC-2 by not setting it (upsert replaces)
    del inv._on_hand[Sku("ABC-2")]  # noqa: SLF001
    await repo.upsert(inv)
    await session.commit()

    got2 = await repo.get("tokyo")
    assert got2 is not None
    assert got2.available(Sku("ABC-1")) == 7
    assert got2.available(Sku("ABC-2")) == 0
    assert got2.available(Sku("ABC-3")) == 9
