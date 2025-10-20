from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class ExternalBase(BaseModel):
    model_config = {
        "extra": "forbid",
        "str_strip_whitespace": True,
    }


class ExternalOrderItem(ExternalBase):
    product_code: str = Field(..., description="SKU in external terms")
    qty: int = Field(..., gt=0, description="positive quantity")


class ExternalOrderPayload(ExternalBase):
    order_items: list[ExternalOrderItem]
    currency: str | None = Field(default=None, description="ISO4217 3 letters (optional)")

    @model_validator(mode="after")
    def _validate_currency(self) -> ExternalOrderPayload:
        cur = self.currency
        if cur is not None:
            c = cur.strip().upper()
            if len(c) != 3 or not c.isalpha():
                raise ValueError("currency must be 3 uppercase letters")
            object(self, "currency", c)
        return self


# 外部の在庫ペイロード
class ExternalInventoryItem(ExternalBase):
    code: str = Field(..., description="SKU code")
    count: int = Field(..., ge=0, description="on hand")


class ExternalInventoryPayload(ExternalBase):
    warehouse: str = Field(default="default")
    stock: list[ExternalInventoryItem]
