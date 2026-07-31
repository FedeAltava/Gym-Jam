"""Normalize email case and add functional unique index.

Revision ID: 017
Revises: 016
Create Date: 2026-07-31

Three-step fix for the case-sensitive email regression introduced in 016:

1. Normalize all existing email rows to lowercase so no two rows can match
   the same lower(email) value before the unique index is created.
2. Drop the old case-sensitive unique constraint (users_email_key).
3. Create a functional unique index on lower(email), which:
   - Enforces uniqueness case-insensitively at the DB level.
   - Allows PostgreSQL to use the index for queries that filter on
     lower(email) = ..., eliminating the sequential-scan risk on login.

After this migration, find_by_email queries
  WHERE lower(email) = lower(:email)
are both safe (no MultipleResultsFound) and index-backed.
"""

from alembic import op

revision = "017"
down_revision = "016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE users SET email = lower(email)")
    op.drop_constraint("users_email_key", "users", type_="unique")
    op.execute(
        "CREATE UNIQUE INDEX uix_users_email_lower ON users (lower(email))"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uix_users_email_lower")
    op.create_unique_constraint("users_email_key", "users", ["email"])
