"""Unit tests for AvailabilityRepository."""

import inspect
import uuid
from datetime import UTC, date, datetime, time
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.availability import (
    AvailabilityOverride,
    AvailabilityOverrideType,
    DayOfWeek,
    RecurringAvailability,
)
from app.models.booking import Booking, BookingStatus
from app.repositories.availability import AvailabilityRepository


@pytest.fixture
def mock_session():
    """Create a mock async session."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def availability_repository(mock_session):
    """Create an AvailabilityRepository with a mock session."""
    return AvailabilityRepository(mock_session)


@pytest.fixture
def sample_host_profile_id():
    """Create a sample host profile ID."""
    return uuid.uuid4()


@pytest.fixture
def sample_recurring_availability(sample_host_profile_id):
    """Create a sample recurring availability."""
    return RecurringAvailability(
        id=uuid.uuid4(),
        host_profile_id=str(sample_host_profile_id),
        day_of_week=DayOfWeek.MONDAY.value,
        start_time=time(9, 0),
        end_time=time(17, 0),
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_availability_override(sample_host_profile_id):
    """Create a sample availability override."""
    return AvailabilityOverride(
        id=uuid.uuid4(),
        host_profile_id=str(sample_host_profile_id),
        override_date=date(2026, 2, 1),
        override_type=AvailabilityOverrideType.AVAILABLE,
        start_time=time(10, 0),
        end_time=time(14, 0),
        all_day=False,
        reason="Special availability",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_blocked_override(sample_host_profile_id):
    """Create a sample blocked availability override."""
    return AvailabilityOverride(
        id=uuid.uuid4(),
        host_profile_id=str(sample_host_profile_id),
        override_date=date(2026, 2, 10),
        override_type=AvailabilityOverrideType.BLOCKED,
        start_time=None,
        end_time=None,
        all_day=True,
        reason="Vacation",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_booking(sample_host_profile_id):
    """Create a sample booking."""
    return Booking(
        id=uuid.uuid4(),
        client_id=str(uuid.uuid4()),
        host_id=str(uuid.uuid4()),
        host_profile_id=str(sample_host_profile_id),
        status=BookingStatus.CONFIRMED,
        scheduled_start=datetime(2026, 2, 3, 10, 0, tzinfo=UTC),
        scheduled_end=datetime(2026, 2, 3, 12, 0, tzinfo=UTC),
        duration_minutes=120,
        hourly_rate_cents=5000,
        amount_cents=10000,
        platform_fee_cents=1500,
        host_payout_cents=8500,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


class TestSetRecurringAvailability:
    """Tests for AvailabilityRepository.set_recurring_availability() method."""

    async def test_create_new_recurring_availability(
        self, availability_repository, mock_session, sample_host_profile_id
    ):
        """Test creating new recurring availability."""
        # Mock no existing record
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await availability_repository.set_recurring_availability(
            host_profile_id=sample_host_profile_id,
            day_of_week=DayOfWeek.MONDAY,
            start_time=time(9, 0),
            end_time=time(17, 0),
        )

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        assert result.host_profile_id == str(sample_host_profile_id)
        assert result.day_of_week == DayOfWeek.MONDAY.value
        assert result.start_time == time(9, 0)
        assert result.end_time == time(17, 0)
        assert result.is_active is True

    async def test_update_existing_recurring_availability(
        self, availability_repository, mock_session, sample_recurring_availability
    ):
        """Test updating existing recurring availability."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_recurring_availability
        mock_session.execute.return_value = mock_result

        result = await availability_repository.set_recurring_availability(
            host_profile_id=uuid.UUID(sample_recurring_availability.host_profile_id),
            day_of_week=DayOfWeek.MONDAY,
            start_time=time(10, 0),
            end_time=time(18, 0),
        )

        mock_session.add.assert_not_called()  # Update, not add
        mock_session.flush.assert_called_once()
        assert result.start_time == time(10, 0)
        assert result.end_time == time(18, 0)

    async def test_set_recurring_availability_invalid_time_range(
        self, availability_repository, sample_host_profile_id
    ):
        """Test that end_time must be after start_time."""
        with pytest.raises(ValueError, match="end_time must be after start_time"):
            await availability_repository.set_recurring_availability(
                host_profile_id=sample_host_profile_id,
                day_of_week=DayOfWeek.MONDAY,
                start_time=time(17, 0),
                end_time=time(9, 0),
            )

    async def test_set_recurring_availability_equal_times(
        self, availability_repository, sample_host_profile_id
    ):
        """Test that end_time cannot equal start_time."""
        with pytest.raises(ValueError, match="end_time must be after start_time"):
            await availability_repository.set_recurring_availability(
                host_profile_id=sample_host_profile_id,
                day_of_week=DayOfWeek.MONDAY,
                start_time=time(9, 0),
                end_time=time(9, 0),
            )

    async def test_set_recurring_availability_inactive(
        self, availability_repository, mock_session, sample_host_profile_id
    ):
        """Test setting recurring availability as inactive."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await availability_repository.set_recurring_availability(
            host_profile_id=sample_host_profile_id,
            day_of_week=DayOfWeek.FRIDAY,
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_active=False,
        )

        assert result.is_active is False


class TestGetRecurringAvailability:
    """Tests for AvailabilityRepository.get_recurring_availability() method."""

    async def test_get_recurring_availability_success(
        self,
        availability_repository,
        mock_session,
        sample_host_profile_id,
        sample_recurring_availability,
    ):
        """Test getting recurring availability for a host."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            sample_recurring_availability
        ]
        mock_session.execute.return_value = mock_result

        result = await availability_repository.get_recurring_availability(
            sample_host_profile_id
        )

        assert len(result) == 1
        assert result[0] == sample_recurring_availability

    async def test_get_recurring_availability_empty(
        self, availability_repository, mock_session, sample_host_profile_id
    ):
        """Test getting recurring availability when none exists."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await availability_repository.get_recurring_availability(
            sample_host_profile_id
        )

        assert len(result) == 0

    async def test_get_recurring_availability_include_inactive(
        self,
        availability_repository,
        mock_session,
        sample_host_profile_id,
        sample_recurring_availability,
    ):
        """Test getting all recurring availability including inactive."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            sample_recurring_availability
        ]
        mock_session.execute.return_value = mock_result

        result = await availability_repository.get_recurring_availability(
            sample_host_profile_id, active_only=False
        )

        assert len(result) == 1


