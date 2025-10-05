from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from hex_commerce_service.app.adapters.inbound.api.auth.security import require_role
from hex_commerce_service.app.adapters.inbound.api.dtos import InventoryOut, InventoryUpsertIn
from hex_commerce_service.app.adapters.inbound.api.errors import to_http
from hex_commerce_service.app.adapters.inmemory.system import InMemoryUnitOfWork
from hex_commerce_service.app.domain.entities import Inventory
from hex_commerce_service.app.domain.value_objects import Sku

router = APIRouter()


def get_uow() -> InMemoryUnitOfWork:
    raise RuntimeError("dependency not provided")


require_admin = require_role("admin")
require_user = require_role("user")


@router.put("/{location}", response_model=InventoryOut, dependencies=[Depends(require_admin)])
def upsert_inventory(
    location: str, body: InventoryUpsertIn, uow: Annotated[InMemoryUnitOfWork, Depends(get_uow)]
) -> InventoryOut:
    try:
        inv = Inventory(location=location)
        for item in body.items:
            inv.set_on_hand(Sku(item.sku), item.on_hand)
        with uow:
            uow.inventories.upsert(inv)
            uow.commit()
        return InventoryOut(
            location=location,
            items=[{"sku": s.value, "on_hand": inv.available(s)} for s in inv._on_hand],  # noqa: SLF001
        )
    except Exception as exc:
        raise to_http(exc) from exc


@router.get("/{location}", response_model=InventoryOut, dependencies=[Depends(require_user)])
def get_inventory(
    location: str, uow: Annotated[InMemoryUnitOfWork, Depends(get_uow)]
) -> InventoryOut:
    inv = uow.inventories.get(location)
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="inventory not found")
    return InventoryOut(
        location=location,
        items=[{"sku": s.value, "on_hand": inv.available(s)} for s in inv._on_hand],  # noqa: SLF001
    )
