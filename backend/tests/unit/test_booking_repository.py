"""Unit tests for BookingRepository."""

import inspect
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking, BookingStatus
from app.repositories.booking import BookingRepository


@pytest.fixture
def mock_session():
    """Create a mock async session."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def booking_repository(mock_session):
    """Create a BookingRepository with a mock session."""
    return BookingRepository(mock_session)


@pytest.fixture
def sample_client_id():
    """Create a sample client ID."""
    return uuid.uuid4()


@pytest.fixture
def sample_host_id():
    """Create a sample host ID."""
    return uuid.uuid4()


@pytest.fixture
def sample_host_profile_id():
    """Create a sample host profile ID."""
    return uuid.uuid4()


@pytest.fixture
def sample_booking(sample_client_id, sample_host_id, sample_host_profile_id):
    """Create a sample booking."""
    return Booking(
        id=str(uuid.uuid4()),
        client_id=str(sample_client_id),
        host_id=str(sample_host_id),
        host_profile_id=str(sample_host_profile_id),
        status=BookingStatus.PENDING,
        scheduled_start=datetime(2026, 2, 10, 10, 0, tzinfo=UTC),
        scheduled_end=datetime(2026, 2, 10, 12, 0, tzinfo=UTC),
        duration_minutes=120,
        hourly_rate_cents=5000,
        amount_cents=10000,
        platform_fee_cents=1500,
        host_payout_cents=8500,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_confirmed_booking(sample_client_id, sample_host_id, sample_host_profile_id):
    """Create a sample confirmed booking."""
    return Booking(
        id=str(uuid.uuid4()),
        client_id=str(sample_client_id),
        host_id=str(sample_host_id),
        host_profile_id=str(sample_host_profile_id),
        status=BookingStatus.CONFIRMED,
        scheduled_start=datetime(2026, 2, 15, 14, 0, tzinfo=UTC),
        scheduled_end=datetime(2026, 2, 15, 16, 0, tzinfo=UTC),
        duration_minutes=120,
        hourly_rate_cents=5000,
        amount_cents=10000,
        platform_fee_cents=1500,
        host_payout_cents=8500,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


class TestBookingRepositoryCreate:
    """Tests for BookingRepository.create() method."""

    async def test_create_booking_success(
        self,
        booking_repository,
        mock_session,
        sample_client_id,
        sample_host_id,
        sample_host_profile_id,
    ):
        """Test creating a new booking."""
        scheduled_start = datetime(2026, 2, 10, 10, 0, tzinfo=UTC)
        scheduled_end = datetime(2026, 2, 10, 12, 0, tzinfo=UTC)

        result = await booking_repository.create(
            client_id=sample_client_id,
            host_id=sample_host_id,
            host_profile_id=sample_host_profile_id,
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            duration_minutes=120,
            hourly_rate_cents=5000,
            amount_cents=10000,
        )

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        assert result.client_id == str(sample_client_id)
        assert result.host_id == str(sample_host_id)
        assert result.host_profile_id == str(sample_host_profile_id)
        assert result.status == BookingStatus.PENDING
        assert result.scheduled_start == scheduled_start
        assert result.scheduled_end == scheduled_end
        assert result.duration_minutes == 120
        assert result.hourly_rate_cents == 5000
        assert result.amount_cents == 10000

    async def test_create_booking_with_all_fields(
        self,
        booking_repository,
        mock_session,
        sample_client_id,
        sample_host_id,
        sample_host_profile_id,
    ):
        """Test creating a booking with all optional fields."""
        dance_style_id = uuid.uuid4()
        scheduled_start = datetime(2026, 2, 10, 10, 0, tzinfo=UTC)
        scheduled_end = datetime(2026, 2, 10, 12, 0, tzinfo=UTC)

        result = await booking_repository.create(
            client_id=sample_client_id,
            host_id=sample_host_id,
            host_profile_id=sample_host_profile_id,
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            duration_minutes=120,
            hourly_rate_cents=5000,
            amount_cents=10000,
            platform_fee_cents=1500,
            host_payout_cents=8500,
            dance_style_id=dance_style_id,
            location="POINT(-74.0 40.7)",
            location_name="Central Park Dance Studio",
            location_notes="Enter through the side door",
            client_notes="First time dancer, looking to learn salsa",
            stripe_payment_intent_id="pi_test123",
        )

        assert result.dance_style_id == str(dance_style_id)
        assert result.platform_fee_cents == 1500
        assert result.host_payout_cents == 8500
        assert result.location == "POINT(-74.0 40.7)"
        assert result.location_name == "Central Park Dance Studio"
        assert result.location_notes == "Enter through the side door"
        assert result.client_notes == "First time dancer, looking to learn salsa"
        assert result.stripe_payment_intent_id == "pi_test123"

    async def test_create_booking_default_status_is_pending(
        self,
        booking_repository,
        mock_session,
        sample_client_id,
        sample_host_id,
        sample_host_profile_id,
    ):
        """Test that newly created bookings have PENDING status."""
        result = await booking_repository.create(
            client_id=sample_client_id,
            host_id=sample_host_id,
            host_profile_id=sample_host_profile_id,
            scheduled_start=datetime(2026, 2, 10, 10, 0, tzinfo=UTC),
            scheduled_end=datetime(2026, 2, 10, 12, 0, tzinfo=UTC),
            duration_minutes=120,
            hourly_rate_cents=5000,
            amount_cents=10000,
        )

        assert result.status == BookingStatus.PENDING


class TestBookingRepositoryGetById:
    """Tests for BookingRepository.get_by_id() method."""

    async def test_get_by_id_found(
        self, booking_repository, mock_session, sample_booking
    ):
        """Test getting a booking by ID when it exists."""
        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = sample_booking
        mock_session.execute.return_value = mock_result

        result = await booking_repository.get_by_id(uuid.UUID(sample_booking.id))

        assert result == sample_booking

    async def test_get_by_id_not_found(self, booking_repository, mock_session):
        """Test getting a booking by ID when it doesn't exist."""
        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await booking_repository.get_by_id(uuid.uuid4())

        assert result is None

    async def test_get_by_id_without_relationships(
        self, booking_repository, mock_session, sample_booking
    ):
        """Test getting a booking without loading relationships."""
        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = sample_booking
        mock_session.execute.return_value = mock_result

        result = await booking_repository.get_by_id(
            uuid.UUID(sample_booking.id), load_relationships=False
        )

        assert result == sample_booking


