from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class EventPublisher(Protocol):
    def publish(self, event: object) -> None: ...
