from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from collections.abc import Iterable

from hex_commerce_service.app.domain.entities import Inventory, Order, Product
from hex_commerce_service.app.domain.value_objects import OrderId, Sku


@runtime_checkable
class ProductRepository(Protocol):
    def get_by_sku(self, sku: Sku) -> Product | None: ...
    def add(self, product: Product) -> None: ...
    def list(self) -> Iterable[Product]: ...


@runtime_checkable
class OrderRepository(Protocol):
    def get(self, order_id: OrderId) -> Order | None: ...
    def add(self, order: Order) -> None: ...
    def list(self) -> Iterable[Order]: ...


@runtime_checkable
class InventoryRepository(Protocol):
    def get(self, location: str = "default") -> Inventory | None: ...
    def upsert(self, inventory: Inventory) -> None: ...
    def list(self) -> Iterable[Inventory]: ...