class TestBookingRepositoryGetForClient:
    """Tests for BookingRepository.get_for_client() method."""

    async def test_get_for_client_returns_bookings(
        self, booking_repository, mock_session, sample_booking, sample_client_id
    ):
        """Test getting bookings for a client."""
        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.all.return_value = [
            sample_booking
        ]
        mock_session.execute.return_value = mock_result

        result = await booking_repository.get_for_client(sample_client_id)

        assert len(result) == 1
        assert result[0] == sample_booking

    async def test_get_for_client_empty(
        self, booking_repository, mock_session, sample_client_id
    ):
        """Test getting bookings when client has none."""
        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await booking_repository.get_for_client(sample_client_id)

        assert len(result) == 0

    async def test_get_for_client_with_status_filter(
        self, booking_repository, mock_session, sample_booking, sample_client_id
    ):
        """Test filtering by single status."""
        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.all.return_value = [
            sample_booking
        ]
        mock_session.execute.return_value = mock_result

        result = await booking_repository.get_for_client(
            sample_client_id, status=BookingStatus.PENDING
        )

        assert len(result) == 1

    async def test_get_for_client_with_status_list(
        self, booking_repository, mock_session, sample_booking, sample_client_id
    ):
        """Test filtering by list of statuses."""
        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.all.return_value = [
            sample_booking
        ]
        mock_session.execute.return_value = mock_result

        result = await booking_repository.get_for_client(
            sample_client_id,
            status=[BookingStatus.PENDING, BookingStatus.CONFIRMED],
        )

        assert len(result) == 1

    async def test_get_for_client_with_pagination(
        self, booking_repository, mock_session, sample_client_id
    ):
        """Test pagination parameters are used."""
        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        await booking_repository.get_for_client(sample_client_id, limit=10, offset=20)

        mock_session.execute.assert_called_once()


