"""Add avatar columns to users table.

Revision ID: 000000000014
Revises: 000000000013
Create Date: 2026-01-29 13:00:00.000000+00:00

This migration adds avatar_url and avatar_thumbnail_url columns
to the users table for storing profile image URLs.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "000000000014"
down_revision: str | None = "000000000013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add avatar_url and avatar_thumbnail_url columns."""
    op.add_column(
        "users",
        sa.Column("avatar_url", sa.String(500), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("avatar_thumbnail_url", sa.String(500), nullable=True),
    )


def downgrade() -> None:
    """Remove avatar columns."""
    op.drop_column("users", "avatar_thumbnail_url")
    op.drop_column("users", "avatar_url")
