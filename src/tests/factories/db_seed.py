from __future__ import annotations

from typing import Iterable

from sqlalchemy.ext.asyncio import AsyncSession

from hex_commerce_service.app.adapters.outbound.sqlalchemy_repositories import (
    SqlAlchemyInventoryRepository,
    SqlAlchemyOrderRepository,
    SqlAlchemyProductRepository,
)
from hex_commerce_service.app.domain.entities import Inventory, Order, Product


async def seed_products(session: AsyncSession, products: Iterable[Product]) -> None:
    repo = SqlAlchemyProductRepository(session)
    for p in products:
        await repo.add(p)
    await session.commit()


async def seed_orders(session: AsyncSession, orders: Iterable[Order]) -> None:
    repo = SqlAlchemyOrderRepository(session)
    for o in orders:
        await repo.add(o)
    await session.commit()


async def seed_inventory(session: AsyncSession, inventory: Inventory) -> None:
    repo = SqlAlchemyInventoryRepository(session)
    await repo.upsert(inventory)
    await session.commit()