class TestBookingRepositoryGetForHost:
    """Tests for BookingRepository.get_for_host() method."""

    async def test_get_for_host_returns_bookings(
        self, booking_repository, mock_session, sample_booking, sample_host_id
    ):
        """Test getting bookings for a host."""
        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.all.return_value = [
            sample_booking
        ]
        mock_session.execute.return_value = mock_result

        result = await booking_repository.get_for_host(sample_host_id)

        assert len(result) == 1
        assert result[0] == sample_booking

    async def test_get_for_host_empty(
        self, booking_repository, mock_session, sample_host_id
    ):
        """Test getting bookings when host has none."""
        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await booking_repository.get_for_host(sample_host_id)

        assert len(result) == 0

    async def test_get_for_host_with_status_filter(
        self, booking_repository, mock_session, sample_booking, sample_host_id
    ):
        """Test filtering by status."""
        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.all.return_value = [
            sample_booking
        ]
        mock_session.execute.return_value = mock_result

        result = await booking_repository.get_for_host(
            sample_host_id, status=BookingStatus.CONFIRMED
        )

        assert len(result) == 1


class TestBookingRepositoryGetForUser:
    """Tests for BookingRepository.get_for_user() method."""

    async def test_get_for_user_returns_both_client_and_host_bookings(
        self, booking_repository, mock_session, sample_booking, sample_client_id
    ):
        """Test getting bookings where user is client or host."""
        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.all.return_value = [
            sample_booking
        ]
        mock_session.execute.return_value = mock_result

        result = await booking_repository.get_for_user(sample_client_id)

        assert len(result) == 1

    async def test_get_for_user_with_status_filter(
        self, booking_repository, mock_session, sample_client_id
    ):
        """Test filtering by status."""
        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        await booking_repository.get_for_user(
            sample_client_id, status=BookingStatus.COMPLETED
        )

        mock_session.execute.assert_called_once()


class TestBookingRepositoryUpdateStatus:
    """Tests for BookingRepository.update_status() method."""

    async def test_update_status_to_confirmed(
        self, booking_repository, mock_session, sample_booking
    ):
        """Test updating booking status to confirmed."""
        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = sample_booking
        mock_session.execute.return_value = mock_result

        result = await booking_repository.update_status(
            uuid.UUID(sample_booking.id), BookingStatus.CONFIRMED
        )

        assert result.status == BookingStatus.CONFIRMED
        mock_session.flush.assert_called_once()

    async def test_update_status_to_cancelled_with_reason(
        self, booking_repository, mock_session, sample_booking
    ):
        """Test updating to cancelled with cancellation info."""
        canceller_id = uuid.uuid4()
        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = sample_booking
        mock_session.execute.return_value = mock_result

        result = await booking_repository.update_status(
            uuid.UUID(sample_booking.id),
            BookingStatus.CANCELLED,
            cancelled_by_id=canceller_id,
            cancellation_reason="Schedule conflict",
        )

        assert result.status == BookingStatus.CANCELLED
        assert result.cancelled_by_id == str(canceller_id)
        assert result.cancellation_reason == "Schedule conflict"
        assert result.cancelled_at is not None

    async def test_update_status_to_in_progress_with_actual_start(
        self, booking_repository, mock_session, sample_booking
    ):
        """Test updating to in_progress with actual start time."""
        actual_start = datetime.now(UTC)
        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = sample_booking
        mock_session.execute.return_value = mock_result

        result = await booking_repository.update_status(
            uuid.UUID(sample_booking.id),
            BookingStatus.IN_PROGRESS,
            actual_start=actual_start,
        )

        assert result.status == BookingStatus.IN_PROGRESS
        assert result.actual_start == actual_start

    async def test_update_status_to_completed_with_transfer(
        self, booking_repository, mock_session, sample_booking
    ):
        """Test updating to completed with stripe transfer."""
        actual_end = datetime.now(UTC)
        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = sample_booking
        mock_session.execute.return_value = mock_result

        result = await booking_repository.update_status(
            uuid.UUID(sample_booking.id),
            BookingStatus.COMPLETED,
            actual_end=actual_end,
            stripe_transfer_id="tr_test123",
        )

        assert result.status == BookingStatus.COMPLETED
        assert result.actual_end == actual_end
        assert result.stripe_transfer_id == "tr_test123"

    async def test_update_status_booking_not_found(
        self, booking_repository, mock_session
    ):
        """Test updating status when booking doesn't exist."""
        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await booking_repository.update_status(
            uuid.uuid4(), BookingStatus.CONFIRMED
        )

        assert result is None


