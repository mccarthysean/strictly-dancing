"""Availability database models for host scheduling.

This module provides two models for managing host availability:
1. RecurringAvailability - Weekly recurring schedules (e.g., "Available Mondays 9am-5pm")
2. AvailabilityOverride - One-time overrides and blocked periods
"""

import enum
from datetime import date, time

from sqlalchemy import Boolean, Date, ForeignKey, Index, Integer, Text, Time
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DayOfWeek(int, enum.Enum):
    """Day of week enumeration (0=Monday, 6=Sunday)."""

    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


class AvailabilityOverrideType(str, enum.Enum):
    """Type of availability override."""

    AVAILABLE = "available"  # Add availability on this date/time
    BLOCKED = "blocked"  # Block availability on this date/time


class RecurringAvailability(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Recurring weekly availability schedule for a host.

    Represents when a host is regularly available each week.
    For example, "Available every Monday from 9am to 5pm".

    Attributes:
        id: UUID primary key
        host_profile_id: Foreign key to host_profiles table
        day_of_week: Day of week (0=Monday, 6=Sunday)
        start_time: Time availability begins
        end_time: Time availability ends
        is_active: Whether this schedule is currently active
        created_at: When the record was created
        updated_at: When the record was last updated
    """

    __tablename__ = "recurring_availability"

    host_profile_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("host_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    day_of_week: Mapped[DayOfWeek] = mapped_column(
        Integer,
        nullable=False,
    )

    start_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    end_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    # Relationships
    host_profile = relationship(
        "HostProfile",
        backref="recurring_availability",
        lazy="joined",
    )

    # Indexes
    __table_args__ = (
        Index(
            "ix_recurring_availability_host_day",
            "host_profile_id",
            "day_of_week",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<RecurringAvailability(id={self.id}, "
            f"day={self.day_of_week.name if isinstance(self.day_of_week, DayOfWeek) else self.day_of_week}, "
            f"time={self.start_time}-{self.end_time})>"
        )


class AvailabilityOverride(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """One-time availability override for a specific date.

    Used for:
    - Adding one-time available slots on dates outside regular schedule
    - Blocking time on specific dates (vacation, appointments, etc.)

    Attributes:
        id: UUID primary key
        host_profile_id: Foreign key to host_profiles table
        override_date: The specific date this override applies to
        override_type: Whether this adds availability or blocks time
        start_time: Start time of the override (null for all-day)
        end_time: End time of the override (null for all-day)
        all_day: Whether this override applies to the entire day
        reason: Optional reason for the override (e.g., "Vacation")
        created_at: When the record was created
        updated_at: When the record was last updated
    """

    __tablename__ = "availability_overrides"

    host_profile_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("host_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    override_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    override_type: Mapped[AvailabilityOverrideType] = mapped_column(
        ENUM(
            AvailabilityOverrideType,
            name="availability_override_type_enum",
            create_type=True,
        ),
        nullable=False,
    )

    start_time: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )

    end_time: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )

    all_day: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    host_profile = relationship(
        "HostProfile",
        backref="availability_overrides",
        lazy="joined",
    )

    # Indexes
    __table_args__ = (
        Index(
            "ix_availability_overrides_host_date",
            "host_profile_id",
            "override_date",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<AvailabilityOverride(id={self.id}, "
            f"date={self.override_date}, "
            f"type={self.override_type.value if isinstance(self.override_type, AvailabilityOverrideType) else self.override_type})>"
        )
