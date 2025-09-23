from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable


class MessageBus:
    """
    同期ディスパッチの最小実装.

    - subscribe(type, handler) でイベント型に対するハンドラを登録
    - publish(event) で同型のハンドラを順次呼び出す(例外は握りつぶしてerrorsへ記録)
    """

    def __init__(self) -> None:
        self._handlers: defaultdict[type[Any], list[Callable[[Any], None]]] = defaultdict(list)
        self.errors: list[tuple[object, BaseException]] = []

    def subscribe(self, event_type: type[Any], handler: Callable[[Any], None]) -> None:
        self._handlers[event_type].append(handler)

    def publish(self, event: object) -> None:
        for handler in list(self._handlers.get(type(event), [])):
            try:
                handler(event)
            except BaseException as exc:  # ここでは例外を潰して記録(PlaceOrder成功を阻害しない)
                self.errors.append((event, exc))
