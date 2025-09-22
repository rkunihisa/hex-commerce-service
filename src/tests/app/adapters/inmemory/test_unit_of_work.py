from __future__ import annotations

import pytest

from hex_commerce_service.app.adapters.inmemory.system import InMemoryIdGenerator, InMemoryUnitOfWork
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
