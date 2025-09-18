from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable
from types import TracebackType

from hex_commerce_service.app.application.ports.events import EventPublisher
from hex_commerce_service.app.application.ports.ids import IdGenerator
from hex_commerce_service.app.application.ports.unit_of_work import UnitOfWork
from hex_commerce_service.app.application.ports.repositories import (
    InventoryRepository,
    OrderRepository,
    ProductRepository,
)
from hex_commerce_service.app.application.ports.time import Clock
from hex_commerce_service.app.domain.value_objects import OrderId
from hex_commerce_service.app.adapters.inmemory.repositories import (
    InMemoryInventoryRepository,
    InMemoryOrderRepository,
    InMemoryProductRepository,
)


@dataclass(slots=True)
class InMemoryClock(Clock):
    fixed: datetime | None = None

    def now(self) -> datetime:
        return self.fixed or datetime.now(tz=timezone.utc)


@dataclass(slots=True)
class InMemoryIdGenerator(IdGenerator):
    def new_order_id(self) -> OrderId:
        # Use UUID v4; deterministic behavior is not required for tests.
        from uuid import uuid4

        return OrderId(uuid4())


@dataclass(slots=True)
class InMemoryEventPublisher(EventPublisher):
    events: list[object] = field(default_factory=list)

    def publish(self, event: object) -> None:
        self.events.append(event)

    def publish_many(self, events: Iterable[object]) -> None:
        self.events.extend(list(events))


@dataclass(slots=True)
class InMemoryUnitOfWork(UnitOfWork):
    products: ProductRepository = field(default_factory=InMemoryProductRepository)
    orders: OrderRepository = field(default_factory=InMemoryOrderRepository)
    inventories: InventoryRepository = field(default_factory=InMemoryInventoryRepository)
    events: EventPublisher = field(default_factory=InMemoryEventPublisher)

    _committed: bool = False
    _in_context: bool = False

    def __enter__(self) -> InMemoryUnitOfWork:
        self._in_context = True
        self._committed = False
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None
    ) -> None:
        self._in_context = False
        if exc_type:
            self.rollback()
            self.rollback()

    def commit(self) -> None:
        self._committed = True

    def rollback(self) -> None:
        self._committed = False

    @property
    def committed(self) -> bool:
        return self._committed
