from __future__ import annotations

from decimal import Decimal  # noqa: TC003

from pydantic import BaseModel, Field, field_validator


# -------- Products --------
class ProductCreate(BaseModel):
    sku: str = Field(..., description="SKU code (A-Z0-9-_ up to 64)")
    name: str = Field(..., min_length=1, max_length=255)
    price: Decimal = Field(..., ge=0)
    currency: str = Field(..., min_length=3, max_length=3, description="ISO4217-like, uppercase")

    @field_validator("currency")
    @classmethod
    def _upper_currency(cls, v: str) -> str:
        v2 = v.strip().upper()
        if len(v2) != 3 or not v2.isalpha():
            raise ValueError("currency must be 3 uppercase letters")
        return v2


class ProductOut(BaseModel):
    sku: str
    name: str
    price: str
    currency: str


# -------- Orders --------
class OrderItemIn(BaseModel):
    sku: str
    quantity: int = Field(..., gt=0)


class PlaceOrderIn(BaseModel):
    items: list[OrderItemIn]


class MoneyOut(BaseModel):
    currency: str
    amount: str


class PlaceOrderOut(BaseModel):
    order_id: str
    total: MoneyOut


# -------- Inventory --------
class InventoryItemIn(BaseModel):
    sku: str
    on_hand: int = Field(..., ge=0)


class InventoryUpsertIn(BaseModel):
    location: str = "default"
    items: list[InventoryItemIn]


class InventoryOut(BaseModel):
    location: str
    items: list[InventoryItemIn]


class AllocateIn(BaseModel):
    location: str | None = "default"
