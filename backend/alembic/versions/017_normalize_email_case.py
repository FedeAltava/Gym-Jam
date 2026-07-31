"""Normalize email case and add functional unique index.

Revision ID: 017
Revises: 016
Create Date: 2026-07-31

1. Pre-flight: abort with a clear message if duplicate emails exist (must be
   resolved manually before the migration can proceed).
2. Drop the old case-sensitive unique constraint (users_email_key) BEFORE the
   UPDATE so the normalization never collides with the still-active constraint.
3. UPDATE users SET email = lower(email) to normalize existing rows.
4. Create a functional unique index on lower(email), which:
   - Enforces case-insensitive uniqueness at the DB level.
   - Allows PostgreSQL to use the index for queries that filter on
     lower(email) = ..., eliminating the sequential-scan risk on login.

After this migration, find_by_email queries
  WHERE lower(email) = lower(:email)
are both safe (no MultipleResultsFound) and index-backed.
"""

import sqlalchemy as sa
from alembic import op

revision = "017"
down_revision = "016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    dupes = bind.execute(
        sa.text("SELECT lower(email) FROM users GROUP BY 1 HAVING count(*) > 1")
    ).fetchall()
    if dupes:
        raise RuntimeError(
            f"Duplicate emails (case-insensitive) must be merged manually before "
            f"this migration can run: {[row[0] for row in dupes]}"
        )

    op.drop_constraint("users_email_key", "users", type_="unique")
    op.execute("UPDATE users SET email = lower(email)")
    op.execute("CREATE UNIQUE INDEX uix_users_email_lower ON users (lower(email))")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uix_users_email_lower")
    op.create_unique_constraint("users_email_key", "users", ["email"])
