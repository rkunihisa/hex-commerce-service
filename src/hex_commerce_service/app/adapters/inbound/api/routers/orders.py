from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from hex_commerce_service.app.adapters.inbound.api.dtos import (
    MoneyOut,
    PlaceOrderIn,
    PlaceOrderOut,
)
from hex_commerce_service.app.adapters.inbound.api.errors import to_http
from hex_commerce_service.app.adapters.inmemory.system import (
    InMemoryIdGenerator,
    InMemoryUnitOfWork,
)
from hex_commerce_service.app.application.use_cases.allocate_stock import (
    AllocateStockCommand,
    AllocateStockUseCase,
)
from hex_commerce_service.app.application.use_cases.place_order import (
    NewOrderItem,
    PlaceOrderCommand,
    PlaceOrderUseCase,
)
from hex_commerce_service.app.domain.value_objects import OrderId, Sku

router = APIRouter()


def get_uow() -> InMemoryUnitOfWork:
    raise RuntimeError("dependency not provided")


def get_id_gen() -> InMemoryIdGenerator:
    raise RuntimeError("dependency not provided")


@router.post("", response_model=PlaceOrderOut, status_code=status.HTTP_201_CREATED)
def place_order(
    body: PlaceOrderIn,
    uow: Annotated[InMemoryUnitOfWork, Depends(get_uow)],
    id_gen: Annotated[InMemoryIdGenerator, Depends(get_id_gen)],
) -> PlaceOrderOut:
    try:
        uc = PlaceOrderUseCase(uow=uow, id_gen=id_gen)
        cmd = PlaceOrderCommand(items=[NewOrderItem(Sku(i.sku), i.quantity) for i in body.items])
        res = uc.execute(cmd)
        return PlaceOrderOut(
            order_id=res.order_id,
            total=MoneyOut(currency=str(res.total.currency), amount=f"{res.total.amount:.2f}"),
        )
    except Exception as exc:
        raise to_http(exc) from exc


@router.post("/{order_id}/allocate", status_code=status.HTTP_200_OK)
def allocate_stock(
    order_id: str,
    uow: Annotated[InMemoryUnitOfWork, Depends(get_uow)],
) -> dict[str, str]:
    try:
        uc = AllocateStockUseCase(uow=uow)
        uc.execute(AllocateStockCommand(order_id=OrderId.parse(order_id)))
    except Exception as exc:
        raise to_http(exc) from exc
    else:
        return {"status": "allocated", "order_id": order_id}
