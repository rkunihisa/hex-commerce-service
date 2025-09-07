from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class OrderId:
    value: UUID

    @classmethod
    def new(cls) -> OrderId:
        return cls(uuid4())

    @classmethod
    def parse(cls, value: str) -> OrderId:
        try:
            return cls(UUID(value))
        except Exception as exc:  # noqa: BLE001 - broad for parse robustness
            msg = f"invalid order id: {value!r}"
            raise ValueError(msg) from exc

    def __str__(self) -> str:
        return str(self.value)
