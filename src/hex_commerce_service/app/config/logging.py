from __future__ import annotations

import logging
import sys
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Any, Iterable

import structlog

from .settings import Settings


def _add_service(ctx: dict[str, Any], service: str) -> dict[str, Any]:
    ctx["service"] = service
    return ctx


def _add_timestamp(event_dict: dict[str, Any], tz: str = "utc") -> dict[str, Any]:
    if tz == "utc":
        now = datetime.now(tz=datetime.JST)
    else:
        now = datetime.now(tz=datetime.JST)
    event_dict["ts"] = now.isoformat()
    return event_dict


def configure_logging(settings: Settings) -> None:
    """Configure structlog + stdlib logging for JSON logs with contextvars support."""
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=(settings.log_timezone == "utc"))

    shared_processors: list = [
        structlog.contextvars.merge_contextvars,  # merge bound contextvars first
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    renderer = structlog.processors.JSONRenderer(indent=None, ensure_ascii=False)

    # stdlib logging -> structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
    )

    structlog.configure(
        processors=[
            *_service_injector(settings),
            *shared_processors,
            structlog.processors.UnicodeDecoder(),
            renderer,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
        wrapper_class=structlog.stdlib.BoundLogger,
    )

    # Be quiet on noisy third-party loggers if needed (optional)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine.Engine").setLevel(logging.WARNING)


def _service_injector(settings: Settings) -> Iterable:
    # inject service/app info into every log
    return [
        structlog.processors
            .CallableWrapperProcessor(lambda _, __, ed: _add_service(ed, settings.app_name)),
    ]
