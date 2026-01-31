"""Create users table.

Revision ID: 000000000002
Revises: 000000000001
Create Date: 2026-01-29 01:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM, UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "000000000002"
down_revision: str | None = "000000000001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create users table with all required fields."""
    # Create user_type enum using raw SQL
    op.execute("CREATE TYPE user_type_enum AS ENUM ('client', 'host', 'both')")

    # Create users table
    op.create_table(
        "users",
        sa.Column(
            "id",
            UUID(as_uuid=False),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column(
            "user_type",
            ENUM("client", "host", "both", name="user_type_enum", create_type=False),
            nullable=False,
            server_default="client",
        ),
        sa.Column(
            "email_verified", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # Create unique index on email (case-insensitive)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # Create case-insensitive pattern matching index for email lookups
    op.create_index(
        "ix_users_email_lower",
        "users",
        [sa.text("lower(email)")],
        unique=False,
    )


def downgrade() -> None:
    """Drop users table and enum."""
    op.drop_index("ix_users_email_lower", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    # Drop enum type
    sa.Enum(name="user_type_enum").drop(op.get_bind(), checkfirst=True)
