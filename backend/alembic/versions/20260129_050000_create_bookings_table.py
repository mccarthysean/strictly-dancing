"""Create bookings table.

Revision ID: 000000000006
Revises: 000000000005
Create Date: 2026-01-29 05:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from geoalchemy2 import Geography
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "000000000006"
down_revision: str | None = "000000000005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create bookings table."""
    # Create booking_status enum
    booking_status_enum = sa.Enum(
        "pending",
        "confirmed",
        "in_progress",
        "completed",
        "cancelled",
        "disputed",
        name="booking_status_enum",
    )
    booking_status_enum.create(op.get_bind(), checkfirst=True)

    # Create bookings table
    op.create_table(
        "bookings",
        sa.Column(
            "id",
            UUID(as_uuid=False),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # Foreign keys
        sa.Column(
            "client_id",
            UUID(as_uuid=False),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "host_id",
            UUID(as_uuid=False),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
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
            sa.ForeignKey("dance_styles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        # Status
        sa.Column(
            "status",
            booking_status_enum,
            nullable=False,
            server_default="pending",
        ),
        # Scheduling
        sa.Column(
            "scheduled_start",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "scheduled_end",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "actual_start",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "actual_end",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "duration_minutes",
            sa.Integer(),
            nullable=False,
        ),
        # Location
        sa.Column(
            "location",
            Geography(geometry_type="POINT", srid=4326),
            nullable=True,
        ),
        sa.Column(
            "location_name",
            sa.String(255),
            nullable=True,
        ),
        sa.Column(
            "location_notes",
            sa.Text(),
            nullable=True,
        ),
        # Pricing (all in cents)
        sa.Column(
            "hourly_rate_cents",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "amount_cents",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "platform_fee_cents",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "host_payout_cents",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        # Stripe integration
        sa.Column(
            "stripe_payment_intent_id",
            sa.String(255),
            nullable=True,
        ),
        sa.Column(
            "stripe_transfer_id",
            sa.String(255),
            nullable=True,
        ),
        # Notes
        sa.Column(
            "client_notes",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "host_notes",
            sa.Text(),
            nullable=True,
        ),
        # Cancellation tracking
        sa.Column(
            "cancellation_reason",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "cancelled_by_id",
            UUID(as_uuid=False),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "cancelled_at",
            sa.DateTime(timezone=True),
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

    # Create indexes for foreign keys and frequently queried columns
    op.create_index("ix_bookings_client_id", "bookings", ["client_id"])
    op.create_index("ix_bookings_host_id", "bookings", ["host_id"])
    op.create_index("ix_bookings_host_profile_id", "bookings", ["host_profile_id"])
    op.create_index("ix_bookings_dance_style_id", "bookings", ["dance_style_id"])
    op.create_index("ix_bookings_status", "bookings", ["status"])
    op.create_index(
        "ix_bookings_stripe_payment_intent_id", "bookings", ["stripe_payment_intent_id"]
    )

    # Create composite index for common queries (client bookings by status)
    op.create_index("ix_bookings_client_status", "bookings", ["client_id", "status"])
    # Create composite index for host bookings by status
    op.create_index("ix_bookings_host_status", "bookings", ["host_id", "status"])

    # Create index for scheduled time queries
    op.create_index("ix_bookings_scheduled_start", "bookings", ["scheduled_start"])

    # Create geospatial index on location
    op.execute("CREATE INDEX ix_bookings_location ON bookings USING GIST (location);")


def downgrade() -> None:
    """Drop bookings table."""
    # Drop indexes
    op.execute("DROP INDEX IF EXISTS ix_bookings_location;")
    op.drop_index("ix_bookings_scheduled_start", table_name="bookings")
    op.drop_index("ix_bookings_host_status", table_name="bookings")
    op.drop_index("ix_bookings_client_status", table_name="bookings")
    op.drop_index("ix_bookings_stripe_payment_intent_id", table_name="bookings")
    op.drop_index("ix_bookings_status", table_name="bookings")
    op.drop_index("ix_bookings_dance_style_id", table_name="bookings")
    op.drop_index("ix_bookings_host_profile_id", table_name="bookings")
    op.drop_index("ix_bookings_host_id", table_name="bookings")
    op.drop_index("ix_bookings_client_id", table_name="bookings")

    # Drop table
    op.drop_table("bookings")

    # Drop enum
    sa.Enum(name="booking_status_enum").drop(op.get_bind(), checkfirst=True)
