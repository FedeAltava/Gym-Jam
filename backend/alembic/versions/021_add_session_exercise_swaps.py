"""Add session_exercise_swaps: replace a planned exercise for one session only.

Revision ID: 021
Revises: 020
Create Date: 2026-11-04
"""

import sqlalchemy as sa
from alembic import op

revision = "021"
down_revision = "020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "session_exercise_swaps",
        sa.Column(
            "session_id",
            sa.String(36),
            sa.ForeignKey("workout_sessions.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "workout_exercise_id",
            sa.String(36),
            sa.ForeignKey("workout_exercises.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("exercise_id", sa.String(255), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("session_exercise_swaps")
