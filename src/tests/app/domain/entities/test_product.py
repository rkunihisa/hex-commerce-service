import pytest

from hex_commerce_service.app.domain.entities import Product
from hex_commerce_service.app.domain.errors import ValidationError
from hex_commerce_service.app.domain.value_objects import Money


def make_product(
    sku: str = "SKU123", name: str = "test", unit_price: int = 1000, currency: str = "JPY"
) -> Product:
    return Product(sku=sku, name=name, unit_price=Money.from_major(unit_price, currency))


@pytest.mark.parametrize(
    "value, expected",
    [
        ("product", "product"),
        ("product name", "product name"),
        ("  product name  ", "product name"),
    ],
)
def test_rename(value: str, expected: str) -> None:
    product = make_product()
    product.rename(value)
    assert product.name == expected


@pytest.mark.parametrize("value", ["", "   ", "\n"])
def test_rename_invalid(value: str) -> None:
    product = make_product()
    with pytest.raises(ValidationError, match="product name must not be empty"):
        product.rename(value)


@pytest.mark.parametrize(
    "value, expected",
    [
        (Money.from_major(1000, "JPY"), Money.from_major(1000, "JPY")),
    ],
)
def test_change_price(value: Money, expected: Money) -> None:
    product = make_product()
    product.change_price(value)
    assert product.unit_price == expected


@pytest.mark.parametrize("value", [Money.from_major(0, "JPY")])
def test_change_price_invalid(value: Money) -> None:
    product = make_product()
    with pytest.raises(ValidationError, match="unit price must be positive"):
        product.change_price(value)


def test_eq() -> None:
    product1 = make_product(sku="SKU123")
    product2 = make_product(sku="SKU123")
    product3 = make_product(sku="SKU124")
    assert product1 == product2
    assert product1 != product3


def test_eq_notimplemented() -> None:
    product1 = make_product()
    not_product = "not a product"
    result = product1.__eq__(not_product)
    assert result is NotImplemented


def test_hash() -> None:
    product1 = make_product(sku="SKU123", name="test", unit_price=1000)
    product2 = make_product(sku="SKU123", name="other", unit_price=2000)
    product3 = make_product(sku="SKU124", name="test", unit_price=1000)
    assert hash(product1) == hash(product2)  # SKUが同じならハッシュも同じ
    assert hash(product1) != hash(product3)  # SKUが異なればハッシュも異なる
