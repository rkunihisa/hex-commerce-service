from __future__ import annotations

from dataclasses import dataclass

from hex_commerce_service.app.domain.value_objects import Money, OrderId


@dataclass(frozen=True, slots=True)
class OrderPlaced:
    order_id: OrderId
    total: Money


@dataclass(frozen=True, slots=True)
class StockAllocated:
    order_id: OrderId
    location: str
