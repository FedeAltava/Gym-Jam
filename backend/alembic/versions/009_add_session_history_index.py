"""Add composite index for the session history endpoint.

GET /sessions pages a user's sessions ordered by started_at DESC; the
composite (user_id, started_at) index serves both the filter and the sort.
"""
from alembic import op

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_workout_sessions_user_started",
        "workout_sessions",
        ["user_id", "started_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_workout_sessions_user_started", table_name="workout_sessions")
