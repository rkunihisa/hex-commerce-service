from decimal import Decimal
from hex_commerce_service.app.domain.value_object.money import Money

import pytest

@pytest.mark.parametrize("amount, currency, expected", [
    (10.00, "JPY", Money(amount=Decimal('10.00'), currency='JPY')),
    (1000, "JPY", Money(amount=Decimal('1000.00'), currency='JPY')),
    ("1000", "JPY", Money(amount=Decimal('1000.00'), currency='JPY')),
])
def test_from_major(amount: Decimal | int | str, currency: str, expected: Money) -> None:
    # act
    result = Money.from_major(amount, currency)
    # assert
    assert result == expected

@pytest.mark.parametrize("amount, currency, expected", [
    (10.00, "JPY", Money(amount=Decimal('0.10'), currency='JPY')),
    (1000, "JPY", Money(amount=Decimal('10.00'), currency='JPY')),
    ("1000", "JPY", Money(amount=Decimal('10.00'), currency='JPY')),
])
def test_from_minor(amount: Decimal | int | str, currency: str, expected: Money) -> None:
    # act
    result = Money.from_minor(amount, currency)
    # assert
    assert result == expected

@pytest.mark.parametrize("a, b, expected", [
    (
        Money(amount=Decimal('10.00'), currency='JPY'),
        Money(amount=Decimal('5.00'), currency='JPY'),
        Money(amount=Decimal('15.00'), currency='JPY'),
    ),
    (
        Money(amount=Decimal('1000.00'), currency='JPY'),
        Money(amount=Decimal('10.00'), currency='JPY'),
        Money(amount=Decimal('1010.00'), currency='JPY'),
    ),
])
def test_add(a: Money, b: Money, expected: Money) -> None:
    # act
    result = a + b
    # assert
    assert result == expected

