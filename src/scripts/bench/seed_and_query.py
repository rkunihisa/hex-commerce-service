from __future__ import annotations

import asyncio
import os
import time

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from hex_commerce_service.app.adapters.outbound.sqlalchemy_repositories import (
    SqlAlchemyOrderRepository,
    SqlAlchemyProductRepository,
)
from tests.factories.domain_builders import OrderFactory, ProductFactory

DB_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://app:app@localhost:5432/appdb")


async def main() -> None:
    engine = create_async_engine(DB_URL)
    sm: async_sessionmaker[AsyncSession] = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with sm() as session:
        # seed
        pf = ProductFactory()
        pr = SqlAlchemyProductRepository(session)
        products = [pf.build() for _ in range(5)]
        for p in products:
            await pr.add(p)
        await session.commit()

        of = OrderFactory()
        orp = SqlAlchemyOrderRepository(session)
        for _ in range(200):
            lines = [(p.sku, 2, p.unit_price) for p in products]
            await orp.add(of.build(lines))
        await session.commit()

        # query benchmark
        t0 = time.perf_counter()
        orders = list(await orp.list())
        t1 = time.perf_counter()
        print(f"Loaded {len(orders)} orders with selectinload in {(t1 - t0) * 1000:.1f} ms")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
