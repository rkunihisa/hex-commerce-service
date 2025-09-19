from __future__ import annotations

import pytest

from hex_commerce_service.app.adapters.inmemory.system import InMemoryIdGenerator, InMemoryUnitOfWork
from hex_commerce_service.app.application.use_cases.place_order import (
    NewOrderItem,
    PlaceOrderCommand,
    PlaceOrderUseCase,
)
from hex_commerce_service.app.application.messages.events import OrderPlaced
from hex_commerce_service.app.domain.entities import Product
from hex_commerce_service.app.domain.errors import CurrencyMismatch, ValidationError
from hex_commerce_service.app.domain.value_objects import Money, Sku

