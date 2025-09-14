from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from hex_commerce_service.app.domain.errors import NegativeQuantity, OutOfStock
from hex_commerce_service.app.domain.value_objects import Sku


@dataclass(slots=True)
class Inventory:
    """Inventory keeps on-hand quantities per SKU with the invariant: stock >= 0."""

    location: str = "default"
    _on_hand: Dict[Sku, int] = field(default_factory=dict)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Inventory):
            return NotImplemented
        return self.location == other.location

    def __hash__(self) -> int:
        return hash(self.location)

    def available(self, sku: Sku) -> int:
        return self._on_hand.get(sku, 0)

    def set_on_hand(self, sku: Sku, qty: int) -> None:
        if qty < 0:
            raise NegativeQuantity("on-hand cannot be negative")
        self._on_hand[sku] = qty

    def add(self, sku: Sku, qty: int) -> None:
        if qty <= 0:
            raise NegativeQuantity("add quantity must be positive")
        self._on_hand[sku] = self.available(sku) + qty

    def remove(self, sku: Sku, qty: int) -> None:
        if qty <= 0:
            raise NegativeQuantity("remove quantity must be positive")
        cur = self.available(sku)
        if qty > cur:
            raise OutOfStock(f"cannot remove {qty}; only {cur} available")
        self._on_hand[sku] = cur - qty

    def can_fulfill(self, sku: Sku, qty: int) -> bool:
        if qty <= 0:
            raise NegativeQuantity("requested quantity must be positive")
        return self.available(sku) >= qty

    def allocate(self, sku: Sku, qty: int) -> None:
        """Reserve/consume stock. Invariant: never below zero."""
        if not self.can_fulfill(sku, qty):
            raise OutOfStock(f"requested {qty} of {sku} exceeds availability {self.available(sku)}")
        self._on_hand[sku] = self.available(sku) - qty
