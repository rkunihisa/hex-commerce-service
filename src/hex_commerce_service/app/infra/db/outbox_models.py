from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from hex_commerce_service.app.infra.db.base import Base


class OutboxMessageModel(Base):
    __tablename__ = "outbox_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    aggregate_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)

    state: Mapped[str] = mapped_column(String(16), nullable=False, server_default=text("'pending'"))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    lock_owner: Mapped[str | None] = mapped_column(String(64), nullable=True)
    lock_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    __table_args__ = (
        UniqueConstraint("event_type", "idempotency_key", name="uq_outbox_type_idempo"),
        CheckConstraint("attempt_count >= 0", name="ck_outbox_attempts_non_negative"),
        Index("ix_outbox_state_available", "state", "available_at"),
        Index("ix_outbox_lock_until", "lock_until"),
        Index("ix_outbox_created_at", "created_at"),
    )
