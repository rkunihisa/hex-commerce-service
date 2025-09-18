from __future__ import annotations

from dataclasses import dataclass

from hex_commerce_service.app.application.messages.events import StockAllocated
from hex_commerce_service.app.application.ports.unit_of_work import UnitOfWork
from hex_commerce_service.app.domain.errors import OutOfStock, ValidationError
from hex_commerce_service.app.domain.value_objects import OrderId


@dataclass(frozen=True, slots=True)
class AllocateStockCommand:
    order_id: OrderId
    location: str = "default"


@dataclass(frozen=True, slots=True)
class AllocateStockResult:
    order_id: str
    location: str


class AllocateStockUseCase:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, cmd: AllocateStockCommand) -> AllocateStockResult:
        order = self._uow.orders.get(cmd.order_id)
        if order is None:
            raise ValidationError(f"order not found: {cmd.order_id}")

        inventory = self._uow.inventories.get(cmd.location)
        if inventory is None:
            raise ValidationError(f"inventory not found: {cmd.location}")

        # 事前チェック。全行を満たせるか。
        for line in order.lines:
            if inventory.available(line.sku) < line.quantity:
                raise OutOfStock(
                    f"insufficient stock for {line.sku}: "
                    f"need {line.quantity}, have {inventory.available(line.sku)}"
                )

        # 実際の割当。原子的に近い挙動。
        with self._uow:
            for line in order.lines:
                inventory.allocate(line.sku, line.quantity)
            self._uow.inventories.upsert(inventory)
            self._uow.events.publish(StockAllocated(order_id=order.id, location=cmd.location))
            self._uow.commit()

        return AllocateStockResult(order_id=str(order.id), location=cmd.location)
