import pytest

from hex_commerce_service.app.adapters.inmemory.system import InMemoryIdGenerator, InMemoryUnitOfWork
from hex_commerce_service.app.application.use_cases import (
    NewOrderItem,
    PlaceOrderCommand,
    PlaceOrderResult,
    PlaceOrderUseCase,
)
from hex_commerce_service.app.application.messages.events import OrderPlaced
from hex_commerce_service.app.domain.entities.product import Product
from hex_commerce_service.app.domain.errors import CurrencyMismatchError, ValidationError
from hex_commerce_service.app.domain.value_objects import Sku, Money


def test_execute() -> None:
    # arrange
    uow = InMemoryUnitOfWork()
    id_gen = InMemoryIdGenerator()

    # Seed products (same currency)
    p1 = Product(sku=Sku("ABC-1"), name="Widget", unit_price=Money.from_major(12.50, "USD"))
    p2 = Product(sku=Sku("ABC-2"), name="Gadget", unit_price=Money.from_major("7.25", "USD"))
    uow.products.add(p1)
    uow.products.add(p2)

    # act
    uc = PlaceOrderUseCase(uow=uow, id_gen=id_gen)
    cmd = PlaceOrderCommand(items=[NewOrderItem(Sku("ABC-1"), 2), NewOrderItem(Sku("ABC-2"), 3)])
    res = uc.execute(cmd)

    # assert
    # order persisted
    orders = list(uow.orders.list())
    assert len(orders) == 1
    order = orders[0]
    assert res.order_id == str(order.id)
    assert str(order.total) == "USD 46.75"

    # event emitted
    events = getattr(uow.events, "events", [])
    assert any(isinstance(e, OrderPlaced) and str(e.order_id) == res.order_id for e in events)

    # "commit" has been marked
    assert getattr(uow, "committed", False) is True


def test_place_order_rejects_empty_and_currency_mismatch() -> None:
    uow = InMemoryUnitOfWork()
    id_gen = InMemoryIdGenerator()
    uc = PlaceOrderUseCase(uow=uow, id_gen=id_gen)

    with pytest.raises(ValidationError):
        uc.execute(PlaceOrderCommand(items=[]))

    # currency mismatch across products
    uow.products.add(Product(sku=Sku("X-USD"), name="US", unit_price=Money.from_major(1, "USD")))
    uow.products.add(Product(sku=Sku("X-EUR"), name="EU", unit_price=Money.from_major(1, "EUR")))
    with pytest.raises(CurrencyMismatchError):
        uc.execute(PlaceOrderCommand(items=[NewOrderItem(Sku("X-USD"), 1), NewOrderItem(Sku("X-EUR"), 1)]))

    # unknown SKU
    with pytest.raises(ValidationError):
        uc.execute(PlaceOrderCommand(items=[NewOrderItem(Sku("NOPE"), 1)]))

def test_place_order_rejects_item_quantity_zero() -> None:
    # arrange
    uow = InMemoryUnitOfWork()
    id_gen = InMemoryIdGenerator()

    # Seed products (same currency)
    p1 = Product(sku=Sku("ABC-1"), name="Widget", unit_price=Money.from_major(12.50, "USD"))
    p2 = Product(sku=Sku("ABC-2"), name="Gadget", unit_price=Money.from_major("7.25", "USD"))
    uow.products.add(p1)
    uow.products.add(p2)

    # act
    uc = PlaceOrderUseCase(uow=uow, id_gen=id_gen)
    cmd = PlaceOrderCommand(items=[NewOrderItem(Sku("ABC-1"), 0), NewOrderItem(Sku("ABC-2"), -1)])

    with pytest.raises(ValidationError):
        uc.execute(cmd)
