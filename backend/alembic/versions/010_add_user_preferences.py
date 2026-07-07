"""Add user preference columns (rest timer + weight units).

rest_seconds drives the rest-timer default between sets; units selects the
display unit (storage is always kg — lb is a presentation conversion).
"""
import sqlalchemy as sa
from alembic import op

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("rest_seconds", sa.Integer(), nullable=False, server_default="90"),
    )
    op.add_column(
        "users",
        sa.Column("units", sa.String(2), nullable=False, server_default="kg"),
    )


def downgrade() -> None:
    # batch_alter_table so DROP COLUMN works on older SQLite (< 3.35).
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("units")
        batch_op.drop_column("rest_seconds")
