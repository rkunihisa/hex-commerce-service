from hex_commerce_service.app.domain.value_objects.order_id import OrderId

import pytest
from uuid import UUID

def test_new() -> None:
    # arrange
    order_id = OrderId.new()
    # act
    result = order_id.value
    # assert
    assert isinstance(result, UUID)
    # UUID version 4
    assert result.version == 4

def test_parse_valid_uuid() -> None:
    # arrange
    uuid_str = "123e4567-e89b-12d3-a456-426614174000"
    # act
    order_id = OrderId.parse(uuid_str)
    # assert
    assert isinstance(order_id.value, UUID)
    assert str(order_id.value) == uuid_str

def test_parse_invalid_uuid() -> None:
    # act
    with pytest.raises(ValueError) as excinfo:
        OrderId.parse("not-a-uuid")
    # assert
    assert "invalid order id: 'not-a-uuid'" in str(excinfo.value)

def test_str_returns_uuid_string() -> None:
    # arrange
    uuid_str = "123e4567-e89b-12d3-a456-426614174000"
    order_id = OrderId.parse(uuid_str)
    # act
    result = str(order_id)
    # assert
    assert result == uuid_str
