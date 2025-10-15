from __future__ import annotations

from datetime import datetime
from typing import Any, TypedDict

from hex_commerce_service.app.application.messages.events import OrderPlaced, StockAllocated
from hex_commerce_service.app.domain.value_objects import Money, OrderId


class EventEnvelope(TypedDict):
    type: str
    occurred_at: str
    payload: dict[str, Any]


def serialize_event(evt: object) -> EventEnvelope:
    if isinstance(evt, OrderPlaced):
        return {
            "type": "OrderPlaced",
            "occurred_at": evt.occurred_at.isoformat(),
            "payload": {
                "order_id": str(evt.order_id),
                "total": {"amount": f"{evt.total.amount:.2f}", "currency": str(evt.total.currency)},
            },
        }
    if isinstance(evt, StockAllocated):
        return {
            "type": "StockAllocated",
            "occurred_at": evt.occurred_at.isoformat(),
            "payload": {"order_id": str(evt.order_id), "location": evt.location},
        }
    raise TypeError(f"cannot serialize event type: {type(evt).__name__}")


def deserialize_event(env: EventEnvelope) -> object:
    t = env["type"]
    occurred = datetime.fromisoformat(env["occurred_at"])
    if t == "OrderPlaced":
        payload = env["payload"]
        evt = OrderPlaced(
            order_id=OrderId.parse(payload["order_id"]),
            total=Money.from_major(payload["total"]["amount"], payload["total"]["currency"]),
        )
        evt.occurred_at = occurred
        return evt
    if t == "StockAllocated":
        payload = env["payload"]
        evt = StockAllocated(
            order_id=OrderId.parse(payload["order_id"]),
            location=payload["location"],
        )
        evt.occurred_at = occurred
        return evt
    raise TypeError(f"cannot deserialize event type: {t}")
