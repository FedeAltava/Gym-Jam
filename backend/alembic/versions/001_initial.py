"""Initial schema — create all tables.

Revision ID: 001
Revises:
Create Date: 2026-05-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "workouts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_workouts_user_id", "workouts", ["user_id"])

    op.create_table(
        "training_days",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workout_id", sa.String(36), sa.ForeignKey("workouts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("day_of_week", sa.String(10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("workout_id", "day_of_week"),
    )

    op.create_table(
        "workout_exercises",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workout_id", sa.String(36), sa.ForeignKey("workouts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("training_day_id", sa.String(36), sa.ForeignKey("training_days.id", ondelete="CASCADE"), nullable=False),
        sa.Column("exercise_id", sa.String(255), nullable=False),
        sa.Column("order_in_day", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("training_day_id", "order_in_day"),
    )
    op.create_index("ix_workout_exercises_exercise_id", "workout_exercises", ["exercise_id"])

    op.create_table(
        "workout_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("workout_id", sa.String(36), sa.ForeignKey("workouts.id"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("notes", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_workout_sessions_user_id", "workout_sessions", ["user_id"])

    op.create_table(
        "workout_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("workout_sessions.id"), nullable=False),
        sa.Column("workout_exercise_id", sa.String(36), sa.ForeignKey("workout_exercises.id"), nullable=False),
        sa.Column("set_number", sa.Integer(), nullable=False),
        sa.Column("reps_completed", sa.Integer(), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=True),
        sa.Column("difficulty_rating", sa.Integer(), nullable=True),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_workout_logs_session_id", "workout_logs", ["session_id"])


def downgrade() -> None:
    op.drop_table("workout_logs")
    op.drop_table("workout_sessions")
    op.drop_table("workout_exercises")
    op.drop_table("training_days")
    op.drop_table("workouts")
    op.drop_table("users")
