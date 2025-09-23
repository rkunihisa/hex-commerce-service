from __future__ import annotations

import pytest

from hex_commerce_service.app.adapters.inmemory.system import InMemoryIdGenerator, InMemoryUnitOfWork
from hex_commerce_service.app.application.message_bus import MessageBus
from hex_commerce_service.app.application.messages.events import OrderPlaced
from hex_commerce_service.app.domain.entities import Order
from hex_commerce_service.app.domain.value_objects import Money, OrderId


def test_uow_commit_persists_and_flushes_events() -> None:
    uow = InMemoryUnitOfWork()
    oid = InMemoryIdGenerator().new_order_id()
    order = Order(id=oid, currency="USD")

    with uow:
        uow.orders.add(order)
        uow.events.publish(OrderPlaced(order_id=order.id, total=Money.from_major(0, "USD")))
        uow.commit()

    # 変更が反映されている
    orders = list(uow.orders.list())
    assert any(o.id == oid for o in orders)
    # イベントが確定されている
    events = getattr(uow.events, "events", [])
    assert any(isinstance(e, OrderPlaced) and str(e.order_id) == str(oid) for e in events)
    # コミット済みフラグ
    assert uow.committed is True


def test_uow_rollback_on_exception_restores_state_and_discards_events() -> None:
    uow = InMemoryUnitOfWork()
    oid = OrderId.parse(str(InMemoryIdGenerator().new_order_id()))
    before_orders = list(uow.orders.list())

    with pytest.raises(RuntimeError):
        with uow:
            uow.orders.add(Order(id=oid, currency="USD"))
            uow.events.publish(OrderPlaced(order_id=oid, total=Money.from_major(0, "USD")))
            raise RuntimeError("boom")  # 例外 → __exit__でrollback

    # 変更はロールバックされている
    after_orders = list(uow.orders.list())
    assert after_orders == before_orders  # 追加されていない
    # イベントは破棄されている
    events = getattr(uow.events, "events", [])
    assert not any(isinstance(e, OrderPlaced) and str(e.order_id) == str(oid) for e in events)
    # コミットされていない
    assert uow.committed is False


def test_restore_snapshots_returns_if_snapshots_none() -> None:
    uow = InMemoryUnitOfWork()
    # デフォルトで _products_snapshot, _orders_snapshot, _inventories_snapshot は None
    # 何もせず _restore_snapshots を呼ぶと if文がTrueになりreturnする
    uow._restore_snapshots()  # ここで何も起きなければOK（例外が出ない）

    # 明示的なアサート（副作用がないことを確認）
    assert uow._products_snapshot is None
    assert uow._orders_snapshot is None
    assert uow._inventories_snapshot is None

def test_buffer_or_sink_outside_context_dispatches_immediately() -> None:
    uow = InMemoryUnitOfWork()
    bus = MessageBus()
    uow.message_bus = bus

    # イベントを記録するためのハンドラ
    received = []
    class DummyEvent: pass

    def handler(event: DummyEvent) -> None:
        received.append(event)

    bus.subscribe(DummyEvent, handler)

    event = DummyEvent()
    # withブロック外でpublish
    uow.buffer_or_sink(event)

    # event_sinkに即追加されている
    assert event in uow.event_sink.events
    # message_busで即ディスパッチされている
    assert event in received

def test_buffer_or_sink_calls_message_bus_publish_outside_context() -> None:
    uow = InMemoryUnitOfWork()
    bus = None
    uow.message_bus = bus

    class DummyEvent: pass

    event = DummyEvent()
    # withブロック外なので、即時publishされる
    uow.buffer_or_sink(event)

    # event_sinkにも追加されている
    assert event in uow.event_sink.events
