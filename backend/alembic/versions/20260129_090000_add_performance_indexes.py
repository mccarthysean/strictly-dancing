"""Add performance indexes.

Revision ID: 000000000010
Revises: 000000000009
Create Date: 2026-01-29 09:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "000000000010"
down_revision: str | None = "000000000009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add performance indexes for frequently queried columns."""
    # Host profiles - rating and price sorting for search
    op.create_index(
        "ix_host_profiles_rating_average",
        "host_profiles",
        ["rating_average"],
        postgresql_where=sa.text("rating_average IS NOT NULL"),
    )
    op.create_index(
        "ix_host_profiles_hourly_rate_cents",
        "host_profiles",
        ["hourly_rate_cents"],
    )
    # Composite index for verified hosts with location (common search filter)
    op.create_index(
        "ix_host_profiles_verification_status",
        "host_profiles",
        ["verification_status"],
    )

    # Bookings - composite index for upcoming bookings query
    op.create_index(
        "ix_bookings_scheduled_start_status",
        "bookings",
        ["scheduled_start", "status"],
    )
    # Index for host overlap queries (availability checking)
    op.create_index(
        "ix_bookings_host_profile_schedule",
        "bookings",
        ["host_profile_id", "scheduled_start", "scheduled_end"],
    )

    # Reviews - sorting by created_at for pagination
    op.create_index(
        "ix_reviews_reviewee_created",
        "reviews",
        ["reviewee_id", "created_at"],
    )

    # Messages - index for unread messages query
    op.create_index(
        "ix_messages_sender_id",
        "messages",
        ["sender_id"],
    )

    # Host dance styles - index for search by dance style
    op.create_index(
        "ix_host_dance_styles_dance_style_id",
        "host_dance_styles",
        ["dance_style_id"],
    )

    # Availability - index for date range queries
    op.create_index(
        "ix_availability_overrides_date_type",
        "availability_overrides",
        ["host_profile_id", "override_date", "override_type"],
    )


def downgrade() -> None:
    """Remove performance indexes."""
    op.drop_index(
        "ix_availability_overrides_date_type", table_name="availability_overrides"
    )
    op.drop_index("ix_host_dance_styles_dance_style_id", table_name="host_dance_styles")
    op.drop_index("ix_messages_sender_id", table_name="messages")
    op.drop_index("ix_reviews_reviewee_created", table_name="reviews")
    op.drop_index("ix_bookings_host_profile_schedule", table_name="bookings")
    op.drop_index("ix_bookings_scheduled_start_status", table_name="bookings")
    op.drop_index("ix_host_profiles_verification_status", table_name="host_profiles")
    op.drop_index("ix_host_profiles_hourly_rate_cents", table_name="host_profiles")
    op.drop_index("ix_host_profiles_rating_average", table_name="host_profiles")
