"""Add password_changed_at column to users table.

Revision ID: 015
Revises: 014
Create Date: 2026-07-31

Adds a nullable password_changed_at timestamp to users. This field is
embedded in JWT access tokens (claim "pca") so tokens issued before a
password change are rejected on the next request, even before the access
token would have expired naturally (B6 security fix).

Existing rows receive NULL, which is intentional: the validation in
get_current_user only rejects a token when BOTH the token carries a "pca"
claim AND the user row has a non-NULL password_changed_at. Tokens issued
before this column existed carry no "pca" claim, so old sessions remain
valid until they expire normally.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "015"
down_revision: Union[str, None] = "014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "password_changed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "password_changed_at")
