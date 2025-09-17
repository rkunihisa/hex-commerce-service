from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Self, runtime_checkable

from .events import EventPublisher

if TYPE_CHECKING:
    from types import TracebackType

    from .repositories import InventoryRepository, OrderRepository, ProductRepository


@runtime_checkable
class UnitOfWork(Protocol):
    products: ProductRepository
    orders: OrderRepository
    inventories: InventoryRepository
    events: EventPublisher

    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
