import pytest

from hex_commerce_service.app.domain.entities import Inventory
from hex_commerce_service.app.domain.errors import NegativeQuantityError, OutOfStockError
from hex_commerce_service.app.domain.value_objects import Sku


def make_inventory(on_hand: dict[Sku, int] | None = None, location: str = "japan") -> Inventory:
    if on_hand is None:
        on_hand = {}
    return Inventory(location=location, _on_hand=on_hand)


def test_inventory_eq_and_hash() -> None:
    inv1 = make_inventory(location="japan")
    inv2 = make_inventory(location="japan")
    inv3 = make_inventory(location="usa")
    assert inv1 == inv2
    assert inv1 != inv3
    assert hash(inv1) == hash(inv2)
    assert hash(inv1) != hash(inv3)


def test_eq_notimplemented() -> None:
    inv = make_inventory()
    assert inv.__eq__("not an inventory") is NotImplemented


@pytest.mark.parametrize(
    "sku, expected",
    [
        (Sku("SKU1"), 10),
        (Sku("SKU2"), 0),
    ],
)
def test_inventory_available(sku: Sku, expected: int) -> None:
    inv = make_inventory({Sku("SKU1"): 10})
    assert inv.available(sku) == expected


def test_inventory_set_on_hand_valid() -> None:
    inv = make_inventory({Sku("SKU0"): 10})
    inv.set_on_hand(Sku("SKU1"), 5)
    assert inv.available(Sku("SKU1")) == 5
    assert len(inv._on_hand) == 2


def test_inventory_set_on_hand_invalid() -> None:
    inv = make_inventory({Sku("SKU0"): 10})
    with pytest.raises(NegativeQuantityError, match="on-hand cannot be negative"):
        inv.set_on_hand(Sku("SKU0"), -5)


@pytest.mark.parametrize(
    "start, sku, qty, expected",
    [
        ({Sku("SKU0"): 10}, Sku("SKU0"), 10, 20),
        ({Sku("SKU0"): 5}, Sku("SKU1"), 5, 5),
    ],
)
def test_inventory_add(start: dict[Sku, int], sku: Sku, qty: int, expected: int) -> None:
    inv = make_inventory(start)
    inv.add(sku, qty)
    assert inv.available(sku) == expected


def test_inventory_add_invalid() -> None:
    inv = make_inventory({Sku("SKU0"): 10})
    with pytest.raises(NegativeQuantityError, match="add quantity must be positive"):
        inv.add(Sku("SKU0"), -5)


def test_inventory_remove_valid() -> None:
    inv = make_inventory({Sku("SKU0"): 10})
    inv.remove(Sku("SKU0"), 5)
    assert inv.available(Sku("SKU0")) == 5


def test_inventory_remove_invalid_negative() -> None:
    inv = make_inventory({Sku("SKU0"): 10})
    with pytest.raises(NegativeQuantityError, match="remove quantity must be positive"):
        inv.remove(Sku("SKU0"), -5)


def test_inventory_remove_invalid_out_of_stock() -> None:
    inv = make_inventory({Sku("SKU0"): 10})
    with pytest.raises(OutOfStockError, match="cannot remove 15; only 10 available"):
        inv.remove(Sku("SKU0"), 15)


@pytest.mark.parametrize(
    "start, sku, qty, expected",
    [
        ({Sku("SKU0"): 10}, Sku("SKU0"), 1, True),
        ({Sku("SKU0"): 1}, Sku("SKU1"), 10, False),
    ],
)
def test_inventory_can_fulfill(start: dict[Sku, int], sku: Sku, qty: int, expected: bool) -> None:
    inv = make_inventory(start)
    assert inv.can_fulfill(sku, qty) == expected


def test_inventory_can_fulfill_invalid() -> None:
    inv = make_inventory({Sku("SKU0"): 10})
    with pytest.raises(NegativeQuantityError, match="requested quantity must be positive"):
        inv.can_fulfill(Sku("SKU0"), -5)


def test_inventory_allocate_valid() -> None:
    inv = make_inventory({Sku("SKU0"): 10})
    inv.allocate(Sku("SKU0"), 5)
    assert inv.available(Sku("SKU0")) == 5


def test_inventory_allocate_invalid_out_of_stock() -> None:
    inv = make_inventory({Sku("SKU0"): 10})
    with pytest.raises(OutOfStockError, match="requested 15 of SKU0 exceeds availability 10"):
        inv.allocate(Sku("SKU0"), 15)
