"""Create host_dance_styles junction table.

Revision ID: 000000000005
Revises: 000000000004
Create Date: 2026-01-29 04:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "000000000005"
down_revision: str | None = "000000000004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create host_dance_styles junction table."""
    # Create host_dance_styles table
    op.create_table(
        "host_dance_styles",
        sa.Column(
            "id",
            UUID(as_uuid=False),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "host_profile_id",
            UUID(as_uuid=False),
            sa.ForeignKey("host_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "dance_style_id",
            UUID(as_uuid=False),
            sa.ForeignKey("dance_styles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "skill_level",
            sa.Integer(),
            nullable=False,
            server_default="3",
        ),
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

    # Create unique constraint on (host_profile_id, dance_style_id)
    op.create_unique_constraint(
        "uq_host_dance_style_host_profile_dance_style",
        "host_dance_styles",
        ["host_profile_id", "dance_style_id"],
    )

    # Create check constraint for skill_level range (1-5)
    op.create_check_constraint(
        "ck_host_dance_style_skill_level_range",
        "host_dance_styles",
        "skill_level >= 1 AND skill_level <= 5",
    )

    # Create indexes for foreign keys
    op.create_index(
        "ix_host_dance_styles_host_profile_id",
        "host_dance_styles",
        ["host_profile_id"],
    )
    op.create_index(
        "ix_host_dance_styles_dance_style_id",
        "host_dance_styles",
        ["dance_style_id"],
    )


def downgrade() -> None:
    """Drop host_dance_styles table."""
    op.drop_index("ix_host_dance_styles_dance_style_id", table_name="host_dance_styles")
    op.drop_index(
        "ix_host_dance_styles_host_profile_id", table_name="host_dance_styles"
    )
    op.drop_constraint(
        "ck_host_dance_style_skill_level_range",
        "host_dance_styles",
        type_="check",
    )
    op.drop_constraint(
        "uq_host_dance_style_host_profile_dance_style",
        "host_dance_styles",
        type_="unique",
    )
    op.drop_table("host_dance_styles")