class TestDeleteRecurringAvailability:
    """Tests for AvailabilityRepository.delete_recurring_availability() method."""

    async def test_delete_recurring_availability_success(
        self, availability_repository, mock_session, sample_host_profile_id
    ):
        """Test deleting recurring availability."""
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        result = await availability_repository.delete_recurring_availability(
            sample_host_profile_id, DayOfWeek.MONDAY
        )

        assert result is True
        mock_session.flush.assert_called_once()

    async def test_delete_recurring_availability_not_found(
        self, availability_repository, mock_session, sample_host_profile_id
    ):
        """Test deleting non-existent recurring availability."""
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result

        result = await availability_repository.delete_recurring_availability(
            sample_host_profile_id, DayOfWeek.SUNDAY
        )

        assert result is False


class TestAddOneTime:
    """Tests for AvailabilityRepository.add_one_time() method."""

    async def test_add_one_time_availability(
        self, availability_repository, mock_session, sample_host_profile_id
    ):
        """Test adding one-time availability."""
        result = await availability_repository.add_one_time(
            host_profile_id=sample_host_profile_id,
            override_date=date(2026, 2, 15),
            start_time=time(10, 0),
            end_time=time(14, 0),
            reason="Special session",
        )

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        assert result.override_type == AvailabilityOverrideType.AVAILABLE
        assert result.override_date == date(2026, 2, 15)
        assert result.start_time == time(10, 0)
        assert result.end_time == time(14, 0)
        assert result.all_day is False
        assert result.reason == "Special session"

    async def test_add_one_time_all_day(
        self, availability_repository, mock_session, sample_host_profile_id
    ):
        """Test adding all-day one-time availability."""
        result = await availability_repository.add_one_time(
            host_profile_id=sample_host_profile_id,
            override_date=date(2026, 2, 20),
            all_day=True,
            reason="Available all day",
        )

        assert result.all_day is True
        assert result.start_time is None
        assert result.end_time is None

    async def test_add_one_time_missing_times_error(
        self, availability_repository, sample_host_profile_id
    ):
        """Test error when times are missing for non-all-day."""
        with pytest.raises(
            ValueError, match="start_time and end_time required when all_day is False"
        ):
            await availability_repository.add_one_time(
                host_profile_id=sample_host_profile_id,
                override_date=date(2026, 2, 15),
                all_day=False,
            )

    async def test_add_one_time_invalid_time_range(
        self, availability_repository, sample_host_profile_id
    ):
        """Test error when end_time is before start_time."""
        with pytest.raises(ValueError, match="end_time must be after start_time"):
            await availability_repository.add_one_time(
                host_profile_id=sample_host_profile_id,
                override_date=date(2026, 2, 15),
                start_time=time(14, 0),
                end_time=time(10, 0),
            )


