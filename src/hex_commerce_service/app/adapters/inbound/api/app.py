from __future__ import annotations

from fastapi import FastAPI

from hex_commerce_service.app.adapters.inbound.api.routers import inventory, orders, products
from hex_commerce_service.app.adapters.inmemory.system import (
    InMemoryIdGenerator,
    InMemoryUnitOfWork,
)
from hex_commerce_service.app.application.message_bus import MessageBus


def create_app() -> FastAPI:
    app = FastAPI(title="Hex Commerce API", version="0.1.0")

    # シンプルなサービスロケータ(in-memory)。本番はDI/Containerに差し替え前提。
    app.state.uow = InMemoryUnitOfWork()
    app.state.id_gen = InMemoryIdGenerator()
    app.state.bus = MessageBus()
    # UoW にバスを接続(Day7準拠)
    app.state.uow.message_bus = app.state.bus

    # DI dependencies
    def get_uow() -> InMemoryUnitOfWork:
        return app.state.uow

    def get_id_gen() -> InMemoryIdGenerator:
        return app.state.id_gen

    def get_bus() -> MessageBus:
        return app.state.bus

    app.dependency_overrides[products.get_uow] = get_uow
    app.dependency_overrides[orders.get_uow] = get_uow
    app.dependency_overrides[orders.get_id_gen] = get_id_gen
    app.dependency_overrides[inventory.get_uow] = get_uow

    # ルータ
    app.include_router(products.router, prefix="/products", tags=["products"])
    app.include_router(orders.router, prefix="/orders", tags=["orders"])
    app.include_router(inventory.router, prefix="/inventory", tags=["inventory"])

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
