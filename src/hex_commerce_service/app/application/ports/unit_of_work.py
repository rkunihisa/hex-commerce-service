from __future__ import annotations

from typing import Protocol, runtime_checkable

from .events import EventPublisher
from .repositories import InventoryRepository, OrderRepository, ProductRepository


@runtime_checkable
class UnitOfWork(Protocol):
    products: ProductRepository
    orders: OrderRepository
    inventories: InventoryRepository
    events: EventPublisher

    def __enter__(self) -> UnitOfWork: ...
    def __exit__(self, exc_type, exc, tb) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