class TestBlockTimeSlot:
    """Tests for AvailabilityRepository.block_time_slot() method."""

    async def test_block_time_slot(
        self, availability_repository, mock_session, sample_host_profile_id
    ):
        """Test blocking a time slot."""
        result = await availability_repository.block_time_slot(
            host_profile_id=sample_host_profile_id,
            override_date=date(2026, 3, 1),
            start_time=time(12, 0),
            end_time=time(14, 0),
            reason="Doctor appointment",
        )

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        assert result.override_type == AvailabilityOverrideType.BLOCKED
        assert result.start_time == time(12, 0)
        assert result.end_time == time(14, 0)
        assert result.reason == "Doctor appointment"

    async def test_block_all_day(
        self, availability_repository, mock_session, sample_host_profile_id
    ):
        """Test blocking an entire day."""
        result = await availability_repository.block_time_slot(
            host_profile_id=sample_host_profile_id,
            override_date=date(2026, 3, 5),
            all_day=True,
            reason="Vacation",
        )

        assert result.all_day is True
        assert result.override_type == AvailabilityOverrideType.BLOCKED

    async def test_block_missing_times_error(
        self, availability_repository, sample_host_profile_id
    ):
        """Test error when times are missing for non-all-day block."""
        with pytest.raises(
            ValueError, match="start_time and end_time required when all_day is False"
        ):
            await availability_repository.block_time_slot(
                host_profile_id=sample_host_profile_id,
                override_date=date(2026, 3, 1),
                all_day=False,
            )


class TestGetOverridesForDateRange:
    """Tests for AvailabilityRepository.get_overrides_for_date_range() method."""

    async def test_get_overrides_for_date_range(
        self,
        availability_repository,
        mock_session,
        sample_host_profile_id,
        sample_availability_override,
    ):
        """Test getting overrides for a date range."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            sample_availability_override
        ]
        mock_session.execute.return_value = mock_result

        result = await availability_repository.get_overrides_for_date_range(
            host_profile_id=sample_host_profile_id,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 28),
        )

        assert len(result) == 1
        assert result[0] == sample_availability_override

    async def test_get_overrides_filter_by_type(
        self,
        availability_repository,
        mock_session,
        sample_host_profile_id,
        sample_blocked_override,
    ):
        """Test filtering overrides by type."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_blocked_override]
        mock_session.execute.return_value = mock_result

        result = await availability_repository.get_overrides_for_date_range(
            host_profile_id=sample_host_profile_id,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 28),
            override_type=AvailabilityOverrideType.BLOCKED,
        )

        assert len(result) == 1
        assert result[0].override_type == AvailabilityOverrideType.BLOCKED


