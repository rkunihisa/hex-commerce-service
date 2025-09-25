from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "0001_init_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("sku", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("unit_price_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.PrimaryKeyConstraint("sku"),
    )

    op.create_table(
        "orders",
        sa.Column("id", pg.UUID(as_uuid=False), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "order_lines",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_id", pg.UUID(as_uuid=False), nullable=False),
        sa.Column("sku", sa.String(length=64), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sku"], ["products.sku"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_order_lines_order_id", "order_lines", ["order_id"])

    op.create_check_constraint("ck_order_lines_quantity_positive", "order_lines", "quantity > 0")

    op.create_table(
        "inventory_locations",
        sa.Column("location", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("location"),
    )

    op.create_table(
        "inventory_items",
        sa.Column("location", sa.String(length=64), nullable=False),
        sa.Column("sku", sa.String(length=64), nullable=False),
        sa.Column("on_hand", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.ForeignKeyConstraint(["location"], ["inventory_locations.location"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sku"], ["products.sku"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("location", "sku"),
    )

    op.create_check_constraint(
        "ck_inventory_items_on_hand_non_negative", "inventory_items", "on_hand >= 0"
    )


def downgrade() -> None:
    op.drop_constraint("ck_inventory_items_on_hand_non_negative", "inventory_items", type_="check")
    op.drop_table("inventory_items")
    op.drop_table("inventory_locations")
    op.drop_constraint("ck_order_lines_quantity_positive", "order_lines", type_="check")
    op.drop_index("ix_order_lines_order_id", table_name="order_lines")
    op.drop_table("order_lines")
    op.drop_table("orders")
    op.drop_table("products")
