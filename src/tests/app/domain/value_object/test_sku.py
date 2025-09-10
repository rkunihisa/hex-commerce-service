import pytest
from hex_commerce_service.app.domain.value_objects.sku import Sku

@pytest.mark.parametrize("value,expected", [
    ("A", "A"),
    ("SKU123", "SKU123"),
    ("SKU-123", "SKU-123"),
    ("SKU_123", "SKU_123"),
    ("A234567890123456789012345678901234567890123456789012345678901234", "A234567890123456789012345678901234567890123456789012345678901234"),
    ("aBc-123_xyz", "ABC-123_XYZ"),
    ("  sku_1  ", "SKU_1"),
])
def test_valid_sku(value: str, expected: str) -> None:
    # act
    s = Sku(value)
    # assert
    assert s.value == expected
    assert str(s) == expected


@pytest.mark.parametrize("value", [
    "",  # 空
    "-SKU",  # 先頭が記号
    "_SKU",  # 先頭が記号
    "sku@123",  # 許可されていない記号
    "A" * 65,  # 65文字
])
def test_invalid_sku(value: str) -> None:
    # act/assert
    with pytest.raises(ValueError) as excinfo:
        Sku(value)
    assert "invalid sku (use A-Z, 0-9, -, _, length 1..64; must start with alnum)" in str(excinfo.value)
