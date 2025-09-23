from __future__ import annotations

from hex_commerce_service.app.adapters.inmemory.notifications import InMemoryNotifier
from hex_commerce_service.app.adapters.inmemory.system import InMemoryIdGenerator, InMemoryUnitOfWork
from hex_commerce_service.app.application.message_bus import MessageBus
from hex_commerce_service.app.application.messages.events import OrderPlaced, StockAllocated
from hex_commerce_service.app.application.use_cases.allocate_stock import (
    AllocateStockCommand,
    AllocateStockUseCase,
)
from hex_commerce_service.app.application.use_cases.place_order import (
    NewOrderItem,
    PlaceOrderCommand,
    PlaceOrderUseCase,
)
from hex_commerce_service.app.domain.entities import Inventory, Product
from hex_commerce_service.app.domain.value_objects import Money, Sku


def test_e2e_place_order_alloc_notify_via_message_bus() -> None:
    # UoW + Bus + Notifier 準備
    uow = InMemoryUnitOfWork()
    bus = MessageBus()
    notifier = InMemoryNotifier()
    uow.message_bus = bus

    # ハンドラ登録.最小.
    def on_order_placed(ev: OrderPlaced) -> None:
        uc = AllocateStockUseCase(uow)
        uc.execute(AllocateStockCommand(order_id=ev.order_id))

    def on_stock_allocated(ev: StockAllocated) -> None:
        notifier.order_allocated(order_id=ev.order_id, location=ev.location)

    bus.subscribe(OrderPlaced, on_order_placed)
    bus.subscribe(StockAllocated, on_stock_allocated)

    # データ準備.商品と在庫.
    p1 = Product(sku=Sku("ABC-1"), name="Widget", unit_price=Money.from_major(10, "USD"))
    p2 = Product(sku=Sku("ABC-2"), name="Gadget", unit_price=Money.from_major(5, "USD"))
    uow.products.add(p1)
    uow.products.add(p2)

    inv = Inventory(location="default")
    inv.set_on_hand(Sku("ABC-1"), 5)
    inv.set_on_hand(Sku("ABC-2"), 7)
    uow.inventories.upsert(inv)

    # 受注.PlaceOrder → commit で OrderPlaced が発行され、バス経由で在庫引当→通知まで進む
    place = PlaceOrderUseCase(uow=uow, id_gen=InMemoryIdGenerator())
    res = place.execute(
        PlaceOrderCommand(
            items=[NewOrderItem(Sku("ABC-1"), 2), NewOrderItem(Sku("ABC-2"), 3)]
        )
    )

    # 在庫が引き当てられている
    inv2 = uow.inventories.get("default")
    assert inv2 is not None
    assert inv2.available(Sku("ABC-1")) == 3  # 5 - 2
    assert inv2.available(Sku("ABC-2")) == 4  # 7 - 3

    # 通知が送られている
    sent = notifier.sent
    assert len(sent) == 1
    oid, loc = sent[0]
    assert str(oid) == res.order_id
    assert loc == "default"

    # エラーは発生していない
    assert not bus.errors

class CustomBaseException(BaseException):
    pass

def test_message_bus_catches_base_exception() -> None:
    bus = MessageBus()
    event = object()

    def handler(_: object) -> None:
        raise CustomBaseException("test base exception")

    bus.subscribe(type(event), handler)
    bus.publish(event)

    assert len(bus.errors) == 1
    err_event, exc = bus.errors[0]
    assert err_event is event
    assert isinstance(exc, CustomBaseException)
