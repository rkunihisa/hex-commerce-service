from __future__ import annotations

import pytest

from hex_commerce_service.app.adapters.inmemory.system import InMemoryIdGenerator, InMemoryUnitOfWork
from hex_commerce_service.app.application.messages.events import StockAllocated
from hex_commerce_service.app.application.use_cases.allocate_stock import (
    AllocateStockCommand,
    AllocateStockUseCase,
)
from hex_commerce_service.app.application.use_cases.place_order import (
    NewOrderItem,
    PlaceOrderCommand,
    PlaceOrderUseCase,
)
from hex_commerce_service.app.domain.errors import OutOfStockError, ValidationError
from hex_commerce_service.app.domain.value_objects import Money, Sku
from hex_commerce_service.app.domain.entities import Product, Inventory


def seed_order_and_inventory(uow: InMemoryUnitOfWork) -> str:
    id_gen = InMemoryIdGenerator()

    # products and inventory
    p1 = Product(sku=Sku("ABC-1"), name="Widget", unit_price=Money.from_major(10, "USD"))
    p2 = Product(sku=Sku("ABC-2"), name="Gadget", unit_price=Money.from_major(5, "USD"))
    uow.products.add(p1)
    uow.products.add(p2)

    inv = Inventory(location="default")
    inv.set_on_hand(Sku("ABC-1"), 10)
    inv.set_on_hand(Sku("ABC-2"), 10)
    uow.inventories.upsert(inv)

    # place order
    place = PlaceOrderUseCase(uow=uow, id_gen=id_gen)
    res = place.execute(
        PlaceOrderCommand(
            items=[NewOrderItem(Sku("ABC-1"), 3), NewOrderItem(Sku("ABC-2"), 4)]
        )
    )
    order_id = str(res.order_id)
    return order_id


def test_allocate_stock_success() -> None:
    uow = InMemoryUnitOfWork()
    order_id = seed_order_and_inventory(uow)
    uc = AllocateStockUseCase(uow=uow)
    res = uc.execute(AllocateStockCommand(order_id=uow.orders.list().__iter__().__next__().id))

    assert res.order_id == order_id
    inv = uow.inventories.get("default")
    assert inv is not None
    assert inv.available(Sku("ABC-1")) == 7  # 10 - 3
    assert inv.available(Sku("ABC-2")) == 6  # 10 - 4

    events = getattr(uow.events, "events", [])
    assert any(isinstance(e, StockAllocated) for e in events)

def test_allocate_stock_no_inventory() -> None:
    uow = InMemoryUnitOfWork()
    uc = AllocateStockUseCase(uow=uow)
    # place order but no inventory
    order_id = seed_order_and_inventory(uow)  # different UoW
    with pytest.raises(ValidationError):
        uc.execute(AllocateStockCommand(order_id=InMemoryIdGenerator().new_order_id()))

def test_allocate_stock_invalid_command() -> None:
    # insufficient stock
    uow = InMemoryUnitOfWork()
    uc = AllocateStockUseCase(uow=uow)
    order_id = seed_order_and_inventory(uow)
    inv = uow.inventories.get("default")
    assert inv is not None
    with pytest.raises(ValidationError):
        uc.execute(AllocateStockCommand(order_id=list(uow.orders.list())[0].id, location=None))

def test_allocate_stock_insufficient_stock() -> None:
    # insufficient stock
    uow = InMemoryUnitOfWork()
    order_id = seed_order_and_inventory(uow)
    inv = uow.inventories.get("default")
    assert inv is not None
    inv.set_on_hand(Sku("ABC-1"), 2)  # not enough for 3
    uc = AllocateStockUseCase(uow=uow)
    with pytest.raises(OutOfStockError):
        uc.execute(AllocateStockCommand(order_id=list(uow.orders.list())[0].id))
