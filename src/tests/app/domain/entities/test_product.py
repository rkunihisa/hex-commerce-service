from hex_commerce_service.app.domain.entities import Product
from hex_commerce_service.app.domain.errors import ValidationError
from hex_commerce_service.app.domain.value_objects import Money

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

def test_eq() -> None:
    # arrange
    product1 = Product(sku="SKU123", name="test", unit_price=Money.from_major(1000, "JPY"))
    product2 = Product(sku="SKU123", name="test", unit_price=Money.from_major(1000, "JPY"))
    product3 = Product(sku="SKU124", name="test", unit_price=Money.from_major(1000, "JPY"))
    # act/assert
    assert product1 == product2
    assert product1 != product3


def test_eq_notimplemented() -> None:
    # arrange
    product1 = Product(sku="SKU123", name="test", unit_price=Money.from_major(1000, "JPY"))
    not_product = "not a product"
    # act
    result = product1.__eq__(not_product)
    # assert
    assert result is NotImplemented

def test_hash() -> None:
    # arrange
    product1 = Product(sku="SKU123", name="test", unit_price=Money.from_major(1000, "JPY"))
    product2 = Product(sku="SKU123", name="other", unit_price=Money.from_major(2000, "JPY"))
    product3 = Product(sku="SKU124", name="test", unit_price=Money.from_major(1000, "JPY"))
    # act/assert
    assert hash(product1) == hash(product2)  # SKUが同じならハッシュも同じ
    assert hash(product1) != hash(product3)  # SKUが異なればハッシュも異なる
