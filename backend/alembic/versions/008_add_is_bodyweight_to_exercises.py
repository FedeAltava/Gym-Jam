"""Add is_bodyweight flag to exercise catalog."""
from alembic import op
import sqlalchemy as sa

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None

# Frozen list on purpose — migrations must never import mutable app modules
# (see 003_add_exercise_catalog). These are the catalog rows seeded by 003
# that use no external weight.
_BODYWEIGHT_SLUGS = ("push-up", "pull-up", "plank", "crunch")


def upgrade() -> None:
    op.add_column(
        "exercises",
        sa.Column("is_bodyweight", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    # Backfill: rows seeded by migration 003 predate this column, so the
    # DEFAULT FALSE alone would leave the bodyweight exercises unmarked.
    op.execute(
        sa.text("UPDATE exercises SET is_bodyweight = TRUE WHERE id IN :slugs").bindparams(
            sa.bindparam("slugs", value=list(_BODYWEIGHT_SLUGS), expanding=True)
        )
    )


def downgrade() -> None:
    op.drop_column("exercises", "is_bodyweight")
