"""Add body_weight_entries: one body weight measurement per user and day.

Revision ID: 022
Revises: 021
Create Date: 2026-11-04
"""

import sqlalchemy as sa
from alembic import op

revision = "022"
down_revision = "021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "body_weight_entries",
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("measured_on", sa.Date(), primary_key=True),
        sa.Column("weight_kg", sa.Float(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("body_weight_entries")