class TestDeleteOverride:
    """Tests for AvailabilityRepository.delete_override() method."""

    async def test_delete_override_success(
        self, availability_repository, mock_session, sample_availability_override
    ):
        """Test deleting an override."""
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        result = await availability_repository.delete_override(
            sample_availability_override.id
        )

        assert result is True
        mock_session.flush.assert_called_once()

    async def test_delete_override_not_found(
        self, availability_repository, mock_session
    ):
        """Test deleting non-existent override."""
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result

        result = await availability_repository.delete_override(uuid.uuid4())

        assert result is False


class TestGetAvailabilityForDate:
    """Tests for AvailabilityRepository.get_availability_for_date() method."""

    async def test_get_availability_from_recurring(
        self,
        availability_repository,
        mock_session,
        sample_host_profile_id,
        sample_recurring_availability,
    ):
        """Test getting availability from recurring schedule."""
        # Mock recurring availability query
        mock_recurring_result = MagicMock()
        mock_recurring_result.scalars.return_value.all.return_value = [
            sample_recurring_availability
        ]

        # Mock overrides query (empty)
        mock_overrides_result = MagicMock()
        mock_overrides_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [
            mock_recurring_result,
            mock_overrides_result,
        ]

        # Monday date
        target_date = date(2026, 2, 2)  # A Monday
        result = await availability_repository.get_availability_for_date(
            sample_host_profile_id, target_date
        )

        assert len(result) == 1
        assert result[0] == (time(9, 0), time(17, 0))

    async def test_get_availability_blocked_all_day(
        self,
        availability_repository,
        mock_session,
        sample_host_profile_id,
        sample_recurring_availability,
        sample_blocked_override,
    ):
        """Test that all-day block returns no availability."""
        # Mock recurring availability
        mock_recurring_result = MagicMock()
        mock_recurring_result.scalars.return_value.all.return_value = [
            sample_recurring_availability
        ]

        # All-day block
        all_day_block = AvailabilityOverride(
            id=uuid.uuid4(),
            host_profile_id=str(sample_host_profile_id),
            override_date=date(2026, 2, 2),  # Monday
            override_type=AvailabilityOverrideType.BLOCKED,
            all_day=True,
            reason="Vacation",
        )

        mock_overrides_result = MagicMock()
        mock_overrides_result.scalars.return_value.all.return_value = [all_day_block]

        mock_session.execute.side_effect = [
            mock_recurring_result,
            mock_overrides_result,
        ]

        result = await availability_repository.get_availability_for_date(
            sample_host_profile_id, date(2026, 2, 2)
        )

        assert len(result) == 0  # All-day block removes all availability

    async def test_get_availability_with_partial_block(
        self, availability_repository, mock_session, sample_host_profile_id
    ):
        """Test availability with partial time block."""
        # Recurring: 9am-5pm
        recurring = RecurringAvailability(
            id=uuid.uuid4(),
            host_profile_id=str(sample_host_profile_id),
            day_of_week=DayOfWeek.MONDAY.value,
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_active=True,
        )

        mock_recurring_result = MagicMock()
        mock_recurring_result.scalars.return_value.all.return_value = [recurring]

        # Block 12pm-1pm for lunch
        block = AvailabilityOverride(
            id=uuid.uuid4(),
            host_profile_id=str(sample_host_profile_id),
            override_date=date(2026, 2, 2),
            override_type=AvailabilityOverrideType.BLOCKED,
            start_time=time(12, 0),
            end_time=time(13, 0),
            all_day=False,
        )

        mock_overrides_result = MagicMock()
        mock_overrides_result.scalars.return_value.all.return_value = [block]

        mock_session.execute.side_effect = [
            mock_recurring_result,
            mock_overrides_result,
        ]

        result = await availability_repository.get_availability_for_date(
            sample_host_profile_id, date(2026, 2, 2)
        )

        # Should have 9am-12pm and 1pm-5pm
        assert len(result) == 2
        assert result[0] == (time(9, 0), time(12, 0))
        assert result[1] == (time(13, 0), time(17, 0))

    async def test_get_availability_with_one_time_addition(
        self, availability_repository, mock_session, sample_host_profile_id
    ):
        """Test adding one-time availability to a day without recurring."""
        # No recurring availability
        mock_recurring_result = MagicMock()
        mock_recurring_result.scalars.return_value.all.return_value = []

        # One-time availability
        addition = AvailabilityOverride(
            id=uuid.uuid4(),
            host_profile_id=str(sample_host_profile_id),
            override_date=date(2026, 2, 7),  # Saturday
            override_type=AvailabilityOverrideType.AVAILABLE,
            start_time=time(10, 0),
            end_time=time(14, 0),
            all_day=False,
        )

        mock_overrides_result = MagicMock()
        mock_overrides_result.scalars.return_value.all.return_value = [addition]

        mock_session.execute.side_effect = [
            mock_recurring_result,
            mock_overrides_result,
        ]

        result = await availability_repository.get_availability_for_date(
            sample_host_profile_id, date(2026, 2, 7)
        )

        assert len(result) == 1
        assert result[0] == (time(10, 0), time(14, 0))

    async def test_get_availability_empty(
        self, availability_repository, mock_session, sample_host_profile_id
    ):
        """Test no availability when no recurring or overrides."""
        mock_recurring_result = MagicMock()
        mock_recurring_result.scalars.return_value.all.return_value = []

        mock_overrides_result = MagicMock()
        mock_overrides_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [
            mock_recurring_result,
            mock_overrides_result,
        ]

        result = await availability_repository.get_availability_for_date(
            sample_host_profile_id, date(2026, 2, 7)
        )

        assert len(result) == 0


