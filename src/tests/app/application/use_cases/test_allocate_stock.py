from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable, List

from hex_commerce_service.app.application.ports.events import EventPublisher
from hex_commerce_service.app.application.ports.ids import IdGenerator
from hex_commerce_service.app.application.ports.unit_of_work import UnitOfWork
from hex_commerce_service.app.application.ports.repositories import (
    InventoryRepository,
    OrderRepository,
    ProductRepository,
)
from hex_commerce_service.app.application.ports.time import Clock
from hex_commerce_service.app.domain.value_objects import OrderId
from hex_commerce_service.app.adapters.inmemory.repositories import (
    InMemoryInventoryRepository,
    InMemoryOrderRepository,
    InMemoryProductRepository,
)
