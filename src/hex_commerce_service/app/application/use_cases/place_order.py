from __future__ import annotations

from dataclasses import dataclass

from hex_commerce_service.app.application.messages.events import OrderPlaced
from hex_commerce_service.app.application.ports.ids import IdGenerator
from hex_commerce_service.app.application.ports.unit_of_work import UnitOfWork
from hex_commerce_service.app.domain.entities import Order, OrderLine
from hex_commerce_service.app.domain.errors import CurrencyMismatch, ValidationError
from hex_commerce_service.app.domain.value_objects import Money, Sku


@dataclass(frozen=True, slots=True)
class NewOrderItem:
    sku: Sku
    quantity: int


@dataclass(frozen=True, slots=True)
class PlaceOrderCommand:
    items: list[NewOrderItem]


@dataclass(frozen=True, slots=True)
class PlaceOrderResult:
    order_id: str
    total: Money


class PlaceOrderUseCase:
    def __init__(self, uow: UnitOfWork, id_gen: IdGenerator) -> None:
        self._uow = uow
        self._id_gen = id_gen

    def execute(self, cmd: PlaceOrderCommand) -> PlaceOrderResult:
        if not cmd.items:
            raise ValidationError("order must contain at least one item")

        # 1) すべてのSKUが存在し、通貨が一致していることを検証
        products = []
        for item in cmd.items:
            product = self._uow.products.get_by_sku(item.sku)
            if product is None:
                raise ValidationError(f"unknown SKU: {item.sku}")
            if item.quantity <= 0:
                raise ValidationError("quantity must be positive")
            products.append(product)

        # 通貨整合性チェック。最初の商品の通貨に合わせる。
        currency = str(products[0].unit_price.currency)
        for p in products[1:]:
            if str(p.unit_price.currency) != currency:
                raise CurrencyMismatch("all items must share the same currency")

        # 2) Order を生成し、OrderLine を追加
        order = Order(id=self._id_gen.new_order_id(), currency=currency)
        for item, product in zip(cmd.items, products, strict=True):
            order.add_line(
                OrderLine(
                    sku=item.sku,
                    quantity=item.quantity,
                    unit_price=product.unit_price,
                )
            )

        # 3) 永続化 & イベント発行
        with self._uow:
            self._uow.orders.add(order)
            self._uow.events.publish(OrderPlaced(order_id=order.id, total=order.total))
            self._uow.commit()

        return PlaceOrderResult(order_id=str(order.id), total=order.total)
