from __future__ import annotations

from dataclasses import dataclass, field

from hex_commerce_service.app.application.ports.notifications import Notifier
from hex_commerce_service.app.domain.value_objects import OrderId


@dataclass(slots=True)
class InMemoryNotifier(Notifier):
    """送信済み通知をメモリに蓄積して観測可能にする."""

    sent: list[tuple[OrderId, str]] = field(default_factory=list)

    def order_allocated(self, order_id: OrderId, location: str) -> None:
        self.sent.append((order_id, location))
