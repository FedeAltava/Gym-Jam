"""Change default sets from 3 to 4 for new workout exercises.

Revision ID: 018
Revises: 017
Create Date: 2026-08-07
"""

import sqlalchemy as sa
from alembic import op

revision = "018"
down_revision = "017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "workout_exercises",
        "sets",
        existing_type=sa.Integer(),
        server_default="4",
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "workout_exercises",
        "sets",
        existing_type=sa.Integer(),
        server_default="3",
        existing_nullable=False,
    )
