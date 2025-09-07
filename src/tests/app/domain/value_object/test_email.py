from hex_commerce_service.app.domain.value_object.email import Email

import pytest

@pytest.mark.parametrize("email, expected", [
    ("user@example.com", "user"),
    ("USER@EXAMPLE.COM", "user"),
    ("user.name+tag+sorting@example.com", "user.name+tag+sorting"),
    ("user_name@example.co.jp", "user_name"),
    ("user-name@sub.example.com", "user-name"),
    ("a@b.co", "a"),
])
def test_local(email: str, expected: str) -> None:
    # arrange
    target = Email(email)
    # act
    result = target.local
    # assert
    assert result == expected

@pytest.mark.parametrize("email, expected", [
    ("user@example.com", "example.com"),
    ("USER@EXAMPLE.COM", "example.com"),
    ("user.name+tag+sorting@example.com", "example.com"),
    ("user_name@example.co.jp", "example.co.jp"),
    ("user-name@sub.example.com", "sub.example.com"),
    ("a@b.co", "b.co"),
])
def test_domain(email: str, expected: str) -> None:
    # arrange
    target = Email(email)
    # act
    result = target.domain
    # assert
    assert result == expected

@pytest.mark.parametrize("email, expected", [
    ("user@example.com", "user@example.com"),
    ("USER@EXAMPLE.COM", "user@example.com"),
])
def test_str(email: str, expected: str) -> None:
    # arrange
    target = Email(email)
    # act
    result = str(target)
    # assert
    assert result == expected

@pytest.mark.parametrize("email, expected", [
    ("plainaddress", "invalid email: 'plainaddress'"),
    ("@missinglocal.org", "invalid email: '@missinglocal.org'"),
    ("username@", "invalid email: 'username@'"),
    ("username@.com", "invalid email: 'username@.com'"),
    ("username@.com.", "invalid email: 'username@.com.'"),
    ("username@-example.com", "invalid email: 'username@-example.com'"),
    ("username@example..com", "invalid email: 'username@example..com'"),
])
def test_invalid_email(email: str, expected: str) -> None:
    # arrange
    try:
        target = Email(email)
    except ValueError as e:
        # assert
        assert str(e) == expected
