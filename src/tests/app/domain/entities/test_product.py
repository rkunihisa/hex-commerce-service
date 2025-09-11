from hex_commerce_service.app.domain.entities.product import Product
from hex_commerce_service.app.domain.errors import ValidationError
from hex_commerce_service.app.domain.value_objects.money import Money

import pytest

@pytest.mark.parametrize("value, expected", [
    ("product", "product"),
    ("product name", "product name"),
    ("  product name  ", "product name"),
])
def test_rename(value: str, expected: str) -> None:
    # arrange
    product = Product(sku="SKU123", name="test", unit_price=Money.from_major(1000, "JPY"))
    # act
    product.rename(value)
    # assert
    assert product.name == expected

@pytest.mark.parametrize("value", [
    (""),  # empty string
    ("   "),  # whitespace
    ("\n"),  # newline
])
def test_rename_invalid(value: str) -> None:
    # arrange
    product = Product(sku="SKU123", name="test", unit_price=Money.from_major(1000, "JPY"))
    # act
    with pytest.raises(ValidationError) as excinfo:
        product.rename(value)
    # assert
    assert "product name must not be empty" in str(excinfo.value)

@pytest.mark.parametrize("value, expected", [
    (Money.from_major(1000, "JPY"), (Money.from_major(1000, "JPY"))),
])
def test_change_price(value: Money, expected: Money) -> None:
    # arrange
    product = Product(sku="SKU123", name="test", unit_price=Money.from_major(1000, "JPY"))
    # act
    product.change_price(value)
    # assert
    assert product.unit_price == expected

@pytest.mark.parametrize("value", [
    (Money.from_major(0, "JPY")),
])
def test_change_price_invalid(value: Money) -> None:
    # arrange
    product = Product(sku="SKU123", name="test", unit_price=Money.from_major(1000, "JPY"))
    # act
    with pytest.raises(ValidationError) as excinfo:
        product.change_price(value)
    # assert
    assert "unit price must be positive" in str(excinfo.value)
