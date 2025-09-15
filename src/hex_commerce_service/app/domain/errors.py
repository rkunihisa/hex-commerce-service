from __future__ import annotations


class DomainError(Exception):
    """Base class for domain-level errors."""


class ValidationError(DomainError):
    """Generic validation failure."""


class CurrencyMismatchError(DomainError):
    """Tried to combine values with different currencies."""


class OutOfStockError(DomainError):
    """Insufficient inventory to fulfill a request."""


class NegativeQuantityError(DomainError):
    """Quantity must be positive."""


class OrderStateError(DomainError):
    """Invalid operation for current order state."""
