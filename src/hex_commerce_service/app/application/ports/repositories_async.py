from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from collections.abc import Iterable

from hex_commerce_service.app.domain.entities import Inventory, Order, Product
from hex_commerce_service.app.domain.value_objects import OrderId, Sku


@runtime_checkable
class AsyncProductRepository(Protocol):
    async def get_by_sku(self, sku: Sku) -> Product | None: ...
    async def add(self, product: Product) -> None: ...
    async def list(self) -> Iterable[Product]: ...


@runtime_checkable
class AsyncOrderRepository(Protocol):
    async def get(self, order_id: OrderId) -> Order | None: ...
    async def add(self, order: Order) -> None: ...
    async def list(self) -> Iterable[Order]: ...


@runtime_checkable
class AsyncInventoryRepository(Protocol):
    async def get(self, location: str = "default") -> Inventory | None: ...
    async def upsert(self, inventory: Inventory) -> None: ...
    async def list(self) -> Iterable[Inventory]: ...
