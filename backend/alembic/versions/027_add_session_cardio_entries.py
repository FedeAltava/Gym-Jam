"""Add session_cardio_entries: treadmill cardio recorded in a session.

Revision ID: 027
Revises: 026
Create Date: 2026-11-24
"""

import sqlalchemy as sa
from alembic import op

revision = "027"
down_revision = "026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "session_cardio_entries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(36),
            sa.ForeignKey("workout_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("distance_km", sa.Float(), nullable=True),
        sa.Column("speed_kmh", sa.Float(), nullable=True),
        sa.Column("incline_percent", sa.Float(), nullable=True),
        sa.Column("calories", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_session_cardio_entries_session_id",
        "session_cardio_entries",
        ["session_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_session_cardio_entries_session_id", table_name="session_cardio_entries")
    op.drop_table("session_cardio_entries")