class TestIsAvailableForSlot:
    """Tests for AvailabilityRepository.is_available_for_slot() method."""

    async def test_is_available_for_slot_success(
        self, availability_repository, mock_session, sample_host_profile_id
    ):
        """Test slot is available when within schedule and no conflicts."""
        # Recurring: 9am-5pm Monday
        recurring = RecurringAvailability(
            id=uuid.uuid4(),
            host_profile_id=str(sample_host_profile_id),
            day_of_week=DayOfWeek.MONDAY.value,
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_active=True,
        )

        mock_recurring_result = MagicMock()
        mock_recurring_result.scalars.return_value.all.return_value = [recurring]

        mock_overrides_result = MagicMock()
        mock_overrides_result.scalars.return_value.all.return_value = []

        # No conflicting bookings
        mock_booking_result = MagicMock()
        mock_booking_result.scalar_one_or_none.return_value = None

        mock_session.execute.side_effect = [
            mock_recurring_result,
            mock_overrides_result,
            mock_booking_result,
        ]

        result = await availability_repository.is_available_for_slot(
            host_profile_id=sample_host_profile_id,
            start_datetime=datetime(2026, 2, 2, 10, 0, tzinfo=UTC),  # Monday 10am
            end_datetime=datetime(2026, 2, 2, 12, 0, tzinfo=UTC),  # Monday 12pm
        )

        assert result is True

    async def test_is_available_for_slot_outside_schedule(
        self, availability_repository, mock_session, sample_host_profile_id
    ):
        """Test slot is not available when outside schedule."""
        # Recurring: 9am-5pm Monday
        recurring = RecurringAvailability(
            id=uuid.uuid4(),
            host_profile_id=str(sample_host_profile_id),
            day_of_week=DayOfWeek.MONDAY.value,
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_active=True,
        )

        mock_recurring_result = MagicMock()
        mock_recurring_result.scalars.return_value.all.return_value = [recurring]

        mock_overrides_result = MagicMock()
        mock_overrides_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [
            mock_recurring_result,
            mock_overrides_result,
        ]

        # Try to book 6pm-8pm (outside 9am-5pm)
        result = await availability_repository.is_available_for_slot(
            host_profile_id=sample_host_profile_id,
            start_datetime=datetime(2026, 2, 2, 18, 0, tzinfo=UTC),
            end_datetime=datetime(2026, 2, 2, 20, 0, tzinfo=UTC),
        )

        assert result is False

    async def test_is_available_for_slot_conflicting_booking(
        self,
        availability_repository,
        mock_session,
        sample_host_profile_id,
        sample_booking,
    ):
        """Test slot is not available when booking exists."""
        # Recurring: 9am-5pm Monday
        recurring = RecurringAvailability(
            id=uuid.uuid4(),
            host_profile_id=str(sample_host_profile_id),
            day_of_week=DayOfWeek.MONDAY.value,
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_active=True,
        )

        mock_recurring_result = MagicMock()
        mock_recurring_result.scalars.return_value.all.return_value = [recurring]

        mock_overrides_result = MagicMock()
        mock_overrides_result.scalars.return_value.all.return_value = []

        # Conflicting booking exists (10am-12pm)
        mock_booking_result = MagicMock()
        mock_booking_result.scalar_one_or_none.return_value = sample_booking

        mock_session.execute.side_effect = [
            mock_recurring_result,
            mock_overrides_result,
            mock_booking_result,
        ]

        # Update booking to match Monday
        sample_booking.scheduled_start = datetime(2026, 2, 2, 10, 0, tzinfo=UTC)
        sample_booking.scheduled_end = datetime(2026, 2, 2, 12, 0, tzinfo=UTC)

        # Try to book 11am-1pm (overlaps with existing 10am-12pm)
        result = await availability_repository.is_available_for_slot(
            host_profile_id=sample_host_profile_id,
            start_datetime=datetime(2026, 2, 2, 11, 0, tzinfo=UTC),
            end_datetime=datetime(2026, 2, 2, 13, 0, tzinfo=UTC),
        )

        assert result is False

    async def test_is_available_for_slot_invalid_time_range(
        self, availability_repository, sample_host_profile_id
    ):
        """Test error when end is before start."""
        with pytest.raises(
            ValueError, match="end_datetime must be after start_datetime"
        ):
            await availability_repository.is_available_for_slot(
                host_profile_id=sample_host_profile_id,
                start_datetime=datetime(2026, 2, 2, 14, 0, tzinfo=UTC),
                end_datetime=datetime(2026, 2, 2, 10, 0, tzinfo=UTC),
            )

    async def test_is_available_for_slot_spans_midnight(
        self, availability_repository, sample_host_profile_id
    ):
        """Test that bookings spanning midnight are not allowed."""
        result = await availability_repository.is_available_for_slot(
            host_profile_id=sample_host_profile_id,
            start_datetime=datetime(2026, 2, 2, 22, 0, tzinfo=UTC),
            end_datetime=datetime(2026, 2, 3, 2, 0, tzinfo=UTC),  # Next day
        )

        assert result is False


