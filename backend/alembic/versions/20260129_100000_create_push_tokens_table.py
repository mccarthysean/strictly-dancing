"""Create push_tokens table for Expo push notifications.

Revision ID: 20260129100000
Revises: 20260129090000
Create Date: 2026-01-29 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "000000000011"
down_revision: str | None = "000000000010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create the device_platform_enum type
    device_platform_enum = postgresql.ENUM(
        "ios", "android", "web", name="device_platform_enum", create_type=False
    )
    device_platform_enum.create(op.get_bind(), checkfirst=True)

    # Create push_tokens table
    op.create_table(
        "push_tokens",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=False),
            nullable=False,
        ),
        sa.Column(
            "token",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "device_id",
            sa.String(255),
            nullable=True,
        ),
        sa.Column(
            "platform",
            device_platform_enum,
            nullable=False,
        ),
        sa.Column(
            "device_name",
            sa.String(255),
            nullable=True,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_push_tokens_user_id",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("token", name="uq_push_tokens_token"),
    )

    # Create indexes
    op.create_index(
        "ix_push_tokens_user_id",
        "push_tokens",
        ["user_id"],
    )
    op.create_index(
        "ix_push_tokens_user_platform",
        "push_tokens",
        ["user_id", "platform"],
    )
    op.create_index(
        "ix_push_tokens_user_active",
        "push_tokens",
        ["user_id", "is_active"],
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_push_tokens_user_active", table_name="push_tokens")
    op.drop_index("ix_push_tokens_user_platform", table_name="push_tokens")
    op.drop_index("ix_push_tokens_user_id", table_name="push_tokens")

    # Drop table
    op.drop_table("push_tokens")

    # Drop enum type
    device_platform_enum = postgresql.ENUM(
        "ios", "android", "web", name="device_platform_enum"
    )
    device_platform_enum.drop(op.get_bind(), checkfirst=True)
