from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Self, cast
from uuid import uuid4

from hex_commerce_service.app.domain.entities.inventory import Inventory
from hex_commerce_service.app.domain.entities.order import Order
from hex_commerce_service.app.domain.entities.product import Product
from hex_commerce_service.app.domain.value_objects.sku import Sku

if TYPE_CHECKING:
    from collections.abc import Iterable
    from types import TracebackType

from hex_commerce_service.app.application.ports import (
    Clock,
    EventPublisher,
    IdGenerator,
    InventoryRepository,
    OrderRepository,
    ProductRepository,
    UnitOfWork,
)
from hex_commerce_service.app.domain.value_objects import OrderId

from .repositories import (
    InMemoryInventoryRepository,
    InMemoryOrderRepository,
    InMemoryProductRepository,
)


@dataclass(slots=True)
class InMemoryClock(Clock):
    fixed: datetime | None = None

    def now(self) -> datetime:
        return self.fixed or datetime.now(tz=UTC)


@dataclass(slots=True)
class InMemoryIdGenerator(IdGenerator):
    @staticmethod
    def new_order_id() -> OrderId:
        # Use UUID v4; deterministic behavior is not required for tests.
        return OrderId(uuid4())


@dataclass(slots=True)
class InMemoryEventSink:
    events: list[object] = field(default_factory=list)


@dataclass(slots=True)
class TransactionalEventPublisher(EventPublisher):
    _uow: InMemoryUnitOfWork

    def publish(self, event: object) -> None:
        self._uow.buffer_or_sink(event)

    def publish_many(self, events: Iterable[object]) -> None:
        for e in events:
            self.publish(e)

    # 互換性: testsで `getattr(uow.events, "events", [])` を参照できるように
    @property
    def events(self) -> list[object]:
        return self._uow._event_sink.events


@dataclass(slots=True)
class InMemoryUnitOfWork(UnitOfWork):
    products: ProductRepository = field(default_factory=InMemoryProductRepository)
    orders: OrderRepository = field(default_factory=InMemoryOrderRepository)
    inventories: InventoryRepository = field(default_factory=InMemoryInventoryRepository)

    # イベントはトランザクション・バッファリング
    _event_sink: InMemoryEventSink = field(default_factory=InMemoryEventSink)
    events: EventPublisher = field(init=False)

    _committed: bool = False
    _in_context: bool = False

    # スナップショット
    _products_snapshot: dict[Sku, Product] | None = None
    _orders_snapshot: dict[OrderId, Order] | None = None
    _inventories_snapshot: dict[Sku, Inventory] | None = None

    # ペンディングイベント
    _pending_events: list[object] = field(default_factory=list)

    def __post_init__(self) -> None:
        # UoWに結び付いたトランザクション対応Publisher
        object.__setattr__(self, "events", TransactionalEventPublisher(self))

    # --- コンテキスト管理 ---
    def __enter__(self) -> Self:
        self._in_context = True
        self._committed = False
        self._take_snapshots()
        self._pending_events.clear()
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None) -> None:
        try:
            if exc_type:
                self.rollback()
        finally:
            self._in_context = False

    # --- トランザクション操作 ---
    def commit(self) -> None:
        # 正常に終了する場合のみイベントを確定
        self._event_sink.events.extend(self._pending_events)
        self._pending_events.clear()
        self._clear_snapshots()
        self._committed = True

    def rollback(self) -> None:
        # スナップショットから復元し、ペンディングイベント破棄
        self._restore_snapshots()
        self._pending_events.clear()
        self._committed = False

    @property
    def committed(self) -> bool:
        return self._committed

    # --- 内部ヘルパ ---
    def buffer_or_sink(self, event: object) -> None:
        if self._in_context:
            self._pending_events.append(event)
        else:
            self._event_sink.events.append(event)

    def _take_snapshots(self) -> None:
        # 具体型にキャストして内部Dictをスナップショット
        prod_repo = cast(InMemoryProductRepository, self.products)
        order_repo = cast(InMemoryOrderRepository, self.orders)
        inv_repo = cast(InMemoryInventoryRepository, self.inventories)

        self._products_snapshot = dict(prod_repo._items)
        self._orders_snapshot = dict(order_repo._items)
        self._inventories_snapshot = dict(inv_repo._items)

    def _restore_snapshots(self) -> None:
        if (
            self._products_snapshot is None
            or self._orders_snapshot is None
            or self._inventories_snapshot is None
        ):
            return

        prod_repo = cast(InMemoryProductRepository, self.products)
        order_repo = cast(InMemoryOrderRepository, self.orders)
        inv_repo = cast(InMemoryInventoryRepository, self.inventories)

        prod_repo._items = dict(self._products_snapshot)
        order_repo._items = dict(self._orders_snapshot)
        inv_repo._items = dict(self._inventories_snapshot)

        self._clear_snapshots()

    def _clear_snapshots(self) -> None:
        self._products_snapshot = None
        self._orders_snapshot = None
        self._inventories_snapshot = None
