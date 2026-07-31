"""Drop unused notes/difficulty_rating columns.

Revision ID: 016
Revises: 015
Create Date: 2026-07-31

Removes columns that were added in the initial session-logging design but
never implemented in the domain layer, use cases, or API:

  workout_sessions.notes
  workout_logs.difficulty_rating
  workout_logs.notes

These columns were never written or read by the application. Dropping them
eliminates dead schema and the risk of merge()-based NULL-overwrites on
workout_logs rows.
"""

from alembic import op
import sqlalchemy as sa

revision = "016"
down_revision = "015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("workout_sessions", "notes")
    op.drop_column("workout_logs", "difficulty_rating")
    op.drop_column("workout_logs", "notes")


def downgrade() -> None:
    op.add_column("workout_logs", sa.Column("notes", sa.String(500), nullable=True))
    op.add_column("workout_logs", sa.Column("difficulty_rating", sa.Integer(), nullable=True))
    op.add_column("workout_sessions", sa.Column("notes", sa.String(1000), nullable=True))
