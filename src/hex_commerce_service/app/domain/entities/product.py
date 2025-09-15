from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from hex_commerce_service.app.domain.errors import ValidationError
from hex_commerce_service.app.domain.value_objects import Money, Sku


@dataclass(slots=True)
class Product:
    """Product is identified by SKU. Name and price are attributes."""

    sku: Sku
    name: str
    unit_price: Money
    active: bool = True

    # dunder equality/hash are identity-based (SKU)
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Product):
            return NotImplemented
        return str(self.sku) == str(other.sku)

    def __hash__(self) -> int:  # allow usage in sets/dicts
        return hash(self.sku)

    def rename(self, new_name: str) -> None:
        name = new_name.strip()
        if not name:
            raise ValidationError("product name must not be empty")
        self.name = name

    def change_price(self, new_price: Money) -> None:
        if new_price.amount <= 0:
            raise ValidationError("unit price must be positive")
        # 通貨は制約しない。注文側で通貨整合性を担保する。
        self.unit_price = new_price


# a sentinel for simple pattern matching in tests if needed
ANY_SKU: Final[Sku] = Sku("A")  # not used for logic; tests may override with their own constants
