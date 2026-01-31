"""Create host_profiles table.

Revision ID: 000000000004
Revises: 000000000003
Create Date: 2026-01-29 03:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from geoalchemy2 import Geography
from sqlalchemy.dialects.postgresql import ENUM, UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "000000000004"
down_revision: str | None = "000000000003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create host_profiles table with PostGIS location support."""
    # Create verification_status enum using raw SQL
    op.execute(
        "CREATE TYPE verification_status_enum AS ENUM "
        "('unverified', 'pending', 'verified', 'rejected')"
    )

    # Create host_profiles table
    op.create_table(
        "host_profiles",
        sa.Column(
            "id",
            UUID(as_uuid=False),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=False),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("headline", sa.String(200), nullable=True),
        sa.Column(
            "hourly_rate_cents",
            sa.Integer(),
            nullable=False,
            server_default="5000",
        ),
        sa.Column("rating_average", sa.Numeric(3, 2), nullable=True),
        sa.Column(
            "total_reviews",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "total_sessions",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "verification_status",
            ENUM(
                "unverified",
                "pending",
                "verified",
                "rejected",
                name="verification_status_enum",
                create_type=False,
            ),
            nullable=False,
            server_default="unverified",
        ),
        # PostGIS GEOGRAPHY(POINT, 4326) for accurate distance calculations
        sa.Column(
            "location",
            Geography(geometry_type="POINT", srid=4326),
            nullable=True,
        ),
        sa.Column("stripe_account_id", sa.String(255), nullable=True),
        sa.Column(
            "stripe_onboarding_complete",
            sa.Boolean(),
            nullable=False,
            server_default="false",
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

    # Create unique index on user_id (enforces one-to-one relationship)
    op.create_index(
        "ix_host_profiles_user_id",
        "host_profiles",
        ["user_id"],
        unique=True,
    )

    # Create geospatial index on location for efficient proximity queries
    op.create_index(
        "ix_host_profiles_location",
        "host_profiles",
        ["location"],
        postgresql_using="gist",
    )


def downgrade() -> None:
    """Drop host_profiles table and enum."""
    op.drop_index("ix_host_profiles_location", table_name="host_profiles")
    op.drop_index("ix_host_profiles_user_id", table_name="host_profiles")
    op.drop_table("host_profiles")

    # Drop enum type
    sa.Enum(name="verification_status_enum").drop(op.get_bind(), checkfirst=True)
