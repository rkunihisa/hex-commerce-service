from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from fastapi import Request, Response

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from hex_commerce_service.app.adapters.inbound.api.app_state import get_logger
from hex_commerce_service.app.config.settings import get_settings

REQUEST_ID_KEY = "request_id"
CORRELATION_ID_KEY = "correlation_id"


def _ensure_id(value: str | None) -> str:
    try:
        if value and value.strip():
            return value.strip()
    except Exception:
        structlog.get_logger("request_context").exception("Exception in _ensure_id")
    return str(uuid.uuid4())


class RequestContextMiddleware(BaseHTTPMiddleware):
    @staticmethod
    async def dispatch(request: Request, call_next: RequestResponseEndpoint) -> Response:
        settings = get_settings()
        req_id = _ensure_id(request.headers.get(settings.request_id_header))
        corr_id = _ensure_id(request.headers.get(settings.correlation_id_header) or request.headers.get(settings.request_id_header))

        # Bind to structlog contextvars
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=req_id,
            correlation_id=corr_id,
            path=request.url.path,
            method=request.method,
        )

        logger = get_logger("request")
        logger.info("request_started")

        try:
            response = await call_next(request)
        except Exception:
            logger.exception("request_failed")
            raise

        # Propagate IDs to response headers
        response.headers[settings.request_id_header] = req_id
        response.headers[settings.correlation_id_header] = corr_id

        logger.info("request_finished", status_code=response.status_code)
        return response
