"""expenses: make category_id nullable with SET NULL on category delete

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-05-30
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade():
    # Drop the old FK (no ondelete, NOT NULL enforced)
    op.drop_constraint("expenses_category_id_fkey", "expenses", type_="foreignkey")

    # Allow NULL (uncategorized expense when category is deleted)
    op.alter_column("expenses", "category_id", nullable=True)

    # Re-add FK with SET NULL so deleting a category nullifies its expenses
    op.create_foreign_key(
        "expenses_category_id_fkey",
        "expenses", "finance_categories",
        ["category_id"], ["id"],
        ondelete="SET NULL",
    )


def downgrade():
    op.drop_constraint("expenses_category_id_fkey", "expenses", type_="foreignkey")
    # Cannot restore NOT NULL if any rows have NULL category_id at this point
    op.create_foreign_key(
        "expenses_category_id_fkey",
        "expenses", "finance_categories",
        ["category_id"], ["id"],
    )
