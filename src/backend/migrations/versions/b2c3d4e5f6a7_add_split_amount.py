"""add_split_amount

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-30 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(sa.text("""
        DO $$ BEGIN
            ALTER TYPE splittype ADD VALUE IF NOT EXISTS 'amount';
        EXCEPTION WHEN others THEN NULL;
        END $$;
    """))


def downgrade():
    # PostgreSQL does not support removing enum values; downgrade is a no-op
    pass
