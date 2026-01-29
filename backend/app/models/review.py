"""Review database model."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Review(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Review model.

    Represents a review left after a completed dance session.
    Clients can review hosts, and hosts can leave a response.

    Attributes:
        id: UUID primary key
        booking_id: Foreign key to bookings table (unique - one review per booking)
        reviewer_id: Foreign key to users table (the person leaving the review)
        reviewee_id: Foreign key to users table (the person being reviewed)
        rating: Rating from 1 to 5 stars
        comment: Review text content
        host_response: Host's response to the review (optional)
        host_responded_at: When the host responded
        created_at: When the review was created
        updated_at: When the review was last updated
    """

    __tablename__ = "reviews"

    # Foreign key to booking (unique - one review per booking)
    booking_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # Foreign key to reviewer (the person leaving the review)
    reviewer_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Foreign key to reviewee (the person being reviewed, typically the host)
    reviewee_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Rating (1-5 stars)
    rating: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # Review comment
    comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Host response to the review
    host_response: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    host_responded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="rating_range_1_to_5"),
    )

    # Relationships
    booking = relationship(
        "Booking",
        backref="review",
        uselist=False,
        lazy="joined",
    )
    reviewer = relationship(
        "User",
        foreign_keys=[reviewer_id],
        backref="reviews_given",
        lazy="joined",
    )
    reviewee = relationship(
        "User",
        foreign_keys=[reviewee_id],
        backref="reviews_received",
        lazy="joined",
    )

    def __repr__(self) -> str:
        return f"<Review(id={self.id}, booking_id={self.booking_id}, rating={self.rating})>"
