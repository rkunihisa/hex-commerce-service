from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "0002_add_indexes"
down_revision = "0001_init_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_orders_created_at", "orders", ["created_at"])
    op.create_index("ix_orders_currency_created_at", "orders", ["currency", "created_at"])

    op.create_index("ix_order_lines_sku", "order_lines", ["sku"])
    op.create_index("ix_order_lines_order_id_sku", "order_lines", ["order_id", "sku"])

    op.create_index("ix_inventory_items_sku", "inventory_items", ["sku"])


def downgrade() -> None:
    op.drop_index("ix_inventory_items_sku", table_name="inventory_items")
    op.drop_index("ix_order_lines_order_id_sku", table_name="order_lines")
    op.drop_index("ix_order_lines_sku", table_name="order_lines")
    op.drop_index("ix_orders_currency_created_at", table_name="orders")
    op.drop_index("ix_orders_created_at", table_name="orders")
