from __future__ import annotations

from dataclasses import dataclass

from hex_commerce_service.app.domain.events import DomainEvent
from hex_commerce_service.app.domain.value_objects import Money, OrderId


@dataclass(frozen=True, slots=True)
class OrderPlaced(DomainEvent):
    order_id: OrderId
    total: Money

    def __init__(self, order_id: OrderId, total: Money) -> None:
        object.__setattr__(self, "occurred_at", DomainEvent.now())
        object.__setattr__(self, "order_id", order_id)
        object.__setattr__(self, "total", total)


@dataclass(frozen=True, slots=True)
class StockAllocated(DomainEvent):
    order_id: OrderId
    location: str

    def __init__(self, order_id: OrderId, location: str) -> None:
        object.__setattr__(self, "occurred_at", DomainEvent.now())
        object.__setattr__(self, "order_id", order_id)
        object.__setattr__(self, "location", location)
