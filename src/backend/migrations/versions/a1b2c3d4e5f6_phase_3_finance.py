"""phase_3_finance

Revision ID: a1b2c3d4e5f6
Revises: 673eb06237ff
Create Date: 2026-05-30 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM

revision = 'a1b2c3d4e5f6'
down_revision = '673eb06237ff'
branch_labels = None
depends_on = None

# Reference existing enums without re-creating them
splittype = ENUM('none', 'equal', 'custom', name='splittype', create_type=False)
paymentmethod = ENUM('cash', 'card', name='paymentmethod', create_type=False)


def _table_exists(name):
    from sqlalchemy import inspect
    return inspect(op.get_bind()).has_table(name)


def _column_exists(table, column):
    from sqlalchemy import inspect
    cols = [c['name'] for c in inspect(op.get_bind()).get_columns(table)]
    return column in cols


def upgrade():
    conn = op.get_bind()

    # ── is_admin column ───────────────────────────────────────────────────
    if not _column_exists('users', 'is_admin'):
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.add_column(sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'))
        op.execute("""
            UPDATE users u
            SET is_admin = true
            WHERE u.id = (
                SELECT id FROM users u2
                WHERE u2.household_id = u.household_id
                ORDER BY u2.created_at ASC
                LIMIT 1
            )
        """)

    # ── Enum types ────────────────────────────────────────────────────────
    conn.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE splittype AS ENUM ('none', 'equal', 'custom');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """))
    conn.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE paymentmethod AS ENUM ('cash', 'card');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """))

    # ── finance_categories ────────────────────────────────────────────────
    if not _table_exists('finance_categories'):
        op.create_table(
            'finance_categories',
            sa.Column('id', sa.UUID(as_uuid=True), primary_key=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('household_id', sa.UUID(as_uuid=True), sa.ForeignKey('households.id'), nullable=False),
            sa.Column('created_by', sa.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('icon', sa.String(50), nullable=False, server_default='bi-tag'),
            sa.Column('color', sa.String(20), nullable=False, server_default='#6b7280'),
            sa.Column('is_shared', sa.Boolean(), nullable=False, server_default='true'),
        )

    # ── user_category_assignments ─────────────────────────────────────────
    if not _table_exists('user_category_assignments'):
        op.create_table(
            'user_category_assignments',
            sa.Column('id', sa.UUID(as_uuid=True), primary_key=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('household_id', sa.UUID(as_uuid=True), sa.ForeignKey('households.id'), nullable=False),
            sa.Column('created_by', sa.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('user_id', sa.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('category_id', sa.UUID(as_uuid=True), sa.ForeignKey('finance_categories.id', ondelete='CASCADE'), nullable=False),
            sa.UniqueConstraint('user_id', 'category_id', name='uq_user_category'),
        )

    # ── user_monthly_budgets ──────────────────────────────────────────────
    if not _table_exists('user_monthly_budgets'):
        op.create_table(
            'user_monthly_budgets',
            sa.Column('id', sa.UUID(as_uuid=True), primary_key=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('household_id', sa.UUID(as_uuid=True), sa.ForeignKey('households.id'), nullable=False),
            sa.Column('created_by', sa.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('user_id', sa.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('category_id', sa.UUID(as_uuid=True), sa.ForeignKey('finance_categories.id', ondelete='SET NULL'), nullable=True),
            sa.Column('month', sa.Date(), nullable=False),
            sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        )

    # ── expenses ──────────────────────────────────────────────────────────
    if not _table_exists('expenses'):
        op.create_table(
            'expenses',
            sa.Column('id', sa.UUID(as_uuid=True), primary_key=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('household_id', sa.UUID(as_uuid=True), sa.ForeignKey('households.id'), nullable=False),
            sa.Column('created_by', sa.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('category_id', sa.UUID(as_uuid=True), sa.ForeignKey('finance_categories.id'), nullable=False),
            sa.Column('title', sa.String(300), nullable=False),
            sa.Column('amount', sa.Numeric(12, 2), nullable=False),
            sa.Column('paid_by', sa.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('split_type', splittype, nullable=False, server_default='equal'),
            sa.Column('split_ratio', sa.JSON(), nullable=True),
            sa.Column('expense_date', sa.Date(), nullable=False),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('is_subscription', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('payment_method', paymentmethod, nullable=False, server_default='card'),
        )

    # ── settlements ───────────────────────────────────────────────────────
    if not _table_exists('settlements'):
        op.create_table(
            'settlements',
            sa.Column('id', sa.UUID(as_uuid=True), primary_key=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('household_id', sa.UUID(as_uuid=True), sa.ForeignKey('households.id'), nullable=False),
            sa.Column('created_by', sa.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('paid_by', sa.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('paid_to', sa.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('amount', sa.Numeric(12, 2), nullable=False),
            sa.Column('note', sa.Text(), nullable=True),
            sa.Column('settled_at', sa.Date(), nullable=False),
        )


def downgrade():
    op.drop_table('settlements')
    op.drop_table('expenses')
    op.drop_table('user_monthly_budgets')
    op.drop_table('user_category_assignments')
    op.drop_table('finance_categories')
    op.execute("DROP TYPE IF EXISTS paymentmethod")
    op.execute("DROP TYPE IF EXISTS splittype")
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('is_admin')
