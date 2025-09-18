from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

from hex_commerce_service.app.application.ports.repositories import (
    InventoryRepository,
    OrderRepository,
    ProductRepository,
)
from hex_commerce_service.app.domain.entities import Inventory, Order, Product
from hex_commerce_service.app.domain.value_objects import OrderId, Sku


@dataclass(slots=True)
class InMemoryProductRepository(ProductRepository):
    _items: dict[Sku, Product] = field(default_factory=dict)

    def get_by_sku(self, sku: Sku) -> Product | None:
        return self._items.get(sku)

    def add(self, product: Product) -> None:
        self._items[product.sku] = product

    def list(self) -> Iterable[Product]:
        return list(self._items.values())


@dataclass(slots=True)
class InMemoryOrderRepository(OrderRepository):
    _items: dict[OrderId, Order] = field(default_factory=dict)

    def get(self, order_id: OrderId) -> Order | None:
        return self._items.get(order_id)

    def add(self, order: Order) -> None:
        self._items[order.id] = order

    def list(self) -> Iterable[Order]:
        return list(self._items.values())


@dataclass(slots=True)
class InMemoryInventoryRepository(InventoryRepository):
    _items: dict[str, Inventory] = field(default_factory=dict)

    def get(self, location: str = "default") -> Inventory | None:
        return self._items.get(location)

    def upsert(self, inventory: Inventory) -> None:
        self._items[inventory.location] = inventory

    def list(self) -> Iterable[Inventory]:
        return list(self._items.values())
