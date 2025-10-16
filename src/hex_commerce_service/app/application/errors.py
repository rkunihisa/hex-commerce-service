from __future__ import annotations


class ApplicationError(Exception):
    """Base class for application-layer errors."""


class ExternalServiceError(ApplicationError):
    """Base class for external service failures."""


class TransientExternalError(ExternalServiceError):
    """Retryable error (network glitch, 5xx, timeouts)."""


class PermanentExternalError(ExternalServiceError):
    """Non-retryable error (invalid card, 4xx semantic)."""


class CircuitOpenError(ExternalServiceError):
    """Circuit breaker is open; requests are short-circuited."""
