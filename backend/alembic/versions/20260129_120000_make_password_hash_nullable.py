"""Make password_hash nullable for passwordless auth.

Revision ID: 000000000013
Revises: 000000000012
Create Date: 2026-01-29 12:00:00.000000+00:00

This migration supports the transition to passwordless authentication
via magic link codes. The password_hash column becomes nullable since
new users will not have passwords.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "000000000013"
down_revision: str | None = "000000000012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Make password_hash column nullable for passwordless auth."""
    op.alter_column(
        "users",
        "password_hash",
        existing_type=sa.String(255),
        nullable=True,
    )


def downgrade() -> None:
    """Revert password_hash to non-nullable.

    WARNING: This will fail if there are users without password_hash values.
    You must set password_hash for all users before running this downgrade.
    """
    op.alter_column(
        "users",
        "password_hash",
        existing_type=sa.String(255),
        nullable=False,
    )
