from __future__ import annotations


class DomainError(Exception):
    """Base class for domain-level errors."""


class ValidationError(DomainError):
    """Generic validation failure."""


class CurrencyMismatch(DomainError):
    """Tried to combine values with different currencies."""


class OutOfStock(DomainError):
    """Insufficient inventory to fulfill a request."""


class NegativeQuantity(DomainError):
    """Quantity must be positive."""


class OrderStateError(DomainError):
    """Invalid operation for current order state."""

