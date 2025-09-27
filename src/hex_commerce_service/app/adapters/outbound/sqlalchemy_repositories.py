from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, cast

from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from sqlalchemy.ext.asyncio import AsyncSession

from hex_commerce_service.app.application.ports import (
    AsyncInventoryRepository,
    AsyncOrderRepository,
    AsyncProductRepository,
)
from hex_commerce_service.app.domain.entities import Inventory, Order, OrderLine, Product
from hex_commerce_service.app.domain.value_objects import Money, OrderId, Sku
from hex_commerce_service.app.infra.db.models import (
    InventoryItemModel,
    InventoryLocationModel,
    OrderLineModel,
    OrderModel,
    ProductModel,
)

# --------------------------
# Mapping helpers
# --------------------------


def _product_to_model(p: Product) -> ProductModel:
    return ProductModel(
        sku=p.sku.value,
        name=p.name,
        unit_price_amount=Decimal(p.unit_price.amount),
        currency=str(p.unit_price.currency),
    )


def _model_to_product(m: ProductModel) -> Product:
    return Product(
        sku=Sku(m.sku),
        name=m.name,
        unit_price=Money.from_major(Decimal(m.unit_price_amount), m.currency),
    )


def _order_to_model(o: Order) -> OrderModel:
    om = OrderModel(id=str(o.id.value), currency=o.currency)
    # OrderLineModelはrelationship経由で追加されるように構築
    om.lines = [
        OrderLineModel(
            sku=line.sku.value,
            quantity=line.quantity,
            unit_price_amount=Decimal(line.unit_price.amount),
            currency=str(line.unit_price.currency),
        )
        for line in o.lines
    ]
    return om


def _model_to_order(m: OrderModel) -> Order:
    o = Order(id=OrderId.parse(m.id), currency=m.currency, lines=[])
    for lm in m.lines:
        o.add_line(
            OrderLine(
                sku=Sku(lm.sku),
                quantity=lm.quantity,
                unit_price=Money.from_major(Decimal(lm.unit_price_amount), lm.currency),
            )
        )
    return o


def _inventory_to_models(inv: Inventory) -> tuple[InventoryLocationModel, list[InventoryItemModel]]:
    loc = InventoryLocationModel(location=inv.location, description=None)
    items = [
        InventoryItemModel(location=inv.location, sku=sku.value, on_hand=qty)
        for sku, qty in inv._on_hand.items()  # noqa: SLF001 - adapter層で内部を使用
    ]
    return loc, items


def _models_to_inventory(
    loc: InventoryLocationModel, items: Sequence[InventoryItemModel]
) -> Inventory:
    inv = Inventory(location=loc.location)
    for row in items:
        inv.set_on_hand(Sku(row.sku), int(row.on_hand))
    return inv


# --------------------------
# Repositories (async)
# --------------------------


@dataclass(slots=True)
class SqlAlchemyProductRepository(AsyncProductRepository):
    session: AsyncSession

    async def get_by_sku(self, sku: Sku) -> Product | None:
        stmt = select(ProductModel).where(ProductModel.sku == sku.value)
        res = await self.session.execute(stmt)
        row = res.scalar_one_or_none()
        return _model_to_product(row) if row else None

    async def add(self, product: Product) -> None:
        model = _product_to_model(product)
        self.session.add(model)

    async def list(self) -> Iterable[Product]:
        stmt = select(ProductModel).order_by(ProductModel.sku.asc())
        res = await self.session.execute(stmt)
        models = cast("list[ProductModel]", res.scalars().all())
        return [_model_to_product(m) for m in models]


@dataclass(slots=True)
class SqlAlchemyOrderRepository(AsyncOrderRepository):
    session: AsyncSession

    async def get(self, order_id: OrderId) -> Order | None:
        stmt = (
            select(OrderModel)
            .options(selectinload(OrderModel.lines))
            .where(OrderModel.id == str(order_id.value))
        )
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()
        return _model_to_order(model) if model else None

    async def add(self, order: Order) -> None:
        model = _order_to_model(order)
        # 親にぶら下げて add すれば order_lines も一括追加
        self.session.add(model)

    async def list(self) -> Iterable[Order]:
        stmt = (
            select(OrderModel)
            .options(selectinload(OrderModel.lines))
            .order_by(OrderModel.created_at.asc())
        )
        res = await self.session.execute(stmt)
        models = cast("list[OrderModel]", res.scalars().all())
        return [_model_to_order(m) for m in models]


@dataclass(slots=True)
class SqlAlchemyInventoryRepository(AsyncInventoryRepository):
    session: AsyncSession

    async def get(self, location: str = "default") -> Inventory | None:
        loc = await self.session.get(InventoryLocationModel, location)
        if not loc:
            return None
        stmt = select(InventoryItemModel).where(InventoryItemModel.location == location)
        res = await self.session.execute(stmt)
        items = cast("list[InventoryItemModel]", res.scalars().all())
        return _models_to_inventory(loc, items)

    async def upsert(self, inventory: Inventory) -> None:
        # ロケーションを upsert
        loc_model = await self.session.get(InventoryLocationModel, inventory.location)
        if not loc_model:
            loc_model = InventoryLocationModel(location=inventory.location, description=None)
            self.session.add(loc_model)
            await self.session.flush()  # PK確定

        # 既存itemを削除してから入れ直し.シンプル実装
        await self.session.execute(
            delete(InventoryItemModel).where(InventoryItemModel.location == inventory.location)
        )
        _, items = _inventory_to_models(inventory)
        for im in items:
            self.session.add(im)

    async def list(self) -> Iterable[Inventory]:
        stmt = select(InventoryLocationModel).order_by(InventoryLocationModel.location.asc())
        res = await self.session.execute(stmt)
        locs = cast("list[InventoryLocationModel]", res.scalars().all())

        inventories: list[Inventory] = []
        if not locs:
            return inventories

        # まとめてitems取得
        locations = [loc.location for loc in locs]
        items_stmt = select(InventoryItemModel).where(InventoryItemModel.location.in_(locations))
        items_res = await self.session.execute(items_stmt)
        items = cast("list[InventoryItemModel]", items_res.scalars().all())

        items_by_loc: dict[str, list[InventoryItemModel]] = {}
        for it in items:
            items_by_loc.setdefault(it.location, []).append(it)

        for loc in locs:
            inventories.extend(_models_to_inventory(loc, items_by_loc.get(loc.location, [])))
        return inventories
