"""Add FK indexes on workout_exercises.workout_id, workout_sessions.workout_id,
and workout_logs.workout_exercise_id.

Revision ID: 002
Revises: 001
Create Date: 2026-07-02

"""
from typing import Sequence, Union

from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_workout_exercises_workout_id", "workout_exercises", ["workout_id"])


def downgrade() -> None:
    op.drop_index("ix_workout_exercises_workout_id", table_name="workout_exercises")
