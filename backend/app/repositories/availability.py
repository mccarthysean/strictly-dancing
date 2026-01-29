"""Availability repository for host schedule management."""

from datetime import date, datetime, time, timedelta
from uuid import UUID

from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.availability import (
    AvailabilityOverride,
    AvailabilityOverrideType,
    DayOfWeek,
    RecurringAvailability,
)
from app.models.booking import Booking, BookingStatus


class AvailabilityRepository:
    """Repository for host availability data access operations.

    Manages host schedules including:
    - Recurring weekly availability (e.g., "Available Mondays 9am-5pm")
    - One-time availability additions (e.g., "Available Saturday Dec 15 10am-2pm")
    - Blocked time periods (e.g., "Blocked Monday Dec 10 all day - vacation")
    - Availability checking that accounts for existing bookings

    Attributes:
        session: The async database session for executing queries.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session.

        Args:
            session: An async SQLAlchemy session.
        """
        self._session = session

    async def set_recurring_availability(
        self,
        host_profile_id: UUID,
        day_of_week: DayOfWeek,
        start_time: time,
        end_time: time,
        is_active: bool = True,
    ) -> RecurringAvailability:
        """Set or update recurring availability for a specific day.

        If recurring availability already exists for this host/day combination,
        it will be updated. Otherwise, a new record is created.

        Args:
            host_profile_id: The host profile's unique identifier.
            day_of_week: The day of the week (0=Monday, 6=Sunday).
            start_time: When availability begins.
            end_time: When availability ends.
            is_active: Whether this schedule is active (default True).

        Returns:
            The created or updated RecurringAvailability record.

        Raises:
            ValueError: If end_time is not after start_time.
        """
        if end_time <= start_time:
            raise ValueError("end_time must be after start_time")

        # Check for existing record
        stmt = select(RecurringAvailability).where(
            and_(
                RecurringAvailability.host_profile_id == str(host_profile_id),
                RecurringAvailability.day_of_week == day_of_week.value,
            )
        )
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is not None:
            # Update existing record
            existing.start_time = start_time
            existing.end_time = end_time
            existing.is_active = is_active
            await self._session.flush()
            return existing

        # Create new record
        availability = RecurringAvailability(
            host_profile_id=str(host_profile_id),
            day_of_week=day_of_week.value,
            start_time=start_time,
            end_time=end_time,
            is_active=is_active,
        )
        self._session.add(availability)
        await self._session.flush()
        return availability

    async def get_recurring_availability(
        self,
        host_profile_id: UUID,
        active_only: bool = True,
    ) -> list[RecurringAvailability]:
        """Get all recurring availability records for a host.

        Args:
            host_profile_id: The host profile's unique identifier.
            active_only: If True, only return active schedules.

        Returns:
            List of RecurringAvailability records ordered by day of week.
        """
        conditions = [RecurringAvailability.host_profile_id == str(host_profile_id)]
        if active_only:
            conditions.append(RecurringAvailability.is_active.is_(True))

        stmt = (
            select(RecurringAvailability)
            .where(and_(*conditions))
            .order_by(
                RecurringAvailability.day_of_week, RecurringAvailability.start_time
            )
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def delete_recurring_availability(
        self,
        host_profile_id: UUID,
        day_of_week: DayOfWeek,
    ) -> bool:
        """Delete recurring availability for a specific day.

        Args:
            host_profile_id: The host profile's unique identifier.
            day_of_week: The day to remove.

        Returns:
            True if a record was deleted, False if not found.
        """
        stmt = delete(RecurringAvailability).where(
            and_(
                RecurringAvailability.host_profile_id == str(host_profile_id),
                RecurringAvailability.day_of_week == day_of_week.value,
            )
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount > 0

    async def add_one_time(
        self,
        host_profile_id: UUID,
        override_date: date,
        start_time: time | None = None,
        end_time: time | None = None,
        all_day: bool = False,
        reason: str | None = None,
    ) -> AvailabilityOverride:
        """Add a one-time availability slot.

        Use this to make the host available on a date/time they wouldn't
        normally be available based on their recurring schedule.

        Args:
            host_profile_id: The host profile's unique identifier.
            override_date: The date for this availability.
            start_time: Start time (required unless all_day=True).
            end_time: End time (required unless all_day=True).
            all_day: If True, this covers the entire day.
            reason: Optional reason for this availability.

        Returns:
            The created AvailabilityOverride record.

        Raises:
            ValueError: If times are missing when not all_day, or end_time <= start_time.
        """
        if not all_day:
            if start_time is None or end_time is None:
                raise ValueError(
                    "start_time and end_time required when all_day is False"
                )
            if end_time <= start_time:
                raise ValueError("end_time must be after start_time")

        override = AvailabilityOverride(
            host_profile_id=str(host_profile_id),
            override_date=override_date,
            override_type=AvailabilityOverrideType.AVAILABLE,
            start_time=start_time if not all_day else None,
            end_time=end_time if not all_day else None,
            all_day=all_day,
            reason=reason,
        )
        self._session.add(override)
        await self._session.flush()
        return override

    async def block_time_slot(
        self,
        host_profile_id: UUID,
        override_date: date,
        start_time: time | None = None,
        end_time: time | None = None,
        all_day: bool = False,
        reason: str | None = None,
    ) -> AvailabilityOverride:
        """Block a time slot on a specific date.

        Use this for vacations, appointments, or other times when the host
        is not available despite their normal recurring schedule.

        Args:
            host_profile_id: The host profile's unique identifier.
            override_date: The date to block.
            start_time: Start time to block (required unless all_day=True).
            end_time: End time to block (required unless all_day=True).
            all_day: If True, block the entire day.
            reason: Optional reason for blocking (e.g., "Vacation").

        Returns:
            The created AvailabilityOverride record.

        Raises:
            ValueError: If times are missing when not all_day, or end_time <= start_time.
        """
        if not all_day:
            if start_time is None or end_time is None:
                raise ValueError(
                    "start_time and end_time required when all_day is False"
                )
            if end_time <= start_time:
                raise ValueError("end_time must be after start_time")

        override = AvailabilityOverride(
            host_profile_id=str(host_profile_id),
            override_date=override_date,
            override_type=AvailabilityOverrideType.BLOCKED,
            start_time=start_time if not all_day else None,
            end_time=end_time if not all_day else None,
            all_day=all_day,
            reason=reason,
        )
        self._session.add(override)
        await self._session.flush()
        return override

    async def get_overrides_for_date_range(
        self,
        host_profile_id: UUID,
        start_date: date,
        end_date: date,
        override_type: AvailabilityOverrideType | None = None,
    ) -> list[AvailabilityOverride]:
        """Get all overrides for a date range.

        Args:
            host_profile_id: The host profile's unique identifier.
            start_date: Start of the date range.
            end_date: End of the date range (inclusive).
            override_type: Filter by type (AVAILABLE or BLOCKED), or None for all.

        Returns:
            List of AvailabilityOverride records for the date range.
        """
        conditions = [
            AvailabilityOverride.host_profile_id == str(host_profile_id),
            AvailabilityOverride.override_date >= start_date,
            AvailabilityOverride.override_date <= end_date,
        ]

        if override_type is not None:
            conditions.append(AvailabilityOverride.override_type == override_type)

        stmt = (
            select(AvailabilityOverride)
            .where(and_(*conditions))
            .order_by(
                AvailabilityOverride.override_date, AvailabilityOverride.start_time
            )
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def delete_override(self, override_id: UUID) -> bool:
        """Delete a specific availability override.

        Args:
            override_id: The override's unique identifier.

        Returns:
            True if deleted, False if not found.
        """
        stmt = delete(AvailabilityOverride).where(
            AvailabilityOverride.id == str(override_id)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount > 0

    async def get_availability_for_date(
        self,
        host_profile_id: UUID,
        target_date: date,
    ) -> list[tuple[time, time]]:
        """Get available time slots for a specific date.

        This combines recurring availability with overrides:
        1. Gets the recurring availability for the day of week
        2. Adds any one-time available slots
        3. Subtracts any blocked time periods

        Note: This does NOT account for existing bookings. Use
        is_available_for_slot() to check actual availability.

        Args:
            host_profile_id: The host profile's unique identifier.
            target_date: The date to check availability for.

        Returns:
            List of (start_time, end_time) tuples representing available slots.
        """
        # Determine day of week
        day_of_week = target_date.weekday()  # 0=Monday, 6=Sunday

        # Get recurring availability for this day
        recurring_stmt = select(RecurringAvailability).where(
            and_(
                RecurringAvailability.host_profile_id == str(host_profile_id),
                RecurringAvailability.day_of_week == day_of_week,
                RecurringAvailability.is_active.is_(True),
            )
        )
        recurring_result = await self._session.execute(recurring_stmt)
        recurring = list(recurring_result.scalars().all())

        # Get overrides for this date
        overrides_stmt = select(AvailabilityOverride).where(
            and_(
                AvailabilityOverride.host_profile_id == str(host_profile_id),
                AvailabilityOverride.override_date == target_date,
            )
        )
        overrides_result = await self._session.execute(overrides_stmt)
        overrides = list(overrides_result.scalars().all())

        # Separate into available additions and blocked periods
        available_additions = [
            o
            for o in overrides
            if o.override_type == AvailabilityOverrideType.AVAILABLE
        ]
        blocked_periods = [
            o for o in overrides if o.override_type == AvailabilityOverrideType.BLOCKED
        ]

        # Check for all-day block
        for blocked in blocked_periods:
            if blocked.all_day:
                # All-day block - no availability
                return []

        # Build initial availability from recurring schedule
        available_slots: list[tuple[time, time]] = []
        for rec in recurring:
            available_slots.append((rec.start_time, rec.end_time))

        # Add one-time available periods
        for addition in available_additions:
            if addition.all_day:
                # All-day availability - use full day (8am to 10pm as reasonable defaults)
                available_slots.append((time(8, 0), time(22, 0)))
            elif addition.start_time is not None and addition.end_time is not None:
                available_slots.append((addition.start_time, addition.end_time))

        # Subtract blocked periods from available slots
        for blocked in blocked_periods:
            if blocked.start_time is not None and blocked.end_time is not None:
                available_slots = self._subtract_time_range(
                    available_slots, blocked.start_time, blocked.end_time
                )

        # Merge overlapping slots and sort
        available_slots = self._merge_time_ranges(available_slots)

        return available_slots

    def _subtract_time_range(
        self,
        slots: list[tuple[time, time]],
        block_start: time,
        block_end: time,
    ) -> list[tuple[time, time]]:
        """Subtract a blocked time range from available slots.

        Args:
            slots: Current list of available (start, end) tuples.
            block_start: Start of blocked period.
            block_end: End of blocked period.

        Returns:
            New list of available slots with blocked period removed.
        """
        result: list[tuple[time, time]] = []

        for slot_start, slot_end in slots:
            # No overlap - keep the slot
            if slot_end <= block_start or slot_start >= block_end:
                result.append((slot_start, slot_end))
            # Full overlap - slot is completely blocked
            elif slot_start >= block_start and slot_end <= block_end:
                continue
            # Block cuts the beginning
            elif slot_start >= block_start and slot_start < block_end < slot_end:
                result.append((block_end, slot_end))
            # Block cuts the end
            elif slot_start < block_start < slot_end <= block_end:
                result.append((slot_start, block_start))
            # Block is in the middle - split the slot
            elif slot_start < block_start and block_end < slot_end:
                result.append((slot_start, block_start))
                result.append((block_end, slot_end))

        return result

    def _merge_time_ranges(
        self,
        slots: list[tuple[time, time]],
    ) -> list[tuple[time, time]]:
        """Merge overlapping or adjacent time ranges.

        Args:
            slots: List of (start, end) time tuples.

        Returns:
            Merged and sorted list of non-overlapping time ranges.
        """
        if not slots:
            return []

        # Sort by start time
        sorted_slots = sorted(slots, key=lambda x: x[0])
        merged: list[tuple[time, time]] = [sorted_slots[0]]

        for current in sorted_slots[1:]:
            last = merged[-1]
            # If current overlaps or is adjacent to last, merge them
            if current[0] <= last[1]:
                merged[-1] = (last[0], max(last[1], current[1]))
            else:
                merged.append(current)

        return merged

    async def is_available_for_slot(
        self,
        host_profile_id: UUID,
        start_datetime: datetime,
        end_datetime: datetime,
    ) -> bool:
        """Check if a specific time slot is available for booking.

        This accounts for:
        1. Host's recurring availability
        2. One-time availability additions
        3. Blocked time periods
        4. Existing bookings (pending, confirmed, or in_progress)

        Args:
            host_profile_id: The host profile's unique identifier.
            start_datetime: Proposed session start time.
            end_datetime: Proposed session end time.

        Returns:
            True if the slot is available, False otherwise.

        Raises:
            ValueError: If end_datetime is not after start_datetime.
        """
        if end_datetime <= start_datetime:
            raise ValueError("end_datetime must be after start_datetime")

        target_date = start_datetime.date()
        start_time = start_datetime.time()
        end_time = end_datetime.time()

        # Handle bookings that span midnight (simplification: don't allow for now)
        if end_datetime.date() != target_date:
            # For simplicity, require bookings to be on the same day
            return False

        # Get available slots for the date (accounts for recurring + overrides)
        available_slots = await self.get_availability_for_date(
            host_profile_id, target_date
        )

        # Check if requested time falls within any available slot
        slot_available = False
        for avail_start, avail_end in available_slots:
            if start_time >= avail_start and end_time <= avail_end:
                slot_available = True
                break

        if not slot_available:
            return False

        # Check for conflicting bookings
        # A booking conflicts if it overlaps with the requested time and is not cancelled/disputed
        conflicting_stmt = select(Booking).where(
            and_(
                Booking.host_profile_id == str(host_profile_id),
                Booking.status.in_(
                    [
                        BookingStatus.PENDING,
                        BookingStatus.CONFIRMED,
                        BookingStatus.IN_PROGRESS,
                    ]
                ),
                # Overlap check: NOT (booking ends before requested start OR booking starts after requested end)
                # Which is: booking_start < requested_end AND booking_end > requested_start
                Booking.scheduled_start < end_datetime,
                Booking.scheduled_end > start_datetime,
            )
        )
        conflicting_result = await self._session.execute(conflicting_stmt)
        conflicting_booking = conflicting_result.scalar_one_or_none()

        return conflicting_booking is None

    async def get_bookings_for_date_range(
        self,
        host_profile_id: UUID,
        start_date: date,
        end_date: date,
        include_cancelled: bool = False,
    ) -> list[Booking]:
        """Get all bookings for a host in a date range.

        Used to show booked slots on a calendar.

        Args:
            host_profile_id: The host profile's unique identifier.
            start_date: Start of the date range.
            end_date: End of the date range (inclusive).
            include_cancelled: If True, include cancelled bookings.

        Returns:
            List of Booking records in the date range.
        """
        # Convert dates to datetimes for comparison
        start_datetime = datetime.combine(start_date, time.min)
        end_datetime = datetime.combine(end_date + timedelta(days=1), time.min)

        conditions = [
            Booking.host_profile_id == str(host_profile_id),
            Booking.scheduled_start < end_datetime,
            Booking.scheduled_end > start_datetime,
        ]

        if not include_cancelled:
            conditions.append(
                Booking.status.notin_([BookingStatus.CANCELLED, BookingStatus.DISPUTED])
            )

        stmt = (
            select(Booking).where(and_(*conditions)).order_by(Booking.scheduled_start)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def clear_recurring_availability(self, host_profile_id: UUID) -> int:
        """Delete all recurring availability for a host.

        Args:
            host_profile_id: The host profile's unique identifier.

        Returns:
            Number of records deleted.
        """
        stmt = delete(RecurringAvailability).where(
            RecurringAvailability.host_profile_id == str(host_profile_id)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount

    async def set_weekly_schedule(
        self,
        host_profile_id: UUID,
        schedule: dict[DayOfWeek, list[tuple[time, time]]],
        clear_existing: bool = True,
    ) -> list[RecurringAvailability]:
        """Set the complete weekly schedule for a host.

        This is a convenience method to set multiple days at once.

        Args:
            host_profile_id: The host profile's unique identifier.
            schedule: Dict mapping day of week to list of (start_time, end_time) tuples.
            clear_existing: If True, delete all existing recurring availability first.

        Returns:
            List of created RecurringAvailability records.
        """
        if clear_existing:
            await self.clear_recurring_availability(host_profile_id)

        created = []
        for day, time_slots in schedule.items():
            for start_t, end_t in time_slots:
                rec = await self.set_recurring_availability(
                    host_profile_id=host_profile_id,
                    day_of_week=day,
                    start_time=start_t,
                    end_time=end_t,
                    is_active=True,
                )
                created.append(rec)

        return created
