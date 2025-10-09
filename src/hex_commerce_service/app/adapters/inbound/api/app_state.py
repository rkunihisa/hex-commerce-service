from __future__ import annotations

import structlog


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    return structlog.get_logger(name or "app")
