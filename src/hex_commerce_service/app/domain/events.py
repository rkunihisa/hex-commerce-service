from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True, slots=True)
class DomainEvent:
    """ドメインイベントの基底。発生時刻のみを持つ最小構成。"""
    occurred_at: datetime

    @staticmethod
    def now() -> datetime:
        return datetime.now(tz=timezone.utc)
