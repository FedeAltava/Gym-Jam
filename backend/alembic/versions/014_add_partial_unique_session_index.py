"""Add partial unique index to prevent concurrent in-progress sessions.

Revision ID: 014
Revises: 013
Create Date: 2026-07-30

Adds a partial unique index on workout_sessions(user_id, training_day_id)
WHERE completed_at IS NULL. This closes the race window where two concurrent
POST /sessions requests both pass the app-level guard and insert duplicate
in-progress sessions for the same training day.

Both PostgreSQL and SQLite support partial indexes with a WHERE clause.
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = "014"
down_revision: Union[str, None] = "013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "uix_one_inprogress_per_day",
        "workout_sessions",
        ["user_id", "training_day_id"],
        unique=True,
        postgresql_where=text("completed_at IS NULL"),
        sqlite_where=text("completed_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uix_one_inprogress_per_day", table_name="workout_sessions")
