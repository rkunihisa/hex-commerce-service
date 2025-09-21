from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

from hex_commerce_service.app.application.ports import (
    InventoryRepository,
    OrderRepository,
    ProductRepository,
)
from hex_commerce_service.app.domain.entities import Inventory, Order, Product
from hex_commerce_service.app.domain.value_objects import OrderId, Sku


@dataclass(slots=True)
class InMemoryProductRepository(ProductRepository):
    items: dict[Sku, Product] = field(default_factory=dict)

    def get_by_sku(self, sku: Sku) -> Product | None:
        return self.items.get(sku)

    def add(self, product: Product) -> None:
        self.items[product.sku] = product

    def list(self) -> Iterable[Product]:
        return list(self.items.values())


@dataclass(slots=True)
class InMemoryOrderRepository(OrderRepository):
    items: dict[OrderId, Order] = field(default_factory=dict)

    def get(self, order_id: OrderId) -> Order | None:
        return self.items.get(order_id)

    def add(self, order: Order) -> None:
        self.items[order.id] = order

    def list(self) -> Iterable[Order]:
        return list(self.items.values())


@dataclass(slots=True)
class InMemoryInventoryRepository(InventoryRepository):
    items: dict[str, Inventory] = field(default_factory=dict)

    def get(self, location: str = "default") -> Inventory | None:
        return self.items.get(location)

    def upsert(self, inventory: Inventory) -> None:
        self.items[inventory.location] = inventory

    def list(self) -> Iterable[Inventory]:
        return list(self.items.values())
