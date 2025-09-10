from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, Iterable, List

from hex_commerce_service.app.domain.errors import CurrencyMismatch, NegativeQuantity, ValidationError
from hex_commerce_service.app.domain.value_objects import Money, OrderId, Sku


@dataclass(frozen=True, slots=True)
class OrderLine:
    """Line item inside an Order. Immutable value-like element."""
    sku: Sku
    quantity: int
    unit_price: Money

    # 明示的にパターンマッチ可能に（名前でのマッチを意図）
    __match_args__: ClassVar[tuple[str, str, str]] = ("sku", "quantity", "unit_price")

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise NegativeQuantity("order line quantity must be positive")

    @property
    def line_total(self) -> Money:
        return self.unit_price * self.quantity  # Money * int


@dataclass(slots=True)
class Order:
    """Aggregate root for order.

    Invariants:
      - All lines must share the same currency as the order.
      - Order total equals the sum of line totals (computed).
    """

    id: OrderId
    currency: str  # ISO4217-like (CurrencyCode). Keep as str to ease serialization boundary.
    lines: List[OrderLine] = field(default_factory=list)

    def __post_init__(self) -> None:
        cur = self.currency
        if len(cur) != 3 or not cur.isalpha() or not cur.isupper():
            raise ValidationError("order.currency must be 3 uppercase letters")

    # identity-based equality/hash
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Order):
            return NotImplemented
        return str(self.id) == str(other.id)

    def __hash__(self) -> int:
        return hash(self.id)

    # mutation methods
    def add_line(self, line: OrderLine) -> None:
        if str(line.unit_price.currency) != self.currency:
            raise CurrencyMismatch("line currency must match order currency")
        self.lines.append(line)

    def add_item(self, sku: Sku, quantity: int, unit_price: Money) -> None:
        if str(unit_price.currency) != self.currency:
            raise CurrencyMismatch("unit price currency must match order currency")
        self.add_line(OrderLine(sku=sku, quantity=quantity, unit_price=unit_price))

    def remove_line_at(self, index: int) -> OrderLine:
        try:
            return self.lines.pop(index)
        except IndexError as exc:
            raise ValidationError(f"no order line at index {index}") from exc

    @property
    def total(self) -> Money:
        # sum via Money addition (same currency guaranteed)
        total = Money.from_major(0, self.currency)
        for ln in self.lines:
            total = total + ln.line_total
        return total

    def iterate_skus(self) -> Iterable[Sku]:
        return (ln.sku for ln in self.lines)
