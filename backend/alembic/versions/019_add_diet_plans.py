"""Add diet_plans table for PDF-uploaded weekly meal plans.

Revision ID: 019
Revises: 018
Create Date: 2026-09-08
"""

import sqlalchemy as sa
from alembic import op

revision = "019"
down_revision = "018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "diet_plans",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("calories", sa.Integer(), nullable=True),
        sa.Column("menu_json", sa.Text(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_diet_plans_user_uploaded",
        "diet_plans",
        ["user_id", "uploaded_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_diet_plans_user_uploaded", table_name="diet_plans")
    op.drop_table("diet_plans")
