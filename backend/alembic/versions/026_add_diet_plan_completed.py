"""Add completed flag to diet_plans so a menu can be ticked off.

Revision ID: 026
Revises: 025
Create Date: 2026-11-16
"""

import sqlalchemy as sa
from alembic import op

revision = "026"
down_revision = "025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "diet_plans",
        sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("diet_plans", "completed")