class TestBookingRepositoryGetOverlapping:
    """Tests for BookingRepository.get_overlapping() method."""

    async def test_get_overlapping_finds_conflicts(
        self, booking_repository, mock_session, sample_booking, sample_host_profile_id
    ):
        """Test finding overlapping bookings."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_booking]
        mock_session.execute.return_value = mock_result

        result = await booking_repository.get_overlapping(
            sample_host_profile_id,
            datetime(2026, 2, 10, 9, 0, tzinfo=UTC),
            datetime(2026, 2, 10, 11, 0, tzinfo=UTC),
        )

        assert len(result) == 1

    async def test_get_overlapping_no_conflicts(
        self, booking_repository, mock_session, sample_host_profile_id
    ):
        """Test when no overlapping bookings exist."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await booking_repository.get_overlapping(
            sample_host_profile_id,
            datetime(2026, 2, 10, 18, 0, tzinfo=UTC),
            datetime(2026, 2, 10, 20, 0, tzinfo=UTC),
        )

        assert len(result) == 0

    async def test_get_overlapping_excludes_booking(
        self, booking_repository, mock_session, sample_booking, sample_host_profile_id
    ):
        """Test excluding a specific booking from overlap check."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        await booking_repository.get_overlapping(
            sample_host_profile_id,
            datetime(2026, 2, 10, 10, 0, tzinfo=UTC),
            datetime(2026, 2, 10, 12, 0, tzinfo=UTC),
            exclude_booking_id=uuid.UUID(sample_booking.id),
        )

        mock_session.execute.assert_called_once()

    async def test_get_overlapping_includes_all_statuses(
        self, booking_repository, mock_session, sample_host_profile_id
    ):
        """Test including all statuses when active_only is False."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        await booking_repository.get_overlapping(
            sample_host_profile_id,
            datetime(2026, 2, 10, 10, 0, tzinfo=UTC),
            datetime(2026, 2, 10, 12, 0, tzinfo=UTC),
            active_only=False,
        )

        mock_session.execute.assert_called_once()


class TestBookingRepositoryGetUpcoming:
    """Tests for BookingRepository.get_upcoming() method."""

    async def test_get_upcoming_returns_future_bookings(
        self,
        booking_repository,
        mock_session,
        sample_confirmed_booking,
        sample_client_id,
    ):
        """Test getting upcoming confirmed bookings."""
        # Set booking to future
        sample_confirmed_booking.scheduled_start = datetime.now(UTC) + timedelta(days=7)
        sample_confirmed_booking.scheduled_end = datetime.now(UTC) + timedelta(
            days=7, hours=2
        )

        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.all.return_value = [
            sample_confirmed_booking
        ]
        mock_session.execute.return_value = mock_result

        result = await booking_repository.get_upcoming(sample_client_id)

        assert len(result) == 1
        assert result[0].status == BookingStatus.CONFIRMED

    async def test_get_upcoming_as_host_only(
        self, booking_repository, mock_session, sample_host_id
    ):
        """Test getting upcoming bookings as host only."""
        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        await booking_repository.get_upcoming(sample_host_id, as_host=True)

        mock_session.execute.assert_called_once()

    async def test_get_upcoming_as_client_only(
        self, booking_repository, mock_session, sample_client_id
    ):
        """Test getting upcoming bookings as client only."""
        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        await booking_repository.get_upcoming(sample_client_id, as_client=True)

        mock_session.execute.assert_called_once()

    async def test_get_upcoming_with_limit(
        self, booking_repository, mock_session, sample_client_id
    ):
        """Test limiting number of upcoming bookings."""
        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        await booking_repository.get_upcoming(sample_client_id, limit=5)

        mock_session.execute.assert_called_once()


