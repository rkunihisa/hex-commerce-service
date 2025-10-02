from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from hex_commerce_service.app.adapters.inbound.api.dtos import ProductCreate, ProductOut
from hex_commerce_service.app.adapters.inbound.api.errors import to_http
from hex_commerce_service.app.adapters.inmemory.system import InMemoryUnitOfWork
from hex_commerce_service.app.domain.entities import Product
from hex_commerce_service.app.domain.value_objects import Money, Sku

router = APIRouter()


def get_uow() -> InMemoryUnitOfWork:  # この関数は app.dependency_overrides で上書きされる前提
    raise RuntimeError("dependency not provided")


def create_product(
    payload: ProductCreate, uow: Annotated[InMemoryUnitOfWork, Depends(get_uow)]
) -> ProductOut:
    try:
        product = Product(
            sku=Sku(payload.sku),
            name=payload.name.strip(),
            unit_price=Money.from_major(Decimal(payload.price), payload.currency),
        )
        with uow:
            uow.products.add(product)
            uow.commit()
        return ProductOut(
            sku=product.sku.value,
            name=product.name,
            price=f"{product.unit_price.amount:.2f}",
            currency=str(product.unit_price.currency),
        )
    except Exception as exc:
        raise to_http(exc) from exc


@router.get("/{sku}", response_model=ProductOut)
def get_product(sku: str, uow: Annotated[InMemoryUnitOfWork, Depends(get_uow)]) -> ProductOut:
    prod = uow.products.get_by_sku(Sku(sku))
    if not prod:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="product not found")
    return ProductOut(
        sku=prod.sku.value,
        name=prod.name,
        price=f"{prod.unit_price.amount:.2f}",
        currency=str(prod.unit_price.currency),
    )
