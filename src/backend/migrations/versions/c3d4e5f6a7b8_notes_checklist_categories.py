"""notes: add checklist type and note_categories table

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-30
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # Idempotent: create notetype enum
    conn.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE notetype AS ENUM ('text', 'checklist');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """))

    # note_categories table
    op.create_table(
        "note_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("color", sa.String(7), nullable=False, server_default="#6366f1"),
        sa.Column("icon", sa.String(50), nullable=False, server_default="bi-tag"),
        sa.Column("household_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("households.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    # Add note_type column (default 'text' so existing rows stay valid)
    op.add_column(
        "notes",
        sa.Column(
            "note_type",
            postgresql.ENUM("text", "checklist", name="notetype", create_type=False),
            nullable=False,
            server_default="text",
        ),
    )

    # Add checklist JSON column
    op.add_column("notes", sa.Column("checklist", postgresql.JSONB(), nullable=True))

    # Add category_id FK
    op.add_column("notes", sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_notes_category_id",
        "notes", "note_categories",
        ["category_id"], ["id"],
        ondelete="SET NULL",
    )

    # Allow body to be NULL (checklist notes may have no body)
    op.alter_column("notes", "body", nullable=True)


def downgrade():
    op.drop_constraint("fk_notes_category_id", "notes", type_="foreignkey")
    op.drop_column("notes", "category_id")
    op.drop_column("notes", "checklist")
    op.drop_column("notes", "note_type")
    op.alter_column("notes", "body", nullable=False)
    op.drop_table("note_categories")
    conn = op.get_bind()
    conn.execute(sa.text("DROP TYPE IF EXISTS notetype"))
