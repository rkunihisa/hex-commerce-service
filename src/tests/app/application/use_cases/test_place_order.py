import pytest

from hex_commerce_service.app.adapters.inmemory.system import InMemoryIdGenerator, InMemoryUnitOfWork
from hex_commerce_service.app.application.use_cases import (
    NewOrderItem,
    PlaceOrderCommand,
    PlaceOrderResult,
    PlaceOrderUseCase,
)
from hex_commerce_service.app.domain.value_objects import Sku

def test_execute() -> None:
    # arrange
    target = PlaceOrderUseCase(uow=InMemoryUnitOfWork(), id_gen=InMemoryIdGenerator())
    cmd = PlaceOrderCommand(
        items=[
            NewOrderItem(sku=Sku("SKU123"), quantity=2),
            NewOrderItem(sku=Sku("SKU124"), quantity=1),
        ]
    )

    # act
    result = target.execute(cmd)

    # assert
    assert result.order_id is not None
