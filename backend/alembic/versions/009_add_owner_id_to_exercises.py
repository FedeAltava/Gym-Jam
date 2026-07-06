"""Add owner_id to exercises for custom user exercises."""
from alembic import op
import sqlalchemy as sa

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "exercises",
        sa.Column("owner_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
    )
    op.create_index("ix_exercises_owner_id", "exercises", ["owner_id"])


def downgrade() -> None:
    op.drop_index("ix_exercises_owner_id", table_name="exercises")
    op.drop_column("exercises", "owner_id")
