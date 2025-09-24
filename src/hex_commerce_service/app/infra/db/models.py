from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class ProductModel(Base):
    __tablename__ = "products"

    sku: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit_price_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Product {self.sku} {self.currency} {self.unit_price_amount}>"


class OrderModel(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(PG_UUID(as_uuid=False), primary_key=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False
    )

    lines: Mapped[list[OrderLineModel]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class OrderLineModel(Base):
    __tablename__ = "order_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=False),
        ForeignKey("orders.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    sku: Mapped[str] = mapped_column(
        String(64), ForeignKey("products.sku", ondelete="RESTRICT"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)

    order: Mapped[OrderModel] = relationship(back_populates="lines")

    __table_args__ = (CheckConstraint("quantity > 0", name="ck_order_lines_quantity_positive"),)


class InventoryLocationModel(Base):
    __tablename__ = "inventory_locations"

    location: Mapped[str] = mapped_column(String(64), primary_key=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    items: Mapped[list[InventoryItemModel]] = relationship(
        back_populates="location_ref", cascade="all, delete-orphan", passive_deletes=True
    )


class InventoryItemModel(Base):
    __tablename__ = "inventory_items"

    location: Mapped[str] = mapped_column(
        String(64), ForeignKey("inventory_locations.location", ondelete="CASCADE"), primary_key=True
    )
    sku: Mapped[str] = mapped_column(
        String(64), ForeignKey("products.sku", ondelete="RESTRICT"), primary_key=True
    )
    on_hand: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))

    location_ref: Mapped[InventoryLocationModel] = relationship(back_populates="items")

    __table_args__ = (
        CheckConstraint("on_hand >= 0", name="ck_inventory_items_on_hand_non_negative"),
    )
