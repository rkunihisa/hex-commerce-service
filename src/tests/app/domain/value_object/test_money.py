from decimal import Decimal
import pytest
from hex_commerce_service.app.domain.value_object.money import Money

@pytest.mark.parametrize("a, b, expected", [
    (
        Money(amount=Decimal('10.00'), currency='JPY'),
        Money(amount=Decimal('5.00'), currency='JPY'),
        Money(amount=Decimal('5.00'), currency='JPY'),
    ),
    (
        Money(amount=Decimal('1000.00'), currency='JPY'),
        Money(amount=Decimal('10.00'), currency='JPY'),
        Money(amount=Decimal('990.00'), currency='JPY'),
    ),
])
def test_sub(a: Money, b: Money, expected: Money) -> None:
    # act
    result = a - b
    # assert
    assert result == expected

@pytest.mark.parametrize("a, factor, expected", [
    (Money(amount=Decimal('10.00'), currency='JPY'), 2, Money(amount=Decimal('20.00'), currency='JPY')),
    (Money(amount=Decimal('10.00'), currency='JPY'), Decimal('0.5'), Money(amount=Decimal('5.00'), currency='JPY')),
])
def test_mul(a: Money, factor: int | Decimal, expected: Money) -> None:
    # act
    result = a * factor
    # assert
    assert result == expected

@pytest.mark.parametrize("a, divisor, expected", [
    (Money(amount=Decimal('10.00'), currency='JPY'), 2, Money(amount=Decimal('5.00'), currency='JPY')),
    (Money(amount=Decimal('10.00'), currency='JPY'), Decimal('0.5'), Money(amount=Decimal('20.00'), currency='JPY')),
])
def test_truediv(a: Money, divisor: int | Decimal, expected: Money) -> None:
    # act
    result = a / divisor
    # assert
    assert result == expected

def test_truediv_zero() -> None:
    a = Money(amount=Decimal('10.00'), currency='JPY')
    with pytest.raises(ZeroDivisionError):
        a / 0

def test_currency_mismatch() -> None:
    a = Money(amount=Decimal('10.00'), currency='JPY')
    b = Money(amount=Decimal('5.00'), currency='USD')
    with pytest.raises(ValueError):
        _ = a + b
    with pytest.raises(ValueError):
        _ = a - b
    with pytest.raises(ValueError):
        _ = a < b

@pytest.mark.parametrize("a, b, expected", [
    (Money(amount=Decimal('5.00'), currency='JPY'), Money(amount=Decimal('10.00'), currency='JPY'), True),
    (Money(amount=Decimal('10.00'), currency='JPY'), Money(amount=Decimal('5.00'), currency='JPY'), False),
])
def test_lt(a: Money, b: Money, expected: bool) -> None:
    # act
    result = a < b
    # assert
    assert result == expected

@pytest.mark.parametrize("money, expected", [
    (Money(amount=Decimal('10.00'), currency='JPY'), 1000),
    (Money(amount=Decimal('0.01'), currency='JPY'), 1),
    (Money(amount=Decimal('0.00'), currency='JPY'), 0),
])
def test_to_minor(money: Money, expected: int) -> None:
    # act
    result = money.to_minor()
    # assert
    assert result == expected

@pytest.mark.parametrize("money, expected", [
    (Money(amount=Decimal('10.00'), currency='JPY'), "JPY 10.00"),
    (Money(amount=Decimal('0.01'), currency='USD'), "USD 0.01"),
])
def test_str(money: Money, expected: str) -> None:
    # act
    result = str(money)
    # assert
    assert result == expected

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

