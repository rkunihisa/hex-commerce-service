from __future__ import annotations

from typing import Protocol, runtime_checkable

from hex_commerce_service.app.domain.value_objects import OrderId


@runtime_checkable
class IdGenerator(Protocol):
    def new_order_id(self) -> OrderId: ...
