from __future__ import annotations

from typing import Protocol, runtime_checkable

from hex_commerce_service.app.domain.value_objects import OrderId


@runtime_checkable
class Notifier(Protocol):
    """通知の抽象Port。メール/Slackなど実装はアダプタ側で."""

    def order_allocated(self, order_id: OrderId, location: str) -> None: ...
