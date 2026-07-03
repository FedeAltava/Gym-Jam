"""Add workout session logging tables and exercise plan fields.

Revision ID: 005
Revises: 004
Create Date: 2026-07-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add plan fields to workout_exercises (server_default keeps existing rows valid)
    op.add_column(
        "workout_exercises",
        sa.Column("sets", sa.Integer(), nullable=False, server_default="3"),
    )
    op.add_column(
        "workout_exercises",
        sa.Column("reps_per_set", sa.Integer(), nullable=False, server_default="10"),
    )
    op.add_column(
        "workout_exercises",
        sa.Column("weight_kg", sa.Float(), nullable=True),
    )

    # Create workout_sessions table
    op.create_table(
        "workout_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "workout_id",
            sa.String(36),
            sa.ForeignKey("workouts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "training_day_id",
            sa.String(36),
            sa.ForeignKey("training_days.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("notes", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_workout_sessions_user_id", "workout_sessions", ["user_id"])
    op.create_index("ix_workout_sessions_workout_id", "workout_sessions", ["workout_id"])
    op.create_index("ix_workout_sessions_training_day_id", "workout_sessions", ["training_day_id"])

    # Create workout_logs table
    op.create_table(
        "workout_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(36),
            sa.ForeignKey("workout_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "workout_exercise_id",
            sa.String(36),
            sa.ForeignKey("workout_exercises.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("set_number", sa.Integer(), nullable=False),
        sa.Column("reps_completed", sa.Integer(), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=True),
        sa.Column("difficulty_rating", sa.Integer(), nullable=True),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("session_id", "workout_exercise_id", "set_number"),
    )
    op.create_index("ix_workout_logs_session_id", "workout_logs", ["session_id"])
    op.create_index("ix_workout_logs_workout_exercise_id", "workout_logs", ["workout_exercise_id"])


def downgrade() -> None:
    # Drop workout_logs first (FK dependency on workout_sessions)
    op.drop_index("ix_workout_logs_workout_exercise_id", table_name="workout_logs")
    op.drop_index("ix_workout_logs_session_id", table_name="workout_logs")
    op.drop_table("workout_logs")

    # Drop workout_sessions
    op.drop_index("ix_workout_sessions_training_day_id", table_name="workout_sessions")
    op.drop_index("ix_workout_sessions_workout_id", table_name="workout_sessions")
    op.drop_index("ix_workout_sessions_user_id", table_name="workout_sessions")
    op.drop_table("workout_sessions")

    # Drop plan columns from workout_exercises
    op.drop_column("workout_exercises", "weight_kg")
    op.drop_column("workout_exercises", "reps_per_set")
    op.drop_column("workout_exercises", "sets")
