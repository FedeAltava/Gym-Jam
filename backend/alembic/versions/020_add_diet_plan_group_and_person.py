"""Add group_id and person to diet_plans for per-person menu variants.

Revision ID: 020
Revises: 019
Create Date: 2026-10-27
"""

import sqlalchemy as sa
from alembic import op

revision = "020"
down_revision = "019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("diet_plans", sa.Column("group_id", sa.String(36), nullable=True))
    op.add_column("diet_plans", sa.Column("person", sa.String(50), nullable=True))
    op.create_index("ix_diet_plans_user_group", "diet_plans", ["user_id", "group_id"])


def downgrade() -> None:
    op.drop_index("ix_diet_plans_user_group", table_name="diet_plans")
    op.drop_column("diet_plans", "person")
    op.drop_column("diet_plans", "group_id")
