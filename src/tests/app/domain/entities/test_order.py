import pytest
from hex_commerce_service.app.domain.entities import OrderLine, Order
from hex_commerce_service.app.domain.errors import NegativeQuantity, ValidationError, CurrencyMismatch
from hex_commerce_service.app.domain.value_objects import Money

def make_orderline(sku: str = "SKU123", quantity: int = 1, unit_price: int = 1000, currency: str = "JPY") -> OrderLine:
    return OrderLine(sku=sku, quantity=quantity, unit_price=Money.from_major(unit_price, currency))

def make_order(id: str = "SKU123", currency: str = "JPY", lines: list[OrderLine] | None = None) -> Order:
    if lines is None:
        lines = []
    return Order(id=id, currency=currency, lines=lines)

def test_orderline_valid() -> None:
    line = make_orderline(quantity=2)
    assert line.sku == "SKU123"
    assert line.quantity == 2
    assert line.unit_price.amount == 1000

def test_orderline_invalid_quantity() -> None:
    with pytest.raises(NegativeQuantity, match="order line quantity must be positive"):
        make_orderline(quantity=0)

def test_orderline_line_total() -> None:
    line = make_orderline(quantity=3, unit_price=100)
    assert line.line_total == Money.from_major(300, "JPY")

def test_order_valid() -> None:
    order = make_order(lines=[make_orderline(quantity=2)])
    assert order.id == "SKU123"
    assert order.currency == "JPY"
    assert len(order.lines) == 1

@pytest.mark.parametrize("value", ["product", "円", "US$", "123"])
def test_order_invalid_currency(value: str) -> None:
    with pytest.raises(ValidationError, match="order.currency must be 3 uppercase letters"):
        make_order(currency=value, lines=[make_orderline(quantity=2)])

def test_order_eq() -> None:
    order1 = make_order()
    order2 = make_order()
    order3 = make_order(id="SKU124")
    assert order1 == order2
    assert order1 != order3
    assert hash(order1) == hash(order2)
    assert hash(order1) != hash(order3)

def test_eq_notimplemented() -> None:
    order1 = make_order()
    not_order = "not an order"
    result = order1.__eq__(not_order)
    assert result is NotImplemented

def test_order_valid_add_line() -> None:
    order = make_order(lines=[make_orderline()])
    line = make_orderline(quantity=2, unit_price=2000)
    order.add_line(line)
    assert len(order.lines) == 2
    assert order.lines[1] == line

def test_order_invalid_add_line() -> None:
    order = make_order(lines=[make_orderline()])
    line = make_orderline(quantity=2, unit_price=2000, currency="USD")
    with pytest.raises(CurrencyMismatch, match="line currency must match order currency"):
        order.add_line(line)

def test_order_valid_add_item() -> None:
    order = make_order(lines=[])
    order.add_item(sku="SKU123", quantity=3, unit_price=Money.from_major(1500, "JPY"))
    assert len(order.lines) == 1
    line = order.lines[0]
    assert line.sku == "SKU123"
    assert line.quantity == 3
    assert line.unit_price == Money.from_major(1500, "JPY")

def test_order_invalid_add_item() -> None:
    order = make_order(lines=[])
    with pytest.raises(CurrencyMismatch, match="unit price currency must match order currency"):
        order.add_item(sku="SKU123", quantity=3, unit_price=Money.from_major(1500, "USD"))

def test_order_valid_remove_line_at() -> None:
    line1 = make_orderline()
    line2 = make_orderline(sku="SKU124", quantity=2, unit_price=2000)
    order = make_order(lines=[line1, line2])
    removed_line = order.remove_line_at(0)
    assert removed_line == line1
    assert len(order.lines) == 1
    assert order.lines[0] == line2

def test_order_invalid_remove_line_at() -> None:
    line1 = make_orderline()
    line2 = make_orderline(sku="SKU124", quantity=2, unit_price=2000)
    order = make_order(lines=[line1, line2])
    with pytest.raises(ValidationError, match="no order line at index 2"):
        order.remove_line_at(2)

def test_order_total() -> None:
    line1 = make_orderline(quantity=1, unit_price=1000)
    line2 = make_orderline(sku="SKU124", quantity=2, unit_price=2000)
    order = make_order(lines=[line1, line2])
    assert order.total == Money.from_major(5000, "JPY")

def test_order_iterate_skus() -> None:
    line1 = make_orderline(quantity=1, unit_price=1000)
    line2 = make_orderline(sku="SKU124", quantity=2, unit_price=2000)
    order = make_order(lines=[line1, line2])
    skus = list(order.iterate_skus())
    assert skus == ["SKU123", "SKU124"]
