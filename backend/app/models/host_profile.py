"""Host profile database model."""

import enum

from geoalchemy2 import Geography
from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class VerificationStatus(str, enum.Enum):
    """Host verification status enumeration."""

    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class HostProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Host profile model.

    Represents a host's public profile on the Strictly Dancing platform.
    Contains additional information beyond the base user account required
    to offer dance hosting services.

    Attributes:
        id: UUID primary key
        user_id: Foreign key to users table (one-to-one relationship)
        bio: Host's biography/description
        headline: Short tagline for profile display
        hourly_rate_cents: Hourly rate in cents (e.g., 5000 = $50.00)
        rating_average: Average rating from reviews (1.00-5.00)
        total_reviews: Number of reviews received
        total_sessions: Number of completed sessions
        verification_status: Current verification status
        location: PostGIS GEOGRAPHY(POINT) for geospatial queries
        stripe_account_id: Stripe Connect account ID for payments
        stripe_onboarding_complete: Whether Stripe onboarding is finished
        created_at: When the profile was created
        updated_at: When the profile was last updated
    """

    __tablename__ = "host_profiles"

    # Foreign key to user (one-to-one relationship)
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # Profile information
    bio: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    headline: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    # Pricing (in cents to avoid floating point issues)
    hourly_rate_cents: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5000,  # $50.00 default
    )

    # Statistics
    rating_average: Mapped[float | None] = mapped_column(
        Numeric(3, 2),  # e.g., 4.75
        nullable=True,
    )
    total_reviews: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    total_sessions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Verification
    verification_status: Mapped[VerificationStatus] = mapped_column(
        ENUM(VerificationStatus, name="verification_status_enum", create_type=True),
        nullable=False,
        default=VerificationStatus.UNVERIFIED,
    )

    # Location (PostGIS GEOGRAPHY for accurate distance calculations)
    # GEOGRAPHY(POINT, 4326) uses WGS84 coordinate system (standard GPS)
    location: Mapped[str | None] = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=True,
    )

    # Stripe Connect integration
    stripe_account_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    stripe_onboarding_complete: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )

    # Relationship to User (back_populates would be defined on User if needed)
    user = relationship("User", backref="host_profile", uselist=False, lazy="joined")

    def __repr__(self) -> str:
        return f"<HostProfile(id={self.id}, user_id={self.user_id}, rate={self.hourly_rate_cents})>"
