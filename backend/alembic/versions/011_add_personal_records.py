"""Add personal_records table.

One row per (user, catalog exercise): the heaviest weight the user has ever
logged for that exercise. Rows are upserted in Python (SELECT-then-INSERT,
ADR 4) when a session is completed; the UNIQUE constraint is the backstop.
"""
import sqlalchemy as sa
from alembic import op

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "personal_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Soft reference to the exercise catalog, same rationale as
        # workout_exercises.exercise_id (legacy free-text ids, no FK).
        sa.Column("exercise_id", sa.String(255), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=False),
        sa.Column("achieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "session_id",
            sa.String(36),
            sa.ForeignKey("workout_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "exercise_id", name="uq_personal_records_user_exercise"),
    )
    op.create_index("ix_personal_records_user", "personal_records", ["user_id"])
    # Serves the pr_count LEFT JOIN in session history.
    op.create_index("ix_personal_records_session_id", "personal_records", ["session_id"])


def downgrade() -> None:
    op.drop_index("ix_personal_records_session_id", table_name="personal_records")
    op.drop_index("ix_personal_records_user", table_name="personal_records")
    op.drop_table("personal_records")
