"""Create availability tables.

Revision ID: 000000000007
Revises: 000000000006
Create Date: 2026-01-29 06:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "000000000007"
down_revision: str | None = "000000000006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create recurring_availability and availability_overrides tables."""
    # Create recurring_availability table for weekly schedules
    op.create_table(
        "recurring_availability",
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
        # day_of_week: 0=Monday, 6=Sunday
        sa.Column(
            "day_of_week",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "start_time",
            sa.Time(),
            nullable=False,
        ),
        sa.Column(
            "end_time",
            sa.Time(),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
        # Timestamps
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
        # Check constraint for valid day_of_week values (0-6)
        sa.CheckConstraint(
            "day_of_week >= 0 AND day_of_week <= 6",
            name="check_valid_day_of_week",
        ),
    )

    # Create indexes for recurring_availability
    op.create_index(
        "ix_recurring_availability_host_profile_id",
        "recurring_availability",
        ["host_profile_id"],
    )
    op.create_index(
        "ix_recurring_availability_host_day",
        "recurring_availability",
        ["host_profile_id", "day_of_week"],
    )

    # Create availability_override_type enum
    override_type_enum = sa.Enum(
        "available",
        "blocked",
        name="availability_override_type_enum",
    )
    override_type_enum.create(op.get_bind(), checkfirst=True)

    # Create availability_overrides table for one-time overrides and blocked periods
    op.create_table(
        "availability_overrides",
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
            "override_date",
            sa.Date(),
            nullable=False,
        ),
        sa.Column(
            "override_type",
            override_type_enum,
            nullable=False,
        ),
        sa.Column(
            "start_time",
            sa.Time(),
            nullable=True,
        ),
        sa.Column(
            "end_time",
            sa.Time(),
            nullable=True,
        ),
        sa.Column(
            "all_day",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column(
            "reason",
            sa.Text(),
            nullable=True,
        ),
        # Timestamps
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

    # Create indexes for availability_overrides
    op.create_index(
        "ix_availability_overrides_host_profile_id",
        "availability_overrides",
        ["host_profile_id"],
    )
    op.create_index(
        "ix_availability_overrides_override_date",
        "availability_overrides",
        ["override_date"],
    )
    op.create_index(
        "ix_availability_overrides_host_date",
        "availability_overrides",
        ["host_profile_id", "override_date"],
    )


def downgrade() -> None:
    """Drop availability tables."""
    # Drop indexes for availability_overrides
    op.drop_index(
        "ix_availability_overrides_host_date", table_name="availability_overrides"
    )
    op.drop_index(
        "ix_availability_overrides_override_date", table_name="availability_overrides"
    )
    op.drop_index(
        "ix_availability_overrides_host_profile_id", table_name="availability_overrides"
    )

    # Drop availability_overrides table
    op.drop_table("availability_overrides")

    # Drop the enum type
    sa.Enum(name="availability_override_type_enum").drop(op.get_bind(), checkfirst=True)

    # Drop indexes for recurring_availability
    op.drop_index(
        "ix_recurring_availability_host_day", table_name="recurring_availability"
    )
    op.drop_index(
        "ix_recurring_availability_host_profile_id", table_name="recurring_availability"
    )

    # Drop recurring_availability table
    op.drop_table("recurring_availability")
