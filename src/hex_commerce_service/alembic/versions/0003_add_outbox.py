from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "0003_add_outbox"
down_revision = "0002_add_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "outbox_messages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("aggregate_id", sa.String(length=64), nullable=True),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("payload", pg.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("lock_owner", sa.String(length=64), nullable=True),
        sa.Column("lock_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("attempt_count >= 0", name="ck_outbox_attempts_non_negative"),
        sa.UniqueConstraint("event_type", "idempotency_key", name="uq_outbox_type_idempo"),
    )
    op.create_index("ix_outbox_state_available", "outbox_messages", ["state", "available_at"])
    op.create_index("ix_outbox_lock_until", "outbox_messages", ["lock_until"])
    op.create_index("ix_outbox_created_at", "outbox_messages", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_outbox_created_at", table_name="outbox_messages")
    op.drop_index("ix_outbox_lock_until", table_name="outbox_messages")
    op.drop_index("ix_outbox_state_available", table_name="outbox_messages")
    op.drop_table("outbox_messages")
