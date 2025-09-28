from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from itertools import count
from typing import Iterable

from hex_commerce_service.app.domain.entities import Inventory, Order, OrderLine, Product
from hex_commerce_service.app.domain.value_objects import Money, OrderId, Sku


_sku_seq = count(1)
_order_seq = count(1)


@dataclass(slots=True)
class ProductFactory:
    currency: str = "USD"
    base_price: Decimal = Decimal("10.00")

    def build(self, name: str | None = None, price: Decimal | None = None) -> Product:
        n = next(_sku_seq)
        sku = Sku(f"SKU-{n:05d}")
        pr = Money.from_major(price if price is not None else self.base_price, self.currency)
        return Product(sku=sku, name=name or f"Product {n}", unit_price=pr)


@dataclass(slots=True)
class OrderFactory:
    currency: str = "USD"

    def build(self, lines: Iterable[tuple[Sku, int, Money]]) -> Order:
        oid = OrderId.parse(str(OrderId.new()))
        order = Order(id=oid, currency=self.currency)
        for sku, qty, price in lines:
            order.add_line(OrderLine(sku=sku, quantity=qty, unit_price=price))
        return order


@dataclass(slots=True)
class InventoryFactory:
    location: str = "default"
    _stocks: dict[Sku, int] = field(default_factory=dict)

    def with_stock(self, sku: Sku, qty: int) -> "InventoryFactory":
        self._stocks[sku] = qty
        return self

    def build(self) -> Inventory:
        inv = Inventory(location=self.location)
        for sku, qty in self._stocks.items():
            inv.set_on_hand(sku, qty)
        return inv
