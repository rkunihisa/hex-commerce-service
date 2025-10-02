from __future__ import annotations

from fastapi import HTTPException, status

from hex_commerce_service.app.domain.errors import (
    CurrencyMismatchError,
    DomainError,
    OutOfStockError,
    ValidationError,
)


def to_http(exc: Exception) -> HTTPException:
    if isinstance(exc, OutOfStockError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, CurrencyMismatchError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, ValidationError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if isinstance(exc, DomainError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    # fallback
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="internal error")