class TestGetBookingsForDateRange:
    """Tests for AvailabilityRepository.get_bookings_for_date_range() method."""

    async def test_get_bookings_for_date_range(
        self,
        availability_repository,
        mock_session,
        sample_host_profile_id,
        sample_booking,
    ):
        """Test getting bookings in a date range."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_booking]
        mock_session.execute.return_value = mock_result

        result = await availability_repository.get_bookings_for_date_range(
            host_profile_id=sample_host_profile_id,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 28),
        )

        assert len(result) == 1
        assert result[0] == sample_booking

    async def test_get_bookings_include_cancelled(
        self,
        availability_repository,
        mock_session,
        sample_host_profile_id,
        sample_booking,
    ):
        """Test including cancelled bookings."""
        sample_booking.status = BookingStatus.CANCELLED
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_booking]
        mock_session.execute.return_value = mock_result

        result = await availability_repository.get_bookings_for_date_range(
            host_profile_id=sample_host_profile_id,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 28),
            include_cancelled=True,
        )

        assert len(result) == 1


class TestClearRecurringAvailability:
    """Tests for AvailabilityRepository.clear_recurring_availability() method."""

    async def test_clear_recurring_availability(
        self, availability_repository, mock_session, sample_host_profile_id
    ):
        """Test clearing all recurring availability."""
        mock_result = MagicMock()
        mock_result.rowcount = 5
        mock_session.execute.return_value = mock_result

        result = await availability_repository.clear_recurring_availability(
            sample_host_profile_id
        )

        assert result == 5
        mock_session.flush.assert_called_once()

    async def test_clear_recurring_availability_none(
        self, availability_repository, mock_session, sample_host_profile_id
    ):
        """Test clearing when none exists."""
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result

        result = await availability_repository.clear_recurring_availability(
            sample_host_profile_id
        )

        assert result == 0


class TestSetWeeklySchedule:
    """Tests for AvailabilityRepository.set_weekly_schedule() method."""

    async def test_set_weekly_schedule(
        self, availability_repository, mock_session, sample_host_profile_id
    ):
        """Test setting a complete weekly schedule."""
        # Mock clear
        mock_clear_result = MagicMock()
        mock_clear_result.rowcount = 0
        mock_session.execute.return_value = mock_clear_result

        schedule = {
            DayOfWeek.MONDAY: [(time(9, 0), time(17, 0))],
            DayOfWeek.TUESDAY: [(time(9, 0), time(17, 0))],
            DayOfWeek.WEDNESDAY: [
                (time(9, 0), time(12, 0)),
                (time(14, 0), time(17, 0)),
            ],
        }

        # Reset mock for set_recurring_availability calls
        mock_session.reset_mock()
        mock_session.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=None),
            rowcount=0,
        )

        result = await availability_repository.set_weekly_schedule(
            host_profile_id=sample_host_profile_id,
            schedule=schedule,
            clear_existing=True,
        )

        # Should create 4 records (Mon, Tue, Wed morning, Wed afternoon)
        assert len(result) == 4


class TestSubtractTimeRange:
    """Tests for _subtract_time_range helper method."""

    def test_subtract_no_overlap_before(self, availability_repository):
        """Test subtraction when block is before slot."""
        slots = [(time(14, 0), time(18, 0))]
        result = availability_repository._subtract_time_range(
            slots, time(9, 0), time(12, 0)
        )
        assert result == [(time(14, 0), time(18, 0))]

    def test_subtract_no_overlap_after(self, availability_repository):
        """Test subtraction when block is after slot."""
        slots = [(time(9, 0), time(12, 0))]
        result = availability_repository._subtract_time_range(
            slots, time(14, 0), time(18, 0)
        )
        assert result == [(time(9, 0), time(12, 0))]

    def test_subtract_complete_overlap(self, availability_repository):
        """Test subtraction when block completely covers slot."""
        slots = [(time(10, 0), time(14, 0))]
        result = availability_repository._subtract_time_range(
            slots, time(9, 0), time(15, 0)
        )
        assert result == []

    def test_subtract_cuts_beginning(self, availability_repository):
        """Test subtraction when block cuts the beginning."""
        slots = [(time(9, 0), time(17, 0))]
        result = availability_repository._subtract_time_range(
            slots, time(8, 0), time(11, 0)
        )
        assert result == [(time(11, 0), time(17, 0))]

    def test_subtract_cuts_end(self, availability_repository):
        """Test subtraction when block cuts the end."""
        slots = [(time(9, 0), time(17, 0))]
        result = availability_repository._subtract_time_range(
            slots, time(15, 0), time(18, 0)
        )
        assert result == [(time(9, 0), time(15, 0))]

    def test_subtract_splits_slot(self, availability_repository):
        """Test subtraction when block is in the middle."""
        slots = [(time(9, 0), time(17, 0))]
        result = availability_repository._subtract_time_range(
            slots, time(12, 0), time(13, 0)
        )
        assert result == [(time(9, 0), time(12, 0)), (time(13, 0), time(17, 0))]


class TestMergeTimeRanges:
    """Tests for _merge_time_ranges helper method."""

    def test_merge_empty(self, availability_repository):
        """Test merging empty list."""
        result = availability_repository._merge_time_ranges([])
        assert result == []

    def test_merge_single(self, availability_repository):
        """Test merging single slot."""
        slots = [(time(9, 0), time(17, 0))]
        result = availability_repository._merge_time_ranges(slots)
        assert result == [(time(9, 0), time(17, 0))]

    def test_merge_non_overlapping(self, availability_repository):
        """Test merging non-overlapping slots."""
        slots = [(time(9, 0), time(12, 0)), (time(14, 0), time(17, 0))]
        result = availability_repository._merge_time_ranges(slots)
        assert result == [(time(9, 0), time(12, 0)), (time(14, 0), time(17, 0))]

    def test_merge_overlapping(self, availability_repository):
        """Test merging overlapping slots."""
        slots = [(time(9, 0), time(14, 0)), (time(12, 0), time(17, 0))]
        result = availability_repository._merge_time_ranges(slots)
        assert result == [(time(9, 0), time(17, 0))]

    def test_merge_adjacent(self, availability_repository):
        """Test merging adjacent slots."""
        slots = [(time(9, 0), time(12, 0)), (time(12, 0), time(17, 0))]
        result = availability_repository._merge_time_ranges(slots)
        assert result == [(time(9, 0), time(17, 0))]


class TestAsyncPatterns:
    """Tests to verify all methods use async patterns."""

    async def test_set_recurring_availability_is_async(self, availability_repository):
        """Verify set_recurring_availability is async."""
        assert inspect.iscoroutinefunction(
            availability_repository.set_recurring_availability
        )

    async def test_get_recurring_availability_is_async(self, availability_repository):
        """Verify get_recurring_availability is async."""
        assert inspect.iscoroutinefunction(
            availability_repository.get_recurring_availability
        )

    async def test_add_one_time_is_async(self, availability_repository):
        """Verify add_one_time is async."""
        assert inspect.iscoroutinefunction(availability_repository.add_one_time)

    async def test_block_time_slot_is_async(self, availability_repository):
        """Verify block_time_slot is async."""
        assert inspect.iscoroutinefunction(availability_repository.block_time_slot)

    async def test_get_availability_for_date_is_async(self, availability_repository):
        """Verify get_availability_for_date is async."""
        assert inspect.iscoroutinefunction(
            availability_repository.get_availability_for_date
        )

    async def test_is_available_for_slot_is_async(self, availability_repository):
        """Verify is_available_for_slot is async."""
        assert inspect.iscoroutinefunction(
            availability_repository.is_available_for_slot
        )

    async def test_get_bookings_for_date_range_is_async(self, availability_repository):
        """Verify get_bookings_for_date_range is async."""
        assert inspect.iscoroutinefunction(
            availability_repository.get_bookings_for_date_range
        )

    async def test_clear_recurring_availability_is_async(self, availability_repository):
        """Verify clear_recurring_availability is async."""
        assert inspect.iscoroutinefunction(
            availability_repository.clear_recurring_availability
        )

    async def test_set_weekly_schedule_is_async(self, availability_repository):
        """Verify set_weekly_schedule is async."""
        assert inspect.iscoroutinefunction(availability_repository.set_weekly_schedule)