class TestBookingRepositoryCountForClient:
    """Tests for BookingRepository.count_for_client() method."""

    async def test_count_for_client_returns_count(
        self, booking_repository, mock_session, sample_client_id
    ):
        """Test counting bookings for a client."""
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 5
        mock_session.execute.return_value = mock_result

        result = await booking_repository.count_for_client(sample_client_id)

        assert result == 5

    async def test_count_for_client_with_status_filter(
        self, booking_repository, mock_session, sample_client_id
    ):
        """Test counting with status filter."""
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 3
        mock_session.execute.return_value = mock_result

        result = await booking_repository.count_for_client(
            sample_client_id, status=BookingStatus.COMPLETED
        )

        assert result == 3

    async def test_count_for_client_with_status_list(
        self, booking_repository, mock_session, sample_client_id
    ):
        """Test counting with list of statuses."""
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 2
        mock_session.execute.return_value = mock_result

        result = await booking_repository.count_for_client(
            sample_client_id,
            status=[BookingStatus.PENDING, BookingStatus.CONFIRMED],
        )

        assert result == 2


class TestBookingRepositoryCountForHost:
    """Tests for BookingRepository.count_for_host() method."""

    async def test_count_for_host_returns_count(
        self, booking_repository, mock_session, sample_host_id
    ):
        """Test counting bookings for a host."""
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 10
        mock_session.execute.return_value = mock_result

        result = await booking_repository.count_for_host(sample_host_id)

        assert result == 10

    async def test_count_for_host_with_status_filter(
        self, booking_repository, mock_session, sample_host_id
    ):
        """Test counting with status filter."""
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 7
        mock_session.execute.return_value = mock_result

        result = await booking_repository.count_for_host(
            sample_host_id, status=BookingStatus.COMPLETED
        )

        assert result == 7


class TestBookingRepositoryUpdateStripePaymentIntent:
    """Tests for BookingRepository.update_stripe_payment_intent() method."""

    async def test_update_stripe_payment_intent_success(
        self, booking_repository, mock_session, sample_booking
    ):
        """Test updating Stripe PaymentIntent ID."""
        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = sample_booking
        mock_session.execute.return_value = mock_result

        result = await booking_repository.update_stripe_payment_intent(
            uuid.UUID(sample_booking.id), "pi_updated123"
        )

        assert result.stripe_payment_intent_id == "pi_updated123"
        mock_session.flush.assert_called_once()

    async def test_update_stripe_payment_intent_not_found(
        self, booking_repository, mock_session
    ):
        """Test updating when booking doesn't exist."""
        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await booking_repository.update_stripe_payment_intent(
            uuid.uuid4(), "pi_test123"
        )

        assert result is None


class TestBookingRepositoryAddHostNotes:
    """Tests for BookingRepository.add_host_notes() method."""

    async def test_add_host_notes_success(
        self, booking_repository, mock_session, sample_booking
    ):
        """Test adding host notes."""
        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = sample_booking
        mock_session.execute.return_value = mock_result

        result = await booking_repository.add_host_notes(
            uuid.UUID(sample_booking.id), "Great session, client improved a lot!"
        )

        assert result.host_notes == "Great session, client improved a lot!"
        mock_session.flush.assert_called_once()

    async def test_add_host_notes_not_found(self, booking_repository, mock_session):
        """Test adding notes when booking doesn't exist."""
        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await booking_repository.add_host_notes(uuid.uuid4(), "Some notes")

        assert result is None


