"""Booking repository for data access operations."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.booking import Booking, BookingStatus


class BookingRepository:
    """Repository for Booking CRUD operations.

    Implements the repository pattern for booking data access,
    providing an abstraction layer over SQLAlchemy operations.

    All methods use async patterns for non-blocking database access.

    Attributes:
        session: The async database session for executing queries.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session.

        Args:
            session: An async SQLAlchemy session.
        """
        self._session = session

    async def create(
        self,
        *,
        client_id: UUID,
        host_id: UUID,
        host_profile_id: UUID,
        scheduled_start: datetime,
        scheduled_end: datetime,
        duration_minutes: int,
        hourly_rate_cents: int,
        amount_cents: int,
        platform_fee_cents: int = 0,
        host_payout_cents: int = 0,
        dance_style_id: UUID | None = None,
        location: str | None = None,
        location_name: str | None = None,
        location_notes: str | None = None,
        client_notes: str | None = None,
        stripe_payment_intent_id: str | None = None,
    ) -> Booking:
        """Create a new booking in the database.

        Args:
            client_id: The client's user ID.
            host_id: The host's user ID.
            host_profile_id: The host profile ID.
            scheduled_start: When the session is scheduled to start.
            scheduled_end: When the session is scheduled to end.
            duration_minutes: Duration of the session in minutes.
            hourly_rate_cents: Host's hourly rate at booking time (in cents).
            amount_cents: Total amount for the session (in cents).
            platform_fee_cents: Platform fee (in cents), default 0.
            host_payout_cents: Amount to be paid to host (in cents), default 0.
            dance_style_id: Optional dance style for the session.
            location: Optional PostGIS POINT location.
            location_name: Optional human-readable location name.
            location_notes: Optional location instructions.
            client_notes: Optional notes from the client.
            stripe_payment_intent_id: Optional Stripe PaymentIntent ID.

        Returns:
            The newly created Booking instance with status PENDING.
        """
        booking = Booking(
            client_id=str(client_id),
            host_id=str(host_id),
            host_profile_id=str(host_profile_id),
            dance_style_id=str(dance_style_id) if dance_style_id else None,
            status=BookingStatus.PENDING,
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            duration_minutes=duration_minutes,
            hourly_rate_cents=hourly_rate_cents,
            amount_cents=amount_cents,
            platform_fee_cents=platform_fee_cents,
            host_payout_cents=host_payout_cents,
            location=location,
            location_name=location_name,
            location_notes=location_notes,
            client_notes=client_notes,
            stripe_payment_intent_id=stripe_payment_intent_id,
        )
        self._session.add(booking)
        await self._session.flush()
        return booking

    async def get_by_id(
        self,
        booking_id: UUID,
        *,
        load_relationships: bool = True,
    ) -> Booking | None:
        """Get a booking by its UUID.

        Args:
            booking_id: The booking's unique identifier.
            load_relationships: If True, eagerly load related entities.

        Returns:
            The Booking if found, None otherwise.
        """
        stmt = select(Booking).where(Booking.id == str(booking_id))

        if load_relationships:
            stmt = stmt.options(
                joinedload(Booking.client),
                joinedload(Booking.host),
                joinedload(Booking.host_profile),
                joinedload(Booking.dance_style),
            )

        result = await self._session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_for_client(
        self,
        client_id: UUID,
        *,
        status: BookingStatus | list[BookingStatus] | None = None,
        limit: int = 50,
        offset: int = 0,
        load_relationships: bool = True,
    ) -> list[Booking]:
        """Get all bookings for a client.

        Args:
            client_id: The client's user ID.
            status: Filter by status (single status or list of statuses).
            limit: Maximum number of bookings to return.
            offset: Number of bookings to skip.
            load_relationships: If True, eagerly load related entities.

        Returns:
            List of Booking records ordered by scheduled_start descending.
        """
        conditions = [Booking.client_id == str(client_id)]

        if status is not None:
            if isinstance(status, list):
                conditions.append(Booking.status.in_(status))
            else:
                conditions.append(Booking.status == status)

        stmt = (
            select(Booking)
            .where(and_(*conditions))
            .order_by(Booking.scheduled_start.desc())
            .limit(limit)
            .offset(offset)
        )

        if load_relationships:
            stmt = stmt.options(
                joinedload(Booking.client),
                joinedload(Booking.host),
                joinedload(Booking.host_profile),
                joinedload(Booking.dance_style),
            )

        result = await self._session.execute(stmt)
        return list(result.unique().scalars().all())

    async def get_for_host(
        self,
        host_id: UUID,
        *,
        status: BookingStatus | list[BookingStatus] | None = None,
        limit: int = 50,
        offset: int = 0,
        load_relationships: bool = True,
    ) -> list[Booking]:
        """Get all bookings for a host.

        Args:
            host_id: The host's user ID.
            status: Filter by status (single status or list of statuses).
            limit: Maximum number of bookings to return.
            offset: Number of bookings to skip.
            load_relationships: If True, eagerly load related entities.

        Returns:
            List of Booking records ordered by scheduled_start descending.
        """
        conditions = [Booking.host_id == str(host_id)]

        if status is not None:
            if isinstance(status, list):
                conditions.append(Booking.status.in_(status))
            else:
                conditions.append(Booking.status == status)

        stmt = (
            select(Booking)
            .where(and_(*conditions))
            .order_by(Booking.scheduled_start.desc())
            .limit(limit)
            .offset(offset)
        )

        if load_relationships:
            stmt = stmt.options(
                joinedload(Booking.client),
                joinedload(Booking.host),
                joinedload(Booking.host_profile),
                joinedload(Booking.dance_style),
            )

        result = await self._session.execute(stmt)
        return list(result.unique().scalars().all())

    async def get_for_user(
        self,
        user_id: UUID,
        *,
        status: BookingStatus | list[BookingStatus] | None = None,
        limit: int = 50,
        offset: int = 0,
        load_relationships: bool = True,
    ) -> list[Booking]:
        """Get all bookings for a user (as either client or host).

        Args:
            user_id: The user's ID.
            status: Filter by status (single status or list of statuses).
            limit: Maximum number of bookings to return.
            offset: Number of bookings to skip.
            load_relationships: If True, eagerly load related entities.

        Returns:
            List of Booking records ordered by scheduled_start descending.
        """
        user_id_str = str(user_id)
        conditions = [
            or_(
                Booking.client_id == user_id_str,
                Booking.host_id == user_id_str,
            )
        ]

        if status is not None:
            if isinstance(status, list):
                conditions.append(Booking.status.in_(status))
            else:
                conditions.append(Booking.status == status)

        stmt = (
            select(Booking)
            .where(and_(*conditions))
            .order_by(Booking.scheduled_start.desc())
            .limit(limit)
            .offset(offset)
        )

        if load_relationships:
            stmt = stmt.options(
                joinedload(Booking.client),
                joinedload(Booking.host),
                joinedload(Booking.host_profile),
                joinedload(Booking.dance_style),
            )

        result = await self._session.execute(stmt)
        return list(result.unique().scalars().all())

    async def update_status(
        self,
        booking_id: UUID,
        status: BookingStatus,
        *,
        cancelled_by_id: UUID | None = None,
        cancellation_reason: str | None = None,
        actual_start: datetime | None = None,
        actual_end: datetime | None = None,
        stripe_transfer_id: str | None = None,
    ) -> Booking | None:
        """Update a booking's status.

        Args:
            booking_id: The booking's unique identifier.
            status: The new status to set.
            cancelled_by_id: User ID of who cancelled (for CANCELLED status).
            cancellation_reason: Reason for cancellation (for CANCELLED status).
            actual_start: Actual start time (for IN_PROGRESS status).
            actual_end: Actual end time (for COMPLETED status).
            stripe_transfer_id: Stripe Transfer ID (for COMPLETED status).

        Returns:
            The updated Booking if found, None otherwise.
        """
        booking = await self.get_by_id(booking_id, load_relationships=False)
        if booking is None:
            return None

        booking.status = status

        if status == BookingStatus.CANCELLED:
            booking.cancelled_at = datetime.now(UTC)
            if cancelled_by_id is not None:
                booking.cancelled_by_id = str(cancelled_by_id)
            if cancellation_reason is not None:
                booking.cancellation_reason = cancellation_reason

        if status == BookingStatus.IN_PROGRESS and actual_start is not None:
            booking.actual_start = actual_start

        if status == BookingStatus.COMPLETED:
            if actual_end is not None:
                booking.actual_end = actual_end
            if stripe_transfer_id is not None:
                booking.stripe_transfer_id = stripe_transfer_id

        await self._session.flush()
        return booking

    async def get_overlapping(
        self,
        host_profile_id: UUID,
        start_datetime: datetime,
        end_datetime: datetime,
        *,
        exclude_booking_id: UUID | None = None,
        active_only: bool = True,
    ) -> list[Booking]:
        """Get bookings that overlap with a given time range.

        A booking overlaps if:
        - booking_start < requested_end AND booking_end > requested_start

        Args:
            host_profile_id: The host profile's unique identifier.
            start_datetime: Start of the time range to check.
            end_datetime: End of the time range to check.
            exclude_booking_id: Optional booking ID to exclude from results.
            active_only: If True, only include pending/confirmed/in_progress.

        Returns:
            List of overlapping Booking records.
        """
        conditions = [
            Booking.host_profile_id == str(host_profile_id),
            Booking.scheduled_start < end_datetime,
            Booking.scheduled_end > start_datetime,
        ]

        if active_only:
            conditions.append(
                Booking.status.in_(
                    [
                        BookingStatus.PENDING,
                        BookingStatus.CONFIRMED,
                        BookingStatus.IN_PROGRESS,
                    ]
                )
            )

        if exclude_booking_id is not None:
            conditions.append(Booking.id != str(exclude_booking_id))

        stmt = (
            select(Booking).where(and_(*conditions)).order_by(Booking.scheduled_start)
        )

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_upcoming(
        self,
        user_id: UUID,
        *,
        as_host: bool = False,
        as_client: bool = False,
        limit: int = 10,
        load_relationships: bool = True,
    ) -> list[Booking]:
        """Get upcoming bookings for a user.

        Returns only confirmed bookings scheduled in the future,
        ordered by scheduled_start ascending (soonest first).

        Args:
            user_id: The user's ID.
            as_host: If True, get bookings where user is the host.
            as_client: If True, get bookings where user is the client.
            limit: Maximum number of bookings to return.
            load_relationships: If True, eagerly load related entities.

        Returns:
            List of upcoming Booking records.

        Note:
            If neither as_host nor as_client is True, returns bookings
            where user is either client or host.
        """
        now = datetime.now(UTC)
        user_id_str = str(user_id)

        # Build user condition based on flags
        if as_host and not as_client:
            user_condition = Booking.host_id == user_id_str
        elif as_client and not as_host:
            user_condition = Booking.client_id == user_id_str
        else:
            # Both or neither - get all bookings for user
            user_condition = or_(
                Booking.client_id == user_id_str,
                Booking.host_id == user_id_str,
            )

        conditions = [
            user_condition,
            Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PENDING]),
            Booking.scheduled_start > now,
        ]

        stmt = (
            select(Booking)
            .where(and_(*conditions))
            .order_by(Booking.scheduled_start.asc())
            .limit(limit)
        )

        if load_relationships:
            stmt = stmt.options(
                joinedload(Booking.client),
                joinedload(Booking.host),
                joinedload(Booking.host_profile),
                joinedload(Booking.dance_style),
            )

        result = await self._session.execute(stmt)
        return list(result.unique().scalars().all())

    async def count_for_client(
        self,
        client_id: UUID,
        *,
        status: BookingStatus | list[BookingStatus] | None = None,
    ) -> int:
        """Count bookings for a client.

        Args:
            client_id: The client's user ID.
            status: Filter by status (single status or list of statuses).

        Returns:
            Number of matching bookings.
        """
        from sqlalchemy import func as sql_func

        conditions = [Booking.client_id == str(client_id)]

        if status is not None:
            if isinstance(status, list):
                conditions.append(Booking.status.in_(status))
            else:
                conditions.append(Booking.status == status)

        stmt = select(sql_func.count()).select_from(Booking).where(and_(*conditions))
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def count_for_host(
        self,
        host_id: UUID,
        *,
        status: BookingStatus | list[BookingStatus] | None = None,
    ) -> int:
        """Count bookings for a host.

        Args:
            host_id: The host's user ID.
            status: Filter by status (single status or list of statuses).

        Returns:
            Number of matching bookings.
        """
        from sqlalchemy import func as sql_func

        conditions = [Booking.host_id == str(host_id)]

        if status is not None:
            if isinstance(status, list):
                conditions.append(Booking.status.in_(status))
            else:
                conditions.append(Booking.status == status)

        stmt = select(sql_func.count()).select_from(Booking).where(and_(*conditions))
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def update_stripe_payment_intent(
        self,
        booking_id: UUID,
        stripe_payment_intent_id: str,
    ) -> Booking | None:
        """Update a booking's Stripe PaymentIntent ID.

        Args:
            booking_id: The booking's unique identifier.
            stripe_payment_intent_id: The Stripe PaymentIntent ID.

        Returns:
            The updated Booking if found, None otherwise.
        """
        booking = await self.get_by_id(booking_id, load_relationships=False)
        if booking is None:
            return None

        booking.stripe_payment_intent_id = stripe_payment_intent_id
        await self._session.flush()
        return booking

    async def add_host_notes(
        self,
        booking_id: UUID,
        notes: str,
    ) -> Booking | None:
        """Add or update host notes for a booking.

        Args:
            booking_id: The booking's unique identifier.
            notes: The notes to add.

        Returns:
            The updated Booking if found, None otherwise.
        """
        booking = await self.get_by_id(booking_id, load_relationships=False)
        if booking is None:
            return None

        booking.host_notes = notes
        await self._session.flush()
        return booking
