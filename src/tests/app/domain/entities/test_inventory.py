from operator import inv
from hex_commerce_service.app.domain.entities import Inventory
from hex_commerce_service.app.domain.errors import NegativeQuantity, OutOfStock
from hex_commerce_service.app.domain.value_objects import Sku

import pytest

def test_inventory_eq() -> None:
    inventory1 = Inventory(location="japan")
    inventory2 = Inventory(location="japan")
    inventory3 = Inventory(location="usa")
    assert inventory1 == inventory2
    assert inventory1 != inventory3
    assert hash(inventory1) == hash(inventory2)
    assert hash(inventory1) != hash(inventory3)

def test_eq_notimplemented() -> None:
    # arrange
    inventory1 = Inventory(location="japan")
    not_inventory = "not an inventory"
    # act
    result = inventory1.__eq__(not_inventory)
    # assert
    assert result is NotImplemented

@pytest.mark.parametrize("sku, expected", [
    (Sku("SKU1"), 10),
    (Sku("SKU2"), 0),
])
def test_inventory_available(sku: Sku, expected: int) -> None:
    # arrange
    inventory = Inventory(location="japan", _on_hand={Sku("SKU1"): 10})
    # act
    result = inventory.available(sku)
    # assert
    assert result == expected

@pytest.mark.parametrize("sku, qty, expected", [
    (Sku("SKU1"), 10, 2)
])
def test_inventory_valid_set_on_hand(sku: Sku, qty:int, expected: int) -> None:
    # arrange
    inventory = Inventory(location="japan", _on_hand={Sku("SKU0"): 10})
    # act
    inventory.set_on_hand(sku, qty)
    # assert
    assert inventory.available(sku) == qty
    assert len(inventory._on_hand) == expected

@pytest.mark.parametrize("inventory, sku, qty, expected", [
    (Inventory(location="japan", _on_hand={Sku("SKU0"): 10}), Sku("SKU0"), 10, 20),
    (Inventory(location="japan", _on_hand={Sku("SKU0"): 5}), Sku("SKU1"), 5, 5),
])
def test_inventory_valid_add(inventory: Inventory, sku: Sku, qty:int, expected: int) -> None:
    # act
    inventory.add(sku, qty)
    # assert
    assert inventory.available(sku) == expected