class TestAsyncPatterns:
    """Tests to verify all methods use async patterns."""

    async def test_create_is_async(self, booking_repository):
        """Verify create is async."""
        assert inspect.iscoroutinefunction(booking_repository.create)

    async def test_get_by_id_is_async(self, booking_repository):
        """Verify get_by_id is async."""
        assert inspect.iscoroutinefunction(booking_repository.get_by_id)

    async def test_get_for_client_is_async(self, booking_repository):
        """Verify get_for_client is async."""
        assert inspect.iscoroutinefunction(booking_repository.get_for_client)

    async def test_get_for_host_is_async(self, booking_repository):
        """Verify get_for_host is async."""
        assert inspect.iscoroutinefunction(booking_repository.get_for_host)

    async def test_get_for_user_is_async(self, booking_repository):
        """Verify get_for_user is async."""
        assert inspect.iscoroutinefunction(booking_repository.get_for_user)

    async def test_update_status_is_async(self, booking_repository):
        """Verify update_status is async."""
        assert inspect.iscoroutinefunction(booking_repository.update_status)

    async def test_get_overlapping_is_async(self, booking_repository):
        """Verify get_overlapping is async."""
        assert inspect.iscoroutinefunction(booking_repository.get_overlapping)

    async def test_get_upcoming_is_async(self, booking_repository):
        """Verify get_upcoming is async."""
        assert inspect.iscoroutinefunction(booking_repository.get_upcoming)

    async def test_count_for_client_is_async(self, booking_repository):
        """Verify count_for_client is async."""
        assert inspect.iscoroutinefunction(booking_repository.count_for_client)

    async def test_count_for_host_is_async(self, booking_repository):
        """Verify count_for_host is async."""
        assert inspect.iscoroutinefunction(booking_repository.count_for_host)

    async def test_update_stripe_payment_intent_is_async(self, booking_repository):
        """Verify update_stripe_payment_intent is async."""
        assert inspect.iscoroutinefunction(
            booking_repository.update_stripe_payment_intent
        )

    async def test_add_host_notes_is_async(self, booking_repository):
        """Verify add_host_notes is async."""
        assert inspect.iscoroutinefunction(booking_repository.add_host_notes)


class TestBookingRepositoryMethods:
    """Tests to verify all required methods exist."""

    def test_create_method_exists(self, booking_repository):
        """Verify create method exists."""
        assert hasattr(booking_repository, "create")
        assert callable(booking_repository.create)

    def test_get_by_id_method_exists(self, booking_repository):
        """Verify get_by_id method exists."""
        assert hasattr(booking_repository, "get_by_id")
        assert callable(booking_repository.get_by_id)

    def test_get_for_client_method_exists(self, booking_repository):
        """Verify get_for_client method exists."""
        assert hasattr(booking_repository, "get_for_client")
        assert callable(booking_repository.get_for_client)

    def test_get_for_host_method_exists(self, booking_repository):
        """Verify get_for_host method exists."""
        assert hasattr(booking_repository, "get_for_host")
        assert callable(booking_repository.get_for_host)

    def test_update_status_method_exists(self, booking_repository):
        """Verify update_status method exists."""
        assert hasattr(booking_repository, "update_status")
        assert callable(booking_repository.update_status)

    def test_get_overlapping_method_exists(self, booking_repository):
        """Verify get_overlapping method exists."""
        assert hasattr(booking_repository, "get_overlapping")
        assert callable(booking_repository.get_overlapping)

    def test_get_upcoming_method_exists(self, booking_repository):
        """Verify get_upcoming method exists."""
        assert hasattr(booking_repository, "get_upcoming")
        assert callable(booking_repository.get_upcoming)
