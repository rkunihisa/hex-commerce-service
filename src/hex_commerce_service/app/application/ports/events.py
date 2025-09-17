from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from collections.abc import Iterable


@runtime_checkable
class EventPublisher(Protocol):
    def publish(self, event: object) -> None: ...
    def publish_many(self, events: Iterable[object]) -> None: ...
