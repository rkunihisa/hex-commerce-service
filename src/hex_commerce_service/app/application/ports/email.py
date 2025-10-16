from __future__ import annotations

from typing import Protocol, runtime_checkable

from hex_commerce_service.app.domain.value_objects import Email, OrderId


@runtime_checkable
class EmailNotifier(Protocol):
    async def send_order_confirmation(self, to: Email, order_id: OrderId) -> str: ...
    async def send_order_allocated(self, to: Email, order_id: OrderId, location: str) -> str: ...
