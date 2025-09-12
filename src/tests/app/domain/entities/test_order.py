from hex_commerce_service.app.domain.entities import OrderLine,Order
from hex_commerce_service.app.domain.errors import NegativeQuantity, ValidationError, CurrencyMismatch
from hex_commerce_service.app.domain.value_objects import Money

import pytest

def test_orderline_valid() -> None:
    line = OrderLine(sku="SKU123", quantity=2, unit_price=Money.from_major(1000, "JPY"))
    assert line.sku == "SKU123"
    assert line.quantity == 2
    assert line.unit_price.amount == 1000

def test_orderline_invalid_quantity() -> None:
    with pytest.raises(NegativeQuantity) as excinfo:
        OrderLine(sku="SKU123", quantity=0, unit_price=Money.from_major(1000, "JPY"))
    assert "order line quantity must be positive" in str(excinfo.value)

def test_orderline_line_total() -> None:
    line = OrderLine(sku="SKU123", quantity=3, unit_price=Money.from_major(100, "JPY"))
    assert line.line_total == Money.from_major(300, "JPY")

def test_order_valid() -> None:
    line = Order(id="SKU123", currency="JPY", lines=[OrderLine(sku="SKU123", quantity=2, unit_price=Money.from_major(1000, "JPY"))])
    assert line.id == "SKU123"
    assert line.currency == "JPY"
    assert len(line.lines) == 1

@pytest.mark.parametrize("value", [
    ("product"),("円"),("US$"),("123")
])
def test_order_invalid_currency(value: str) -> None:
    with pytest.raises(ValidationError) as excinfo:
        Order(id="SKU123", currency=value, lines=[OrderLine(sku="SKU123", quantity=2, unit_price=Money.from_major(1000, "JPY"))])
    assert "order.currency must be 3 uppercase letters" in str(excinfo.value)

def test_order_eq() -> None:
    order1 = Order(id="SKU123", currency="JPY")
    order2 = Order(id="SKU123", currency="JPY")
    order3 = Order(id="SKU124", currency="JPY")
    assert order1 == order2
    assert order1 != order3
    assert hash(order1) == hash(order2)
    assert hash(order1) != hash(order3)

def test_eq_notimplemented() -> None:
    # arrange
    order1 = Order(id="SKU123", currency="JPY")
    not_order = "not an order"
    # act
    result = order1.__eq__(not_order)
    # assert
    assert result is NotImplemented

def test_order_valid_add_line() -> None:
    order = Order(id="SKU123", currency="JPY", lines=[OrderLine(sku="SKU123", quantity=1, unit_price=Money.from_major(1000, "JPY"))])
    line = OrderLine(sku="SKU123", quantity=2, unit_price=Money.from_major(2000, "JPY"))
    order.add_line(line)
    assert len(order.lines) == 2
    assert order.lines[1] == line

def test_order_invalid_add_line() -> None:
    order = Order(id="SKU123", currency="JPY", lines=[OrderLine(sku="SKU123", quantity=1, unit_price=Money.from_major(1000, "JPY"))])
    line = OrderLine(sku="SKU123", quantity=2, unit_price=Money.from_major(2000, "USD"))
    with pytest.raises(CurrencyMismatch) as excinfo:
        order.add_line(line)
    assert "line currency must match order currency" in str(excinfo.value)

def test_order_valid_add_item() -> None:
    order = Order(id="SKU123", currency="JPY", lines=[])
    order.add_item(sku="SKU123", quantity=3, unit_price=Money.from_major(1500, "JPY"))
    assert len(order.lines) == 1
    line = order.lines[0]
    assert line.sku == "SKU123"
    assert line.quantity == 3
    assert line.unit_price == Money.from_major(1500, "JPY")

def test_order_invalid_add_item() -> None:
    order = Order(id="SKU123", currency="JPY", lines=[])
    with pytest.raises(CurrencyMismatch) as excinfo:
        order.add_item(sku="SKU123", quantity=3, unit_price=Money.from_major(1500, "USD"))
    assert "unit price currency must match order currency" in str(excinfo.value)

def test_order_valid_remove_line_at() -> None:
    line1 = OrderLine(sku="SKU123", quantity=1, unit_price=Money.from_major(1000, "JPY"))
    line2 = OrderLine(sku="SKU124", quantity=2, unit_price=Money.from_major(2000, "JPY"))
    order = Order(id="SKU123", currency="JPY", lines=[line1, line2])
    removed_line = order.remove_line_at(0)
    assert removed_line == line1
    assert len(order.lines) == 1
    assert order.lines[0] == line2

def test_order_invalid_remove_line_at() -> None:
    line1 = OrderLine(sku="SKU123", quantity=1, unit_price=Money.from_major(1000, "JPY"))
    line2 = OrderLine(sku="SKU124", quantity=2, unit_price=Money.from_major(2000, "JPY"))
    order = Order(id="SKU123", currency="JPY", lines=[line1, line2])
    with pytest.raises(ValidationError) as excinfo:
        order.remove_line_at(2)
    assert "no order line at index 2" in str(excinfo.value)

def test_order_total() -> None:
    line1 = OrderLine(sku="SKU123", quantity=1, unit_price=Money.from_major(1000, "JPY"))
    line2 = OrderLine(sku="SKU124", quantity=2, unit_price=Money.from_major(2000, "JPY"))
    order = Order(id="SKU123", currency="JPY", lines=[line1, line2])
    assert order.total == Money.from_major(5000, "JPY")

def test_order_iterate_skus() -> None:
    line1 = OrderLine(sku="SKU123", quantity=1, unit_price=Money.from_major(1000, "JPY"))
    line2 = OrderLine(sku="SKU124", quantity=2, unit_price=Money.from_major(2000, "JPY"))
    order = Order(id="SKU123", currency="JPY", lines=[line1, line2])
    skus = list(order.iterate_skus())
    assert skus == ["SKU123", "SKU124"]
