from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class DomainEvent:
    occurred_at: datetime

    @staticmethod
    def now() -> datetime:
        return datetime.now(tz=UTC)
