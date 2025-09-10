from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
from functools import total_ordering
from typing import Any, ClassVar, NewType

CurrencyCode = NewType("CurrencyCode", str)


def _validate_currency(code: str) -> CurrencyCode:
    if len(code) != 3 or not code.isalpha() or not code.isupper():
        msg = "currency must be 3 uppercase letters (ISO 4217-like)"
        raise ValueError(msg)
    return CurrencyCode(code)


def _coerce_decimal(value: Decimal | int | str) -> Decimal:
    try:
        if isinstance(value, Decimal):
            d = value
        else:
            d = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        msg = f"invalid decimal value: {value!r}"
        raise ValueError(msg) from exc
    if d.is_nan() or d.is_infinite():
        msg = "amount must be a finite number"
        raise ValueError(msg)
    return d


@total_ordering
@dataclass(frozen=True, slots=True)
class Money:
    """A value object representing a monetary amount in a specific currency."""

    amount: Decimal
    currency: CurrencyCode

    _QUANT: ClassVar[Decimal] = Decimal("0.01")
    _ROUNDING: ClassVar[Any] = ROUND_HALF_EVEN  # typing-only: decimal.Rounding

    def __post_init__(self) -> None:
        cur = _validate_currency(str(self.currency))
        object.__setattr__(self, "currency", cur)

        amt = _coerce_decimal(self.amount)
        q = amt.quantize(self._QUANT, rounding=self._ROUNDING)
        object.__setattr__(self, "amount", q)

    @classmethod
    def from_major(cls, amount: Decimal | int | str, currency: str) -> Money:
        return cls(amount=_coerce_decimal(amount), currency=_validate_currency(currency))

    @classmethod
    def from_minor(cls, minor: int, currency: str) -> Money:
        major = Decimal(minor) / Decimal(100)
        return cls(amount=major, currency=_validate_currency(currency))

    # Basic arithmetic (same-currency only)
    def _ensure_same_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            msg = "currency mismatch"
            raise ValueError(msg)

    def _new(self, amount: Decimal) -> Money:
        return Money(amount=amount, currency=self.currency)

    def __add__(self, other: Money) -> Money:
        self._ensure_same_currency(other)
        return self._new(self.amount + other.amount)

    def __sub__(self, other: Money) -> Money:
        self._ensure_same_currency(other)
        return self._new(self.amount - other.amount)

    def __mul__(self, factor: int | Decimal) -> Money:
        d = _coerce_decimal(Decimal(factor))
        return self._new(self.amount * d)

    def __truediv__(self, divisor: int | Decimal) -> Money:
        d = _coerce_decimal(Decimal(divisor))
        if d == 0:
            raise ZeroDivisionError("division by zero")
        return self._new(self.amount / d)

    # Ordering (only meaningful within same currency)
    def __lt__(self, other: Money) -> bool:
        self._ensure_same_currency(other)
        return self.amount < other.amount

    # Useful conversions
    def to_minor(self) -> int:
        return int((self.amount * 100).to_integral_value(rounding=self._ROUNDING))

    def __str__(self) -> str:
        return f"{self.currency} {self.amount:.2f}"
