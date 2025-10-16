from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from hex_commerce_service.app.domain.value_objects import Money, OrderId


@dataclass(frozen=True, slots=True)
class PaymentResult:
    charge_id: str
    order_id: OrderId
    amount: Money


@runtime_checkable
class PaymentGateway(Protocol):
    async def charge(
        self,
        order_id: OrderId,
        amount: Money,
        card_token: str,
        idempotency_key: str,
        timeout_seconds: float | None = None,
    ) -> PaymentResult: ...
