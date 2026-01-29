"""Booking database model."""

import enum
from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class BookingStatus(str, enum.Enum):
    """Booking status enumeration."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"


class Booking(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Booking model.

    Represents a dance session booking between a client and a host.

    Attributes:
        id: UUID primary key
        client_id: Foreign key to users table (the client booking the session)
        host_id: Foreign key to users table (the host providing the session)
        host_profile_id: Foreign key to host_profiles table
        dance_style_id: Foreign key to dance_styles table (optional)
        status: Current booking status
        scheduled_start: Scheduled start time for the session
        scheduled_end: Scheduled end time for the session
        actual_start: Actual start time when session began
        actual_end: Actual end time when session ended
        duration_minutes: Duration of the session in minutes
        location: PostGIS GEOGRAPHY(POINT) for session location
        location_name: Human-readable location name/address
        location_notes: Additional location instructions
        hourly_rate_cents: Host's hourly rate at time of booking (in cents)
        amount_cents: Total amount for the session (in cents)
        platform_fee_cents: Platform fee (in cents)
        host_payout_cents: Amount to be paid to host (in cents)
        stripe_payment_intent_id: Stripe PaymentIntent ID for this booking
        stripe_transfer_id: Stripe Transfer ID for host payout
        client_notes: Notes from the client
        host_notes: Notes from the host
        cancellation_reason: Reason for cancellation (if applicable)
        cancelled_by_id: User ID of who cancelled (if applicable)
        cancelled_at: When the booking was cancelled
        created_at: When the booking was created
        updated_at: When the booking was last updated
    """

    __tablename__ = "bookings"

    # Foreign keys to users (client and host)
    client_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    host_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Foreign key to host profile
    host_profile_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("host_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Foreign key to dance style (optional - session may not be style-specific)
    dance_style_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("dance_styles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Booking status
    status: Mapped[BookingStatus] = mapped_column(
        ENUM(BookingStatus, name="booking_status_enum", create_type=True),
        nullable=False,
        default=BookingStatus.PENDING,
        index=True,
    )

    # Scheduling
    scheduled_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    scheduled_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    actual_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    actual_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    duration_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # Location (PostGIS GEOGRAPHY for accurate distance calculations)
    location: Mapped[str | None] = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=True,
    )
    location_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    location_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Pricing (all amounts in cents to avoid floating point issues)
    hourly_rate_cents: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    amount_cents: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    platform_fee_cents: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    host_payout_cents: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Stripe integration
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )
    stripe_transfer_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Notes
    client_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    host_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Cancellation tracking
    cancellation_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    cancelled_by_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    client = relationship(
        "User",
        foreign_keys=[client_id],
        backref="client_bookings",
        lazy="joined",
    )
    host = relationship(
        "User",
        foreign_keys=[host_id],
        backref="host_bookings",
        lazy="joined",
    )
    host_profile = relationship(
        "HostProfile",
        backref="bookings",
        lazy="joined",
    )
    dance_style = relationship(
        "DanceStyle",
        backref="bookings",
        lazy="joined",
    )
    cancelled_by = relationship(
        "User",
        foreign_keys=[cancelled_by_id],
        lazy="joined",
    )

    def __repr__(self) -> str:
        return f"<Booking(id={self.id}, client={self.client_id}, host={self.host_id}, status={self.status})>"
