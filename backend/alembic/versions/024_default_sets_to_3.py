"""Change default sets from 4 back to 3 for new workout exercises.

Revision ID: 024
Revises: 023
Create Date: 2026-11-13

Three working sets per exercise is the base; the main lift of a day can
be raised to 4 by hand. Existing rows keep their sets.
"""
import sqlalchemy as sa
from alembic import op

revision = "024"
down_revision = "023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "workout_exercises",
        "sets",
        existing_type=sa.Integer(),
        server_default="3",
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "workout_exercises",
        "sets",
        existing_type=sa.Integer(),
        server_default="4",
        existing_nullable=False,
    )
