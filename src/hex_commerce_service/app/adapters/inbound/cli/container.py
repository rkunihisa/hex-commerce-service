from __future__ import annotations

from dataclasses import dataclass

from hex_commerce_service.app.adapters.inmemory.system import (
    InMemoryIdGenerator,
    InMemoryUnitOfWork,
)
from hex_commerce_service.app.application.message_bus import MessageBus


@dataclass(slots=True)
class CLIServices:
    uow: InMemoryUnitOfWork
    id_gen: InMemoryIdGenerator
    bus: MessageBus


# プロセス内で共有されるサービス(in-memory)
_services = CLIServices(
    uow=InMemoryUnitOfWork(),
    id_gen=InMemoryIdGenerator(),
    bus=MessageBus(),
)
_services.uow.message_bus = _services.bus


def get_services() -> CLIServices:
    return _services
