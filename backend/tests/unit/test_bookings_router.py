"""Unit tests for bookings router."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.booking import BookingStatus
from app.models.dance_style import DanceStyle, DanceStyleCategory
from app.models.host_profile import HostProfile, VerificationStatus
from app.models.user import User, UserType


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return AsyncMock()


@pytest.fixture
def sample_user():
    """Create a sample client user for testing."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "client@test.com"
    user.first_name = "Test"
    user.last_name = "Client"
    user.user_type = UserType.CLIENT
    user.is_active = True
    user.email_verified = True
    return user


@pytest.fixture
def sample_host_user():
    """Create a sample host user for testing."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "host@test.com"
    user.first_name = "Test"
    user.last_name = "Host"
    user.user_type = UserType.HOST
    user.is_active = True
    user.email_verified = True
    return user


@pytest.fixture
def sample_host_profile(sample_host_user):
    """Create a sample host profile for testing."""
    profile = MagicMock(spec=HostProfile)
    profile.id = uuid4()
    profile.user_id = str(sample_host_user.id)
    profile.user = sample_host_user
    profile.bio = "Test bio"
    profile.headline = "Test headline"
    profile.hourly_rate_cents = 5000  # $50/hour
    profile.rating_average = 4.5
    profile.total_reviews = 10
    profile.total_sessions = 25
    profile.verification_status = VerificationStatus.VERIFIED
    profile.stripe_account_id = "acct_test123"
    profile.stripe_onboarding_complete = True
    return profile


@pytest.fixture
def sample_dance_style():
    """Create a sample dance style for testing."""
    style = MagicMock(spec=DanceStyle)
    style.id = uuid4()
    style.name = "Salsa"
    style.slug = "salsa"
    style.category = DanceStyleCategory.LATIN
    style.description = "Latin dance style"
    return style


@pytest.fixture
def sample_booking(
    sample_user, sample_host_user, sample_host_profile, sample_dance_style
):
    """Create a sample booking for testing."""
    from app.models.booking import Booking

    booking = MagicMock(spec=Booking)
    booking.id = uuid4()
    booking.client_id = str(sample_user.id)
    booking.host_id = str(sample_host_user.id)
    booking.host_profile_id = str(sample_host_profile.id)
    booking.dance_style_id = str(sample_dance_style.id)
    booking.status = BookingStatus.PENDING
    booking.scheduled_start = datetime.now(UTC) + timedelta(days=1)
    booking.scheduled_end = booking.scheduled_start + timedelta(hours=1)
    booking.actual_start = None
    booking.actual_end = None
    booking.duration_minutes = 60
    booking.hourly_rate_cents = 5000
    booking.amount_cents = 5000
    booking.platform_fee_cents = 750
    booking.host_payout_cents = 4250
    booking.location = None
    booking.location_name = "Dance Studio"
    booking.location_notes = "Room 101"
    booking.client_notes = "Looking forward to it!"
    booking.host_notes = None
    booking.cancellation_reason = None
    booking.cancelled_by_id = None
    booking.cancelled_at = None
    booking.stripe_payment_intent_id = "pi_test123"
    booking.created_at = datetime.now(UTC)
    booking.updated_at = datetime.now(UTC)
    booking.client = sample_user
    booking.host = sample_host_user
    booking.host_profile = sample_host_profile
    booking.dance_style = sample_dance_style
    return booking


def get_auth_header(user_id: UUID):
    """Generate a mock authentication header."""
    return {"Authorization": f"Bearer test_token_{user_id}"}


class TestCreateBookingEndpoint:
    """Tests for POST /api/v1/bookings endpoint."""

    @pytest.mark.asyncio
    async def test_create_booking_endpoint_exists(
        self,
        mock_db,
        sample_user,
        sample_host_profile,
        sample_booking,
    ):
        """Test that the create booking endpoint exists and returns 201."""
        scheduled_start = datetime.now(UTC) + timedelta(days=1)
        # Make it a Monday for consistent testing
        while scheduled_start.weekday() != 0:  # 0 = Monday
            scheduled_start += timedelta(days=1)
        # Set to 10am
        scheduled_start = scheduled_start.replace(
            hour=10, minute=0, second=0, microsecond=0
        )

        request_data = {
            "host_id": str(sample_host_profile.id),
            "scheduled_start": scheduled_start.isoformat(),
            "duration_minutes": 60,
        }

        with (
            patch("app.routers.bookings.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.routers.bookings.HostProfileRepository") as mock_host_repo_cls,
            patch("app.routers.bookings.AvailabilityRepository") as mock_avail_repo_cls,
            patch("app.routers.bookings.BookingRepository") as mock_booking_repo_cls,
            patch("app.routers.bookings.stripe_service") as mock_stripe,
            patch("app.routers.bookings.get_settings") as mock_settings,
        ):
            # Mock token validation
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            # Mock user repository for auth middleware
            with patch("app.core.deps.UserRepository") as mock_user_repo_cls:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_id.return_value = sample_user
                mock_user_repo_cls.return_value = mock_user_repo

                # Mock settings
                mock_settings_obj = MagicMock()
                mock_settings_obj.stripe_secret_key = "sk_test_123"
                mock_settings.return_value = mock_settings_obj

                # Mock host profile repository
                mock_host_repo = AsyncMock()
                mock_host_repo.get_by_id.return_value = sample_host_profile
                mock_host_repo.get_dance_style_by_id.return_value = None
                mock_host_repo_cls.return_value = mock_host_repo

                # Mock availability repository
                mock_avail_repo = AsyncMock()
                mock_avail_repo.is_available_for_slot.return_value = True
                mock_avail_repo_cls.return_value = mock_avail_repo

                # Mock booking repository
                mock_booking_repo = AsyncMock()
                mock_booking_repo.create.return_value = sample_booking
                mock_booking_repo.get_by_id.return_value = sample_booking
                mock_booking_repo_cls.return_value = mock_booking_repo

                # Mock Stripe
                async def mock_payment_intent(*args, **kwargs):
                    return ("pi_test123", "cs_test_secret")

                mock_stripe.create_payment_intent = mock_payment_intent

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        "/api/v1/bookings",
                        json=request_data,
                        headers=get_auth_header(sample_user.id),
                    )

        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.asyncio
    async def test_create_booking_returns_booking_response(
        self,
        mock_db,
        sample_user,
        sample_host_profile,
        sample_booking,
    ):
        """Test that create booking returns a proper booking response."""
        scheduled_start = datetime.now(UTC) + timedelta(days=1)
        while scheduled_start.weekday() != 0:
            scheduled_start += timedelta(days=1)
        scheduled_start = scheduled_start.replace(
            hour=10, minute=0, second=0, microsecond=0
        )

        request_data = {
            "host_id": str(sample_host_profile.id),
            "scheduled_start": scheduled_start.isoformat(),
            "duration_minutes": 60,
        }

        with (
            patch("app.routers.bookings.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.routers.bookings.HostProfileRepository") as mock_host_repo_cls,
            patch("app.routers.bookings.AvailabilityRepository") as mock_avail_repo_cls,
            patch("app.routers.bookings.BookingRepository") as mock_booking_repo_cls,
            patch("app.routers.bookings.stripe_service") as mock_stripe,
            patch("app.routers.bookings.get_settings") as mock_settings,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            with patch("app.core.deps.UserRepository") as mock_user_repo_cls:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_id.return_value = sample_user
                mock_user_repo_cls.return_value = mock_user_repo

                mock_settings_obj = MagicMock()
                mock_settings_obj.stripe_secret_key = "sk_test_123"
                mock_settings.return_value = mock_settings_obj

                mock_host_repo = AsyncMock()
                mock_host_repo.get_by_id.return_value = sample_host_profile
                mock_host_repo_cls.return_value = mock_host_repo

                mock_avail_repo = AsyncMock()
                mock_avail_repo.is_available_for_slot.return_value = True
                mock_avail_repo_cls.return_value = mock_avail_repo

                mock_booking_repo = AsyncMock()
                mock_booking_repo.create.return_value = sample_booking
                mock_booking_repo.get_by_id.return_value = sample_booking
                mock_booking_repo_cls.return_value = mock_booking_repo

                async def mock_payment_intent(*args, **kwargs):
                    return ("pi_test123", "cs_test_secret")

                mock_stripe.create_payment_intent = mock_payment_intent

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        "/api/v1/bookings",
                        json=request_data,
                        headers=get_auth_header(sample_user.id),
                    )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "id" in data
        assert "client_id" in data
        assert "host_id" in data
        assert "status" in data
        assert data["status"] == BookingStatus.PENDING.value
        assert "amount_cents" in data
        assert "platform_fee_cents" in data
        assert "host_payout_cents" in data

    @pytest.mark.asyncio
    async def test_create_booking_host_not_found_returns_404(
        self,
        mock_db,
        sample_user,
    ):
        """Test that booking with non-existent host returns 404."""
        scheduled_start = datetime.now(UTC) + timedelta(days=1)
        request_data = {
            "host_id": str(uuid4()),
            "scheduled_start": scheduled_start.isoformat(),
            "duration_minutes": 60,
        }

        with (
            patch("app.routers.bookings.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.routers.bookings.HostProfileRepository") as mock_host_repo_cls,
            patch("app.routers.bookings.get_settings") as mock_settings,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            with patch("app.core.deps.UserRepository") as mock_user_repo_cls:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_id.return_value = sample_user
                mock_user_repo_cls.return_value = mock_user_repo

                mock_settings_obj = MagicMock()
                mock_settings_obj.stripe_secret_key = "sk_test_123"
                mock_settings.return_value = mock_settings_obj

                mock_host_repo = AsyncMock()
                mock_host_repo.get_by_id.return_value = None  # Host not found
                mock_host_repo_cls.return_value = mock_host_repo

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        "/api/v1/bookings",
                        json=request_data,
                        headers=get_auth_header(sample_user.id),
                    )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Host profile not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_booking_unavailable_slot_returns_409(
        self,
        mock_db,
        sample_user,
        sample_host_profile,
    ):
        """Test that booking an unavailable slot returns 409."""
        scheduled_start = datetime.now(UTC) + timedelta(days=1)
        request_data = {
            "host_id": str(sample_host_profile.id),
            "scheduled_start": scheduled_start.isoformat(),
            "duration_minutes": 60,
        }

        with (
            patch("app.routers.bookings.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.routers.bookings.HostProfileRepository") as mock_host_repo_cls,
            patch("app.routers.bookings.AvailabilityRepository") as mock_avail_repo_cls,
            patch("app.routers.bookings.get_settings") as mock_settings,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            with patch("app.core.deps.UserRepository") as mock_user_repo_cls:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_id.return_value = sample_user
                mock_user_repo_cls.return_value = mock_user_repo

                mock_settings_obj = MagicMock()
                mock_settings_obj.stripe_secret_key = "sk_test_123"
                mock_settings.return_value = mock_settings_obj

                mock_host_repo = AsyncMock()
                mock_host_repo.get_by_id.return_value = sample_host_profile
                mock_host_repo_cls.return_value = mock_host_repo

                mock_avail_repo = AsyncMock()
                mock_avail_repo.is_available_for_slot.return_value = (
                    False  # Slot not available
                )
                mock_avail_repo_cls.return_value = mock_avail_repo

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        "/api/v1/bookings",
                        json=request_data,
                        headers=get_auth_header(sample_user.id),
                    )

        assert response.status_code == status.HTTP_409_CONFLICT
        assert "not available" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_booking_requires_authentication(self):
        """Test that booking requires authentication."""
        request_data = {
            "host_id": str(uuid4()),
            "scheduled_start": datetime.now(UTC).isoformat(),
            "duration_minutes": 60,
        }

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/bookings",
                json=request_data,
                # No auth header
            )

        # Should return 403 (forbidden) when no auth provided due to HTTPBearer
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    @pytest.mark.asyncio
    async def test_create_booking_validates_duration_min(
        self,
        mock_db,
        sample_user,
    ):
        """Test that duration must be at least 30 minutes."""
        request_data = {
            "host_id": str(uuid4()),
            "scheduled_start": datetime.now(UTC).isoformat(),
            "duration_minutes": 15,  # Too short
        }

        with (
            patch("app.routers.bookings.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            with patch("app.core.deps.UserRepository") as mock_user_repo_cls:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_id.return_value = sample_user
                mock_user_repo_cls.return_value = mock_user_repo

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        "/api/v1/bookings",
                        json=request_data,
                        headers=get_auth_header(sample_user.id),
                    )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_create_booking_validates_duration_max(
        self,
        mock_db,
        sample_user,
    ):
        """Test that duration cannot exceed 240 minutes."""
        request_data = {
            "host_id": str(uuid4()),
            "scheduled_start": datetime.now(UTC).isoformat(),
            "duration_minutes": 300,  # Too long
        }

        with (
            patch("app.routers.bookings.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            with patch("app.core.deps.UserRepository") as mock_user_repo_cls:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_id.return_value = sample_user
                mock_user_repo_cls.return_value = mock_user_repo

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        "/api/v1/bookings",
                        json=request_data,
                        headers=get_auth_header(sample_user.id),
                    )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_create_booking_calculates_amount_correctly(
        self,
        mock_db,
        sample_user,
        sample_host_profile,
        sample_booking,
    ):
        """Test that booking amount is calculated correctly from hourly rate."""
        scheduled_start = datetime.now(UTC) + timedelta(days=1)
        while scheduled_start.weekday() != 0:
            scheduled_start += timedelta(days=1)
        scheduled_start = scheduled_start.replace(
            hour=10, minute=0, second=0, microsecond=0
        )

        # 90 minute booking at $50/hour = $75 total (7500 cents)
        request_data = {
            "host_id": str(sample_host_profile.id),
            "scheduled_start": scheduled_start.isoformat(),
            "duration_minutes": 90,
        }

        with (
            patch("app.routers.bookings.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.routers.bookings.HostProfileRepository") as mock_host_repo_cls,
            patch("app.routers.bookings.AvailabilityRepository") as mock_avail_repo_cls,
            patch("app.routers.bookings.BookingRepository") as mock_booking_repo_cls,
            patch("app.routers.bookings.stripe_service") as mock_stripe,
            patch("app.routers.bookings.get_settings") as mock_settings,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            with patch("app.core.deps.UserRepository") as mock_user_repo_cls:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_id.return_value = sample_user
                mock_user_repo_cls.return_value = mock_user_repo

                mock_settings_obj = MagicMock()
                mock_settings_obj.stripe_secret_key = "sk_test_123"
                mock_settings.return_value = mock_settings_obj

                mock_host_repo = AsyncMock()
                mock_host_repo.get_by_id.return_value = sample_host_profile
                mock_host_repo_cls.return_value = mock_host_repo

                mock_avail_repo = AsyncMock()
                mock_avail_repo.is_available_for_slot.return_value = True
                mock_avail_repo_cls.return_value = mock_avail_repo

                mock_booking_repo = AsyncMock()

                # Capture the create call to verify amounts
                create_calls = []

                async def capture_create(**kwargs):
                    create_calls.append(kwargs)
                    return sample_booking

                mock_booking_repo.create.side_effect = capture_create
                mock_booking_repo.get_by_id.return_value = sample_booking
                mock_booking_repo_cls.return_value = mock_booking_repo

                async def mock_payment_intent(*args, **kwargs):
                    return ("pi_test123", "cs_test_secret")

                mock_stripe.create_payment_intent = mock_payment_intent

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        "/api/v1/bookings",
                        json=request_data,
                        headers=get_auth_header(sample_user.id),
                    )

        assert response.status_code == status.HTTP_201_CREATED

        # Verify the booking was created with correct amounts
        assert len(create_calls) == 1
        call_kwargs = create_calls[0]

        # 90 min at $50/hr = $75 = 7500 cents
        expected_amount = int(5000 * 90 / 60)  # 7500
        assert call_kwargs["amount_cents"] == expected_amount

        # Platform fee is 15% = 1125 cents
        expected_platform_fee = int(expected_amount * 15 / 100)  # 1125
        assert call_kwargs["platform_fee_cents"] == expected_platform_fee

        # Host payout = amount - platform fee = 6375 cents
        expected_host_payout = expected_amount - expected_platform_fee  # 6375
        assert call_kwargs["host_payout_cents"] == expected_host_payout

    @pytest.mark.asyncio
    async def test_create_booking_cannot_book_self(
        self,
        mock_db,
        sample_user,
        sample_host_profile,
    ):
        """Test that a user cannot book themselves."""
        # Make the host profile belong to the same user
        sample_host_profile.user_id = str(sample_user.id)

        scheduled_start = datetime.now(UTC) + timedelta(days=1)
        request_data = {
            "host_id": str(sample_host_profile.id),
            "scheduled_start": scheduled_start.isoformat(),
            "duration_minutes": 60,
        }

        with (
            patch("app.routers.bookings.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.routers.bookings.HostProfileRepository") as mock_host_repo_cls,
            patch("app.routers.bookings.get_settings") as mock_settings,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            with patch("app.core.deps.UserRepository") as mock_user_repo_cls:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_id.return_value = sample_user
                mock_user_repo_cls.return_value = mock_user_repo

                mock_settings_obj = MagicMock()
                mock_settings_obj.stripe_secret_key = "sk_test_123"
                mock_settings.return_value = mock_settings_obj

                mock_host_repo = AsyncMock()
                mock_host_repo.get_by_id.return_value = sample_host_profile
                mock_host_repo_cls.return_value = mock_host_repo

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        "/api/v1/bookings",
                        json=request_data,
                        headers=get_auth_header(sample_user.id),
                    )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "cannot book yourself" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_booking_host_no_stripe_returns_400(
        self,
        mock_db,
        sample_user,
        sample_host_profile,
    ):
        """Test that booking fails if host hasn't completed Stripe onboarding."""
        sample_host_profile.stripe_onboarding_complete = False

        scheduled_start = datetime.now(UTC) + timedelta(days=1)
        request_data = {
            "host_id": str(sample_host_profile.id),
            "scheduled_start": scheduled_start.isoformat(),
            "duration_minutes": 60,
        }

        with (
            patch("app.routers.bookings.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.routers.bookings.HostProfileRepository") as mock_host_repo_cls,
            patch("app.routers.bookings.get_settings") as mock_settings,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            with patch("app.core.deps.UserRepository") as mock_user_repo_cls:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_id.return_value = sample_user
                mock_user_repo_cls.return_value = mock_user_repo

                mock_settings_obj = MagicMock()
                mock_settings_obj.stripe_secret_key = "sk_test_123"
                mock_settings.return_value = mock_settings_obj

                mock_host_repo = AsyncMock()
                mock_host_repo.get_by_id.return_value = sample_host_profile
                mock_host_repo_cls.return_value = mock_host_repo

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        "/api/v1/bookings",
                        json=request_data,
                        headers=get_auth_header(sample_user.id),
                    )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "payment setup" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_booking_host_no_hourly_rate_returns_400(
        self,
        mock_db,
        sample_user,
        sample_host_profile,
    ):
        """Test that booking fails if host hasn't set an hourly rate."""
        sample_host_profile.hourly_rate_cents = None

        scheduled_start = datetime.now(UTC) + timedelta(days=1)
        request_data = {
            "host_id": str(sample_host_profile.id),
            "scheduled_start": scheduled_start.isoformat(),
            "duration_minutes": 60,
        }

        with (
            patch("app.routers.bookings.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.routers.bookings.HostProfileRepository") as mock_host_repo_cls,
            patch("app.routers.bookings.get_settings") as mock_settings,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            with patch("app.core.deps.UserRepository") as mock_user_repo_cls:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_id.return_value = sample_user
                mock_user_repo_cls.return_value = mock_user_repo

                mock_settings_obj = MagicMock()
                mock_settings_obj.stripe_secret_key = "sk_test_123"
                mock_settings.return_value = mock_settings_obj

                mock_host_repo = AsyncMock()
                mock_host_repo.get_by_id.return_value = sample_host_profile
                mock_host_repo_cls.return_value = mock_host_repo

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        "/api/v1/bookings",
                        json=request_data,
                        headers=get_auth_header(sample_user.id),
                    )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "hourly rate" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_booking_creates_pending_booking_record(
        self,
        mock_db,
        sample_user,
        sample_host_profile,
        sample_booking,
    ):
        """Test that a booking is created with PENDING status."""
        scheduled_start = datetime.now(UTC) + timedelta(days=1)
        while scheduled_start.weekday() != 0:
            scheduled_start += timedelta(days=1)
        scheduled_start = scheduled_start.replace(
            hour=10, minute=0, second=0, microsecond=0
        )

        request_data = {
            "host_id": str(sample_host_profile.id),
            "scheduled_start": scheduled_start.isoformat(),
            "duration_minutes": 60,
        }

        with (
            patch("app.routers.bookings.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.routers.bookings.HostProfileRepository") as mock_host_repo_cls,
            patch("app.routers.bookings.AvailabilityRepository") as mock_avail_repo_cls,
            patch("app.routers.bookings.BookingRepository") as mock_booking_repo_cls,
            patch("app.routers.bookings.stripe_service") as mock_stripe,
            patch("app.routers.bookings.get_settings") as mock_settings,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            with patch("app.core.deps.UserRepository") as mock_user_repo_cls:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_id.return_value = sample_user
                mock_user_repo_cls.return_value = mock_user_repo

                mock_settings_obj = MagicMock()
                mock_settings_obj.stripe_secret_key = "sk_test_123"
                mock_settings.return_value = mock_settings_obj

                mock_host_repo = AsyncMock()
                mock_host_repo.get_by_id.return_value = sample_host_profile
                mock_host_repo_cls.return_value = mock_host_repo

                mock_avail_repo = AsyncMock()
                mock_avail_repo.is_available_for_slot.return_value = True
                mock_avail_repo_cls.return_value = mock_avail_repo

                mock_booking_repo = AsyncMock()
                mock_booking_repo.create.return_value = sample_booking
                mock_booking_repo.get_by_id.return_value = sample_booking
                mock_booking_repo_cls.return_value = mock_booking_repo

                async def mock_payment_intent(*args, **kwargs):
                    return ("pi_test123", "cs_test_secret")

                mock_stripe.create_payment_intent = mock_payment_intent

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        "/api/v1/bookings",
                        json=request_data,
                        headers=get_auth_header(sample_user.id),
                    )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["status"] == BookingStatus.PENDING.value

    @pytest.mark.asyncio
    async def test_create_booking_with_optional_fields(
        self,
        mock_db,
        sample_user,
        sample_host_profile,
        sample_booking,
        sample_dance_style,
    ):
        """Test creating a booking with optional fields (dance_style, location, notes)."""
        scheduled_start = datetime.now(UTC) + timedelta(days=1)
        while scheduled_start.weekday() != 0:
            scheduled_start += timedelta(days=1)
        scheduled_start = scheduled_start.replace(
            hour=10, minute=0, second=0, microsecond=0
        )

        request_data = {
            "host_id": str(sample_host_profile.id),
            "dance_style_id": str(sample_dance_style.id),
            "scheduled_start": scheduled_start.isoformat(),
            "duration_minutes": 60,
            "location": {
                "latitude": 40.7128,
                "longitude": -74.0060,
                "location_name": "NYC Dance Studio",
                "location_notes": "2nd floor",
            },
            "client_notes": "Beginner looking to learn salsa",
        }

        with (
            patch("app.routers.bookings.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.routers.bookings.HostProfileRepository") as mock_host_repo_cls,
            patch("app.routers.bookings.AvailabilityRepository") as mock_avail_repo_cls,
            patch("app.routers.bookings.BookingRepository") as mock_booking_repo_cls,
            patch("app.routers.bookings.stripe_service") as mock_stripe,
            patch("app.routers.bookings.get_settings") as mock_settings,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            with patch("app.core.deps.UserRepository") as mock_user_repo_cls:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_id.return_value = sample_user
                mock_user_repo_cls.return_value = mock_user_repo

                mock_settings_obj = MagicMock()
                mock_settings_obj.stripe_secret_key = "sk_test_123"
                mock_settings.return_value = mock_settings_obj

                mock_host_repo = AsyncMock()
                mock_host_repo.get_by_id.return_value = sample_host_profile
                mock_host_repo.get_dance_style_by_id.return_value = sample_dance_style
                mock_host_repo_cls.return_value = mock_host_repo

                mock_avail_repo = AsyncMock()
                mock_avail_repo.is_available_for_slot.return_value = True
                mock_avail_repo_cls.return_value = mock_avail_repo

                mock_booking_repo = AsyncMock()
                mock_booking_repo.create.return_value = sample_booking
                mock_booking_repo.get_by_id.return_value = sample_booking
                mock_booking_repo_cls.return_value = mock_booking_repo

                async def mock_payment_intent(*args, **kwargs):
                    return ("pi_test123", "cs_test_secret")

                mock_stripe.create_payment_intent = mock_payment_intent

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        "/api/v1/bookings",
                        json=request_data,
                        headers=get_auth_header(sample_user.id),
                    )

        assert response.status_code == status.HTTP_201_CREATED


class TestBookingPricing:
    """Tests for booking pricing calculations."""

    def test_platform_fee_calculation_15_percent(self):
        """Test that platform fee is calculated as 15% of total."""
        from app.routers.bookings import _calculate_platform_fee

        # $100 booking = $15 platform fee (1500 cents)
        assert _calculate_platform_fee(10000) == 1500

        # $50 booking = $7.50 platform fee (750 cents)
        assert _calculate_platform_fee(5000) == 750

        # $75 booking = $11.25 platform fee (1125 cents)
        assert _calculate_platform_fee(7500) == 1125

    def test_platform_fee_rounds_down(self):
        """Test that platform fee rounds down (truncates) fractional cents."""
        from app.routers.bookings import _calculate_platform_fee

        # $33.33 booking (3333 cents) = 15% = 499.95 -> 499 cents
        # Actually 3333 * 15 / 100 = 499 (integer division)
        assert _calculate_platform_fee(3333) == 499


class TestConfirmBookingEndpoint:
    """Tests for POST /api/v1/bookings/{id}/confirm endpoint."""

    @pytest.mark.asyncio
    async def test_confirm_booking_endpoint_exists(
        self,
        mock_db,
        sample_host_user,
        sample_booking,
    ):
        """Test that the confirm booking endpoint exists and returns 200."""
        # Set booking status to PENDING for confirmation
        sample_booking.status = BookingStatus.PENDING

        with (
            patch("app.routers.bookings.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.routers.bookings.BookingRepository") as mock_booking_repo_cls,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_host_user.id), token_type="access"
            )

            with patch("app.core.deps.UserRepository") as mock_user_repo_cls:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_id.return_value = sample_host_user
                mock_user_repo_cls.return_value = mock_user_repo

                mock_booking_repo = AsyncMock()

                # Create confirmed booking for second get_by_id call
                confirmed_booking = MagicMock()
                confirmed_booking.id = sample_booking.id
                confirmed_booking.client_id = sample_booking.client_id
                confirmed_booking.host_id = sample_booking.host_id
                confirmed_booking.host_profile_id = sample_booking.host_profile_id
                confirmed_booking.dance_style_id = sample_booking.dance_style_id
                confirmed_booking.status = BookingStatus.CONFIRMED
                confirmed_booking.scheduled_start = sample_booking.scheduled_start
                confirmed_booking.scheduled_end = sample_booking.scheduled_end
                confirmed_booking.actual_start = None
                confirmed_booking.actual_end = None
                confirmed_booking.duration_minutes = sample_booking.duration_minutes
                confirmed_booking.hourly_rate_cents = sample_booking.hourly_rate_cents
                confirmed_booking.amount_cents = sample_booking.amount_cents
                confirmed_booking.platform_fee_cents = sample_booking.platform_fee_cents
                confirmed_booking.host_payout_cents = sample_booking.host_payout_cents
                confirmed_booking.location = None
                confirmed_booking.location_name = sample_booking.location_name
                confirmed_booking.location_notes = sample_booking.location_notes
                confirmed_booking.client_notes = sample_booking.client_notes
                confirmed_booking.host_notes = None
                confirmed_booking.cancellation_reason = None
                confirmed_booking.cancelled_by_id = None
                confirmed_booking.cancelled_at = None
                confirmed_booking.stripe_payment_intent_id = (
                    sample_booking.stripe_payment_intent_id
                )
                confirmed_booking.created_at = sample_booking.created_at
                confirmed_booking.updated_at = sample_booking.updated_at
                confirmed_booking.client = sample_booking.client
                confirmed_booking.host = sample_booking.host
                confirmed_booking.host_profile = sample_booking.host_profile
                confirmed_booking.dance_style = sample_booking.dance_style

                # First call returns pending, second call (after update) returns confirmed
                mock_booking_repo.get_by_id.side_effect = [
                    sample_booking,
                    confirmed_booking,
                ]
                mock_booking_repo.update_status.return_value = confirmed_booking
                mock_booking_repo_cls.return_value = mock_booking_repo

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        f"/api/v1/bookings/{sample_booking.id}/confirm",
                        headers=get_auth_header(sample_host_user.id),
                    )

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_confirm_booking_only_host_can_confirm(
        self,
        mock_db,
        sample_user,  # Client user, not the host
        sample_booking,
    ):
        """Test that only the host can confirm their booking."""
        sample_booking.status = BookingStatus.PENDING

        with (
            patch("app.routers.bookings.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.routers.bookings.BookingRepository") as mock_booking_repo_cls,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            with patch("app.core.deps.UserRepository") as mock_user_repo_cls:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_id.return_value = sample_user
                mock_user_repo_cls.return_value = mock_user_repo

                mock_booking_repo = AsyncMock()
                mock_booking_repo.get_by_id.return_value = sample_booking
                mock_booking_repo_cls.return_value = mock_booking_repo

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        f"/api/v1/bookings/{sample_booking.id}/confirm",
                        headers=get_auth_header(sample_user.id),
                    )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Only the host can confirm" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_confirm_booking_updates_status_to_confirmed(
        self,
        mock_db,
        sample_host_user,
        sample_booking,
    ):
        """Test that confirm updates booking status to CONFIRMED."""
        sample_booking.status = BookingStatus.PENDING

        with (
            patch("app.routers.bookings.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.routers.bookings.BookingRepository") as mock_booking_repo_cls,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_host_user.id), token_type="access"
            )

            with patch("app.core.deps.UserRepository") as mock_user_repo_cls:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_id.return_value = sample_host_user
                mock_user_repo_cls.return_value = mock_user_repo

                mock_booking_repo = AsyncMock()

                # Track update_status calls
                update_calls = []

                # Create confirmed booking for second get_by_id call
                confirmed_booking = MagicMock()
                confirmed_booking.id = sample_booking.id
                confirmed_booking.client_id = sample_booking.client_id
                confirmed_booking.host_id = sample_booking.host_id
                confirmed_booking.host_profile_id = sample_booking.host_profile_id
                confirmed_booking.dance_style_id = sample_booking.dance_style_id
                confirmed_booking.status = BookingStatus.CONFIRMED
                confirmed_booking.scheduled_start = sample_booking.scheduled_start
                confirmed_booking.scheduled_end = sample_booking.scheduled_end
                confirmed_booking.actual_start = None
                confirmed_booking.actual_end = None
                confirmed_booking.duration_minutes = sample_booking.duration_minutes
                confirmed_booking.hourly_rate_cents = sample_booking.hourly_rate_cents
                confirmed_booking.amount_cents = sample_booking.amount_cents
                confirmed_booking.platform_fee_cents = sample_booking.platform_fee_cents
                confirmed_booking.host_payout_cents = sample_booking.host_payout_cents
                confirmed_booking.location = None
                confirmed_booking.location_name = sample_booking.location_name
                confirmed_booking.location_notes = sample_booking.location_notes
                confirmed_booking.client_notes = sample_booking.client_notes
                confirmed_booking.host_notes = None
                confirmed_booking.cancellation_reason = None
                confirmed_booking.cancelled_by_id = None
                confirmed_booking.cancelled_at = None
                confirmed_booking.stripe_payment_intent_id = (
                    sample_booking.stripe_payment_intent_id
                )
                confirmed_booking.created_at = sample_booking.created_at
                confirmed_booking.updated_at = sample_booking.updated_at
                confirmed_booking.client = sample_booking.client
                confirmed_booking.host = sample_booking.host
                confirmed_booking.host_profile = sample_booking.host_profile
                confirmed_booking.dance_style = sample_booking.dance_style

                # First call returns pending, second call (after update) returns confirmed
                mock_booking_repo.get_by_id.side_effect = [
                    sample_booking,
                    confirmed_booking,
                ]

                async def mock_update_status(booking_id, new_status, **kwargs):
                    update_calls.append((booking_id, new_status, kwargs))
                    return confirmed_booking

                mock_booking_repo.update_status = mock_update_status
                mock_booking_repo_cls.return_value = mock_booking_repo

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        f"/api/v1/bookings/{sample_booking.id}/confirm",
                        headers=get_auth_header(sample_host_user.id),
                    )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == BookingStatus.CONFIRMED.value

        # Verify update_status was called with CONFIRMED status
        assert len(update_calls) == 1
        _, new_status, _ = update_calls[0]
        assert new_status == BookingStatus.CONFIRMED

    @pytest.mark.asyncio
    async def test_confirm_booking_not_pending_returns_400(
        self,
        mock_db,
        sample_host_user,
        sample_booking,
    ):
        """Test that confirming a non-pending booking returns 400."""
        # Set booking to CONFIRMED (not PENDING)
        sample_booking.status = BookingStatus.CONFIRMED

        with (
            patch("app.routers.bookings.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.routers.bookings.BookingRepository") as mock_booking_repo_cls,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_host_user.id), token_type="access"
            )

            with patch("app.core.deps.UserRepository") as mock_user_repo_cls:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_id.return_value = sample_host_user
                mock_user_repo_cls.return_value = mock_user_repo

                mock_booking_repo = AsyncMock()
                mock_booking_repo.get_by_id.return_value = sample_booking
                mock_booking_repo_cls.return_value = mock_booking_repo

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        f"/api/v1/bookings/{sample_booking.id}/confirm",
                        headers=get_auth_header(sample_host_user.id),
                    )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "pending" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_confirm_booking_cancelled_returns_400(
        self,
        mock_db,
        sample_host_user,
        sample_booking,
    ):
        """Test that confirming a cancelled booking returns 400."""
        sample_booking.status = BookingStatus.CANCELLED

        with (
            patch("app.routers.bookings.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.routers.bookings.BookingRepository") as mock_booking_repo_cls,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_host_user.id), token_type="access"
            )

            with patch("app.core.deps.UserRepository") as mock_user_repo_cls:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_id.return_value = sample_host_user
                mock_user_repo_cls.return_value = mock_user_repo

                mock_booking_repo = AsyncMock()
                mock_booking_repo.get_by_id.return_value = sample_booking
                mock_booking_repo_cls.return_value = mock_booking_repo

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        f"/api/v1/bookings/{sample_booking.id}/confirm",
                        headers=get_auth_header(sample_host_user.id),
                    )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_confirm_booking_not_found_returns_404(
        self,
        mock_db,
        sample_host_user,
    ):
        """Test that confirming a non-existent booking returns 404."""
        non_existent_id = uuid4()

        with (
            patch("app.routers.bookings.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.routers.bookings.BookingRepository") as mock_booking_repo_cls,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_host_user.id), token_type="access"
            )

            with patch("app.core.deps.UserRepository") as mock_user_repo_cls:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_id.return_value = sample_host_user
                mock_user_repo_cls.return_value = mock_user_repo

                mock_booking_repo = AsyncMock()
                mock_booking_repo.get_by_id.return_value = None
                mock_booking_repo_cls.return_value = mock_booking_repo

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        f"/api/v1/bookings/{non_existent_id}/confirm",
                        headers=get_auth_header(sample_host_user.id),
                    )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_confirm_booking_requires_authentication(self):
        """Test that confirming a booking requires authentication."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                f"/api/v1/bookings/{uuid4()}/confirm",
                # No auth header
            )

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    @pytest.mark.asyncio
    async def test_confirm_booking_returns_booking_response(
        self,
        mock_db,
        sample_host_user,
        sample_booking,
    ):
        """Test that confirm returns a proper booking response with details."""
        sample_booking.status = BookingStatus.PENDING

        with (
            patch("app.routers.bookings.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.routers.bookings.BookingRepository") as mock_booking_repo_cls,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_host_user.id), token_type="access"
            )

            with patch("app.core.deps.UserRepository") as mock_user_repo_cls:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_id.return_value = sample_host_user
                mock_user_repo_cls.return_value = mock_user_repo

                mock_booking_repo = AsyncMock()

                confirmed_booking = MagicMock()
                confirmed_booking.id = sample_booking.id
                confirmed_booking.client_id = sample_booking.client_id
                confirmed_booking.host_id = sample_booking.host_id
                confirmed_booking.host_profile_id = sample_booking.host_profile_id
                confirmed_booking.dance_style_id = sample_booking.dance_style_id
                confirmed_booking.status = BookingStatus.CONFIRMED
                confirmed_booking.scheduled_start = sample_booking.scheduled_start
                confirmed_booking.scheduled_end = sample_booking.scheduled_end
                confirmed_booking.actual_start = None
                confirmed_booking.actual_end = None
                confirmed_booking.duration_minutes = sample_booking.duration_minutes
                confirmed_booking.hourly_rate_cents = sample_booking.hourly_rate_cents
                confirmed_booking.amount_cents = sample_booking.amount_cents
                confirmed_booking.platform_fee_cents = sample_booking.platform_fee_cents
                confirmed_booking.host_payout_cents = sample_booking.host_payout_cents
                confirmed_booking.location = None
                confirmed_booking.location_name = sample_booking.location_name
                confirmed_booking.location_notes = sample_booking.location_notes
                confirmed_booking.client_notes = sample_booking.client_notes
                confirmed_booking.host_notes = None
                confirmed_booking.cancellation_reason = None
                confirmed_booking.cancelled_by_id = None
                confirmed_booking.cancelled_at = None
                confirmed_booking.stripe_payment_intent_id = (
                    sample_booking.stripe_payment_intent_id
                )
                confirmed_booking.created_at = sample_booking.created_at
                confirmed_booking.updated_at = sample_booking.updated_at
                confirmed_booking.client = sample_booking.client
                confirmed_booking.host = sample_booking.host
                confirmed_booking.host_profile = sample_booking.host_profile
                confirmed_booking.dance_style = sample_booking.dance_style

                # First call returns pending, second call (after update) returns confirmed
                mock_booking_repo.get_by_id.side_effect = [
                    sample_booking,
                    confirmed_booking,
                ]
                mock_booking_repo.update_status.return_value = confirmed_booking
                mock_booking_repo_cls.return_value = mock_booking_repo

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        f"/api/v1/bookings/{sample_booking.id}/confirm",
                        headers=get_auth_header(sample_host_user.id),
                    )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "id" in data
        assert "client_id" in data
        assert "host_id" in data
        assert "status" in data
        assert "client" in data  # Includes details
        assert "host" in data  # Includes details
        assert data["status"] == BookingStatus.CONFIRMED.value


class TestCancelBookingEndpoint:
    """Tests for POST /api/v1/bookings/{id}/cancel endpoint."""

    @pytest.fixture
    def cancelled_booking(self, sample_booking, sample_user):
        """Create a cancelled version of the sample booking."""
        cancelled = MagicMock()
        cancelled.id = sample_booking.id
        cancelled.client_id = sample_booking.client_id
        cancelled.host_id = sample_booking.host_id
        cancelled.host_profile_id = sample_booking.host_profile_id
        cancelled.dance_style_id = sample_booking.dance_style_id
        cancelled.status = BookingStatus.CANCELLED
        cancelled.scheduled_start = sample_booking.scheduled_start
        cancelled.scheduled_end = sample_booking.scheduled_end
        cancelled.actual_start = None
        cancelled.actual_end = None
        cancelled.duration_minutes = sample_booking.duration_minutes
        cancelled.hourly_rate_cents = sample_booking.hourly_rate_cents
        cancelled.amount_cents = sample_booking.amount_cents
        cancelled.platform_fee_cents = sample_booking.platform_fee_cents
        cancelled.host_payout_cents = sample_booking.host_payout_cents
        cancelled.location = None
        cancelled.location_name = sample_booking.location_name
        cancelled.location_notes = sample_booking.location_notes
        cancelled.client_notes = sample_booking.client_notes
        cancelled.host_notes = None
        cancelled.cancellation_reason = "Changed my plans"
        cancelled.cancelled_by_id = str(sample_user.id)
        cancelled.cancelled_at = datetime.now(UTC)
        cancelled.stripe_payment_intent_id = sample_booking.stripe_payment_intent_id
        cancelled.created_at = sample_booking.created_at
        cancelled.updated_at = datetime.now(UTC)
        cancelled.client = sample_booking.client
        cancelled.host = sample_booking.host
        cancelled.host_profile = sample_booking.host_profile
        cancelled.dance_style = sample_booking.dance_style
        return cancelled

    @pytest.mark.asyncio
    async def test_cancel_booking_endpoint_exists(
        self,
        mock_db,
        sample_user,
        sample_booking,
        cancelled_booking,
    ):
        """Test that the cancel booking endpoint exists and returns 200."""
        sample_booking.status = BookingStatus.PENDING

        with (
            patch("app.routers.bookings.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.routers.bookings.BookingRepository") as mock_booking_repo_cls,
            patch("app.routers.bookings.stripe_service") as mock_stripe,
            patch("app.routers.bookings.get_settings") as mock_settings,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            with patch("app.core.deps.UserRepository") as mock_user_repo_cls:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_id.return_value = sample_user
                mock_user_repo_cls.return_value = mock_user_repo

                mock_settings_obj = MagicMock()
                mock_settings_obj.stripe_secret_key = "sk_test_123"
                mock_settings.return_value = mock_settings_obj

                mock_booking_repo = AsyncMock()
                mock_booking_repo.get_by_id.side_effect = [
                    sample_booking,
                    cancelled_booking,
                ]
                mock_booking_repo.update_status.return_value = cancelled_booking
                mock_booking_repo_cls.return_value = mock_booking_repo

                mock_stripe.cancel_payment_intent = AsyncMock(return_value=True)

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        f"/api/v1/bookings/{sample_booking.id}/cancel",
                        headers=get_auth_header(sample_user.id),
                    )

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_cancel_booking_client_can_cancel(
        self,
        mock_db,
        sample_user,
        sample_booking,
        cancelled_booking,
    ):
        """Test that the client can cancel their booking."""
        sample_booking.status = BookingStatus.PENDING

        with (
            patch("app.routers.bookings.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.routers.bookings.BookingRepository") as mock_booking_repo_cls,
            patch("app.routers.bookings.stripe_service") as mock_stripe,
            patch("app.routers.bookings.get_settings") as mock_settings,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            with patch("app.core.deps.UserRepository") as mock_user_repo_cls:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_id.return_value = sample_user
                mock_user_repo_cls.return_value = mock_user_repo

                mock_settings_obj = MagicMock()
                mock_settings_obj.stripe_secret_key = "sk_test_123"
                mock_settings.return_value = mock_settings_obj

                mock_booking_repo = AsyncMock()
                mock_booking_repo.get_by_id.side_effect = [
                    sample_booking,
                    cancelled_booking,
                ]
                mock_booking_repo.update_status.return_value = cancelled_booking
                mock_booking_repo_cls.return_value = mock_booking_repo

                mock_stripe.cancel_payment_intent = AsyncMock(return_value=True)

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        f"/api/v1/bookings/{sample_booking.id}/cancel",
                        headers=get_auth_header(sample_user.id),
                    )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == BookingStatus.CANCELLED.value

    @pytest.mark.asyncio
    async def test_cancel_booking_host_can_cancel(
        self,
        mock_db,
        sample_host_user,
        sample_booking,
    ):
        """Test that the host can cancel their booking."""
        sample_booking.status = BookingStatus.PENDING

        # Create cancelled booking with host as canceller
        cancelled_booking = MagicMock()
        cancelled_booking.id = sample_booking.id
        cancelled_booking.client_id = sample_booking.client_id
        cancelled_booking.host_id = sample_booking.host_id
        cancelled_booking.host_profile_id = sample_booking.host_profile_id
        cancelled_booking.dance_style_id = sample_booking.dance_style_id
        cancelled_booking.status = BookingStatus.CANCELLED
        cancelled_booking.scheduled_start = sample_booking.scheduled_start
        cancelled_booking.scheduled_end = sample_booking.scheduled_end
        cancelled_booking.actual_start = None
        cancelled_booking.actual_end = None
        cancelled_booking.duration_minutes = sample_booking.duration_minutes
        cancelled_booking.hourly_rate_cents = sample_booking.hourly_rate_cents
        cancelled_booking.amount_cents = sample_booking.amount_cents
        cancelled_booking.platform_fee_cents = sample_booking.platform_fee_cents
        cancelled_booking.host_payout_cents = sample_booking.host_payout_cents
        cancelled_booking.location = None
        cancelled_booking.location_name = sample_booking.location_name
        cancelled_booking.location_notes = sample_booking.location_notes
        cancelled_booking.client_notes = sample_booking.client_notes
        cancelled_booking.host_notes = None
        cancelled_booking.cancellation_reason = None
        cancelled_booking.cancelled_by_id = str(sample_host_user.id)
        cancelled_booking.cancelled_at = datetime.now(UTC)
        cancelled_booking.stripe_payment_intent_id = (
            sample_booking.stripe_payment_intent_id
        )
        cancelled_booking.created_at = sample_booking.created_at
        cancelled_booking.updated_at = datetime.now(UTC)
        cancelled_booking.client = sample_booking.client
        cancelled_booking.host = sample_booking.host
        cancelled_booking.host_profile = sample_booking.host_profile
        cancelled_booking.dance_style = sample_booking.dance_style

        with (
            patch("app.routers.bookings.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.routers.bookings.BookingRepository") as mock_booking_repo_cls,
            patch("app.routers.bookings.stripe_service") as mock_stripe,
            patch("app.routers.bookings.get_settings") as mock_settings,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_host_user.id), token_type="access"
            )

            with patch("app.core.deps.UserRepository") as mock_user_repo_cls:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_id.return_value = sample_host_user
                mock_user_repo_cls.return_value = mock_user_repo

                mock_settings_obj = MagicMock()
                mock_settings_obj.stripe_secret_key = "sk_test_123"
                mock_settings.return_value = mock_settings_obj

                mock_booking_repo = AsyncMock()
                mock_booking_repo.get_by_id.side_effect = [
                    sample_booking,
                    cancelled_booking,
                ]
                mock_booking_repo.update_status.return_value = cancelled_booking
                mock_booking_repo_cls.return_value = mock_booking_repo

                mock_stripe.cancel_payment_intent = AsyncMock(return_value=True)

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        f"/api/v1/bookings/{sample_booking.id}/cancel",
                        headers=get_auth_header(sample_host_user.id),
                    )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == BookingStatus.CANCELLED.value

    @pytest.mark.asyncio
    async def test_cancel_booking_unrelated_user_returns_403(
        self,
        mock_db,
        sample_booking,
    ):
        """Test that an unrelated user cannot cancel the booking."""
        sample_booking.status = BookingStatus.PENDING

        # Create a random user who is neither client nor host
        random_user = MagicMock(spec=User)
        random_user.id = uuid4()
        random_user.email = "random@test.com"
        random_user.first_name = "Random"
        random_user.last_name = "User"
        random_user.user_type = UserType.CLIENT
        random_user.is_active = True
        random_user.email_verified = True

        with (
            patch("app.routers.bookings.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.routers.bookings.BookingRepository") as mock_booking_repo_cls,
            patch("app.routers.bookings.get_settings") as mock_settings,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(random_user.id), token_type="access"
            )

            with patch("app.core.deps.UserRepository") as mock_user_repo_cls:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_id.return_value = random_user
                mock_user_repo_cls.return_value = mock_user_repo

                mock_settings_obj = MagicMock()
                mock_settings_obj.stripe_secret_key = "sk_test_123"
                mock_settings.return_value = mock_settings_obj

                mock_booking_repo = AsyncMock()
                mock_booking_repo.get_by_id.return_value = sample_booking
                mock_booking_repo_cls.return_value = mock_booking_repo

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        f"/api/v1/bookings/{sample_booking.id}/cancel",
                        headers=get_auth_header(random_user.id),
                    )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "client or host" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_cancel_booking_releases_stripe_authorization(
        self,
        mock_db,
        sample_user,
        sample_booking,
        cancelled_booking,
    ):
        """Test that cancellation releases the Stripe payment authorization."""
        sample_booking.status = BookingStatus.PENDING

        cancel_calls = []

        async def mock_cancel_payment_intent(payment_intent_id):
            cancel_calls.append(payment_intent_id)
            return True

        with (
            patch("app.routers.bookings.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.routers.bookings.BookingRepository") as mock_booking_repo_cls,
            patch("app.routers.bookings.stripe_service") as mock_stripe,
            patch("app.routers.bookings.get_settings") as mock_settings,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            with patch("app.core.deps.UserRepository") as mock_user_repo_cls:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_id.return_value = sample_user
                mock_user_repo_cls.return_value = mock_user_repo

                mock_settings_obj = MagicMock()
                mock_settings_obj.stripe_secret_key = "sk_test_123"
                mock_settings.return_value = mock_settings_obj

                mock_booking_repo = AsyncMock()
                mock_booking_repo.get_by_id.side_effect = [
                    sample_booking,
                    cancelled_booking,
                ]
                mock_booking_repo.update_status.return_value = cancelled_booking
                mock_booking_repo_cls.return_value = mock_booking_repo

                mock_stripe.cancel_payment_intent = mock_cancel_payment_intent

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        f"/api/v1/bookings/{sample_booking.id}/cancel",
                        headers=get_auth_header(sample_user.id),
                    )

        assert response.status_code == status.HTTP_200_OK
        # Verify Stripe cancel was called with the payment intent ID
        assert len(cancel_calls) == 1
        assert cancel_calls[0] == sample_booking.stripe_payment_intent_id

    @pytest.mark.asyncio
    async def test_cancel_booking_updates_status_to_cancelled(
        self,
        mock_db,
        sample_user,
        sample_booking,
        cancelled_booking,
    ):
        """Test that cancel updates booking status to CANCELLED."""
        sample_booking.status = BookingStatus.PENDING

        update_calls = []

        async def mock_update_status(booking_id, new_status, **kwargs):
            update_calls.append((booking_id, new_status, kwargs))
            return cancelled_booking

        with (
            patch("app.routers.bookings.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.routers.bookings.BookingRepository") as mock_booking_repo_cls,
            patch("app.routers.bookings.stripe_service") as mock_stripe,
            patch("app.routers.bookings.get_settings") as mock_settings,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            with patch("app.core.deps.UserRepository") as mock_user_repo_cls:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_id.return_value = sample_user
                mock_user_repo_cls.return_value = mock_user_repo

                mock_settings_obj = MagicMock()
                mock_settings_obj.stripe_secret_key = "sk_test_123"
                mock_settings.return_value = mock_settings_obj

                mock_booking_repo = AsyncMock()
                mock_booking_repo.get_by_id.side_effect = [
                    sample_booking,
                    cancelled_booking,
                ]
                mock_booking_repo.update_status = mock_update_status
                mock_booking_repo_cls.return_value = mock_booking_repo

                mock_stripe.cancel_payment_intent = AsyncMock(return_value=True)

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        f"/api/v1/bookings/{sample_booking.id}/cancel",
                        headers=get_auth_header(sample_user.id),
                    )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == BookingStatus.CANCELLED.value

        # Verify update_status was called with CANCELLED status
        assert len(update_calls) == 1
        _, new_status, kwargs = update_calls[0]
        assert new_status == BookingStatus.CANCELLED
        assert "cancelled_by_id" in kwargs

    @pytest.mark.asyncio
    async def test_cancel_booking_with_reason(
        self,
        mock_db,
        sample_user,
        sample_booking,
        cancelled_booking,
    ):
        """Test that cancellation reason is saved."""
        sample_booking.status = BookingStatus.PENDING
        cancelled_booking.cancellation_reason = "Schedule conflict"

        update_calls = []

        async def mock_update_status(booking_id, new_status, **kwargs):
            update_calls.append((booking_id, new_status, kwargs))
            return cancelled_booking

        with (
            patch("app.routers.bookings.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.routers.bookings.BookingRepository") as mock_booking_repo_cls,
            patch("app.routers.bookings.stripe_service") as mock_stripe,
            patch("app.routers.bookings.get_settings") as mock_settings,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            with patch("app.core.deps.UserRepository") as mock_user_repo_cls:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_id.return_value = sample_user
                mock_user_repo_cls.return_value = mock_user_repo

                mock_settings_obj = MagicMock()
                mock_settings_obj.stripe_secret_key = "sk_test_123"
                mock_settings.return_value = mock_settings_obj

                mock_booking_repo = AsyncMock()
                mock_booking_repo.get_by_id.side_effect = [
                    sample_booking,
                    cancelled_booking,
                ]
                mock_booking_repo.update_status = mock_update_status
                mock_booking_repo_cls.return_value = mock_booking_repo

                mock_stripe.cancel_payment_intent = AsyncMock(return_value=True)

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        f"/api/v1/bookings/{sample_booking.id}/cancel",
                        json={"reason": "Schedule conflict"},
                        headers=get_auth_header(sample_user.id),
                    )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["cancellation_reason"] == "Schedule conflict"

        # Verify the reason was passed to update_status
        assert len(update_calls) == 1
        _, _, kwargs = update_calls[0]
        assert kwargs["cancellation_reason"] == "Schedule conflict"

    @pytest.mark.asyncio
    async def test_cancel_booking_already_cancelled_returns_400(
        self,
        mock_db,
        sample_user,
        sample_booking,
    ):
        """Test that cancelling an already cancelled booking returns 400."""
        sample_booking.status = BookingStatus.CANCELLED

        with (
            patch("app.routers.bookings.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.routers.bookings.BookingRepository") as mock_booking_repo_cls,
            patch("app.routers.bookings.get_settings") as mock_settings,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            with patch("app.core.deps.UserRepository") as mock_user_repo_cls:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_id.return_value = sample_user
                mock_user_repo_cls.return_value = mock_user_repo

                mock_settings_obj = MagicMock()
                mock_settings_obj.stripe_secret_key = "sk_test_123"
                mock_settings.return_value = mock_settings_obj

                mock_booking_repo = AsyncMock()
                mock_booking_repo.get_by_id.return_value = sample_booking
                mock_booking_repo_cls.return_value = mock_booking_repo

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        f"/api/v1/bookings/{sample_booking.id}/cancel",
                        headers=get_auth_header(sample_user.id),
                    )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "cancelled" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_cancel_booking_completed_returns_400(
        self,
        mock_db,
        sample_user,
        sample_booking,
    ):
        """Test that cancelling a completed booking returns 400."""
        sample_booking.status = BookingStatus.COMPLETED

        with (
            patch("app.routers.bookings.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.routers.bookings.BookingRepository") as mock_booking_repo_cls,
            patch("app.routers.bookings.get_settings") as mock_settings,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            with patch("app.core.deps.UserRepository") as mock_user_repo_cls:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_id.return_value = sample_user
                mock_user_repo_cls.return_value = mock_user_repo

                mock_settings_obj = MagicMock()
                mock_settings_obj.stripe_secret_key = "sk_test_123"
                mock_settings.return_value = mock_settings_obj

                mock_booking_repo = AsyncMock()
                mock_booking_repo.get_by_id.return_value = sample_booking
                mock_booking_repo_cls.return_value = mock_booking_repo

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        f"/api/v1/bookings/{sample_booking.id}/cancel",
                        headers=get_auth_header(sample_user.id),
                    )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "completed" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_cancel_booking_in_progress_returns_400(
        self,
        mock_db,
        sample_user,
        sample_booking,
    ):
        """Test that cancelling an in-progress booking returns 400."""
        sample_booking.status = BookingStatus.IN_PROGRESS

        with (
            patch("app.routers.bookings.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.routers.bookings.BookingRepository") as mock_booking_repo_cls,
            patch("app.routers.bookings.get_settings") as mock_settings,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            with patch("app.core.deps.UserRepository") as mock_user_repo_cls:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_id.return_value = sample_user
                mock_user_repo_cls.return_value = mock_user_repo

                mock_settings_obj = MagicMock()
                mock_settings_obj.stripe_secret_key = "sk_test_123"
                mock_settings.return_value = mock_settings_obj

                mock_booking_repo = AsyncMock()
                mock_booking_repo.get_by_id.return_value = sample_booking
                mock_booking_repo_cls.return_value = mock_booking_repo

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        f"/api/v1/bookings/{sample_booking.id}/cancel",
                        headers=get_auth_header(sample_user.id),
                    )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "in_progress" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_cancel_booking_not_found_returns_404(
        self,
        mock_db,
        sample_user,
    ):
        """Test that cancelling a non-existent booking returns 404."""
        non_existent_id = uuid4()

        with (
            patch("app.routers.bookings.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.routers.bookings.BookingRepository") as mock_booking_repo_cls,
            patch("app.routers.bookings.get_settings") as mock_settings,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            with patch("app.core.deps.UserRepository") as mock_user_repo_cls:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_id.return_value = sample_user
                mock_user_repo_cls.return_value = mock_user_repo

                mock_settings_obj = MagicMock()
                mock_settings_obj.stripe_secret_key = "sk_test_123"
                mock_settings.return_value = mock_settings_obj

                mock_booking_repo = AsyncMock()
                mock_booking_repo.get_by_id.return_value = None
                mock_booking_repo_cls.return_value = mock_booking_repo

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        f"/api/v1/bookings/{non_existent_id}/cancel",
                        headers=get_auth_header(sample_user.id),
                    )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_cancel_booking_requires_authentication(self):
        """Test that cancelling a booking requires authentication."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                f"/api/v1/bookings/{uuid4()}/cancel",
                # No auth header
            )

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    @pytest.mark.asyncio
    async def test_cancel_booking_confirmed_status_can_cancel(
        self,
        mock_db,
        sample_user,
        sample_booking,
        cancelled_booking,
    ):
        """Test that a confirmed booking can be cancelled."""
        sample_booking.status = BookingStatus.CONFIRMED

        with (
            patch("app.routers.bookings.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.routers.bookings.BookingRepository") as mock_booking_repo_cls,
            patch("app.routers.bookings.stripe_service") as mock_stripe,
            patch("app.routers.bookings.get_settings") as mock_settings,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            with patch("app.core.deps.UserRepository") as mock_user_repo_cls:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_id.return_value = sample_user
                mock_user_repo_cls.return_value = mock_user_repo

                mock_settings_obj = MagicMock()
                mock_settings_obj.stripe_secret_key = "sk_test_123"
                mock_settings.return_value = mock_settings_obj

                mock_booking_repo = AsyncMock()
                mock_booking_repo.get_by_id.side_effect = [
                    sample_booking,
                    cancelled_booking,
                ]
                mock_booking_repo.update_status.return_value = cancelled_booking
                mock_booking_repo_cls.return_value = mock_booking_repo

                mock_stripe.cancel_payment_intent = AsyncMock(return_value=True)

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        f"/api/v1/bookings/{sample_booking.id}/cancel",
                        headers=get_auth_header(sample_user.id),
                    )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == BookingStatus.CANCELLED.value


class TestCompleteBookingEndpoint:
    """Tests for POST /api/v1/bookings/{id}/complete endpoint."""

    @pytest.fixture
    def in_progress_booking(self, sample_booking):
        """Create an in_progress version of the sample booking."""
        in_progress = MagicMock()
        in_progress.id = sample_booking.id
        in_progress.client_id = sample_booking.client_id
        in_progress.host_id = sample_booking.host_id
        in_progress.host_profile_id = sample_booking.host_profile_id
        in_progress.dance_style_id = sample_booking.dance_style_id
        in_progress.status = BookingStatus.IN_PROGRESS
        in_progress.scheduled_start = sample_booking.scheduled_start
        in_progress.scheduled_end = sample_booking.scheduled_end
        in_progress.actual_start = datetime.now(UTC) - timedelta(hours=1)
        in_progress.actual_end = None
        in_progress.duration_minutes = sample_booking.duration_minutes
        in_progress.hourly_rate_cents = sample_booking.hourly_rate_cents
        in_progress.amount_cents = sample_booking.amount_cents
        in_progress.platform_fee_cents = sample_booking.platform_fee_cents
        in_progress.host_payout_cents = sample_booking.host_payout_cents
        in_progress.location = None
        in_progress.location_name = sample_booking.location_name
        in_progress.location_notes = sample_booking.location_notes
        in_progress.client_notes = sample_booking.client_notes
        in_progress.host_notes = None
        in_progress.cancellation_reason = None
        in_progress.cancelled_by_id = None
        in_progress.cancelled_at = None
        in_progress.stripe_payment_intent_id = sample_booking.stripe_payment_intent_id
        in_progress.stripe_transfer_id = None
        in_progress.created_at = sample_booking.created_at
        in_progress.updated_at = datetime.now(UTC)
        in_progress.client = sample_booking.client
        in_progress.host = sample_booking.host
        in_progress.host_profile = sample_booking.host_profile
        in_progress.dance_style = sample_booking.dance_style
        return in_progress

    @pytest.fixture
    def completed_booking(self, sample_booking):
        """Create a completed version of the sample booking."""
        completed = MagicMock()
        completed.id = sample_booking.id
        completed.client_id = sample_booking.client_id
        completed.host_id = sample_booking.host_id
        completed.host_profile_id = sample_booking.host_profile_id
        completed.dance_style_id = sample_booking.dance_style_id
        completed.status = BookingStatus.COMPLETED
        completed.scheduled_start = sample_booking.scheduled_start
        completed.scheduled_end = sample_booking.scheduled_end
        completed.actual_start = datetime.now(UTC) - timedelta(hours=1)
        completed.actual_end = datetime.now(UTC)
        completed.duration_minutes = sample_booking.duration_minutes
        completed.hourly_rate_cents = sample_booking.hourly_rate_cents
        completed.amount_cents = sample_booking.amount_cents
        completed.platform_fee_cents = sample_booking.platform_fee_cents
        completed.host_payout_cents = sample_booking.host_payout_cents
        completed.location = None
        completed.location_name = sample_booking.location_name
        completed.location_notes = sample_booking.location_notes
        completed.client_notes = sample_booking.client_notes
        completed.host_notes = None
        completed.cancellation_reason = None
        completed.cancelled_by_id = None
        completed.cancelled_at = None
        completed.stripe_payment_intent_id = sample_booking.stripe_payment_intent_id
        completed.stripe_transfer_id = "tr_test123"
        completed.created_at = sample_booking.created_at
        completed.updated_at = datetime.now(UTC)
        completed.client = sample_booking.client
        completed.host = sample_booking.host
        completed.host_profile = sample_booking.host_profile
        completed.dance_style = sample_booking.dance_style
        return completed

    @pytest.mark.asyncio
    async def test_complete_booking_endpoint_exists(
        self,
        mock_db,
        sample_host_user,
        in_progress_booking,
        completed_booking,
    ):
        """Test that the complete booking endpoint exists and returns 200."""
        with (
            patch("app.routers.bookings.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.routers.bookings.BookingRepository") as mock_booking_repo_cls,
            patch("app.routers.bookings.HostProfileRepository") as mock_host_repo_cls,
            patch("app.routers.bookings.stripe_service") as mock_stripe,
            patch("app.routers.bookings.get_settings") as mock_settings,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_host_user.id), token_type="access"
            )

            with patch("app.core.deps.UserRepository") as mock_user_repo_cls:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_id.return_value = sample_host_user
                mock_user_repo_cls.return_value = mock_user_repo

                mock_settings_obj = MagicMock()
                mock_settings_obj.stripe_secret_key = "sk_test_123"
                mock_settings.return_value = mock_settings_obj

                mock_host_repo = AsyncMock()
                mock_host_profile = MagicMock()
                mock_host_profile.stripe_account_id = "acct_test123"
                mock_host_repo.get_by_id.return_value = mock_host_profile
                mock_host_repo_cls.return_value = mock_host_repo

                mock_booking_repo = AsyncMock()
                mock_booking_repo.get_by_id.side_effect = [
                    in_progress_booking,
                    completed_booking,
                ]
                mock_booking_repo.update_status.return_value = completed_booking
                mock_booking_repo_cls.return_value = mock_booking_repo

                mock_stripe.capture_payment_intent = AsyncMock(return_value=True)
                mock_stripe.create_transfer = AsyncMock(return_value="tr_test123")

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        f"/api/v1/bookings/{in_progress_booking.id}/complete",
                        headers=get_auth_header(sample_host_user.id),
                    )

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_complete_booking_validates_in_progress_status(
        self,
        mock_db,
        sample_host_user,
        sample_booking,
    ):
        """Test that completing requires IN_PROGRESS status."""
        sample_booking.status = BookingStatus.CONFIRMED  # Not in_progress

        with (
            patch("app.routers.bookings.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.routers.bookings.BookingRepository") as mock_booking_repo_cls,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_host_user.id), token_type="access"
            )

            with patch("app.core.deps.UserRepository") as mock_user_repo_cls:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_id.return_value = sample_host_user
                mock_user_repo_cls.return_value = mock_user_repo

                mock_booking_repo = AsyncMock()
                mock_booking_repo.get_by_id.return_value = sample_booking
                mock_booking_repo_cls.return_value = mock_booking_repo

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        f"/api/v1/bookings/{sample_booking.id}/complete",
                        headers=get_auth_header(sample_host_user.id),
                    )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "in_progress" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_complete_booking_captures_payment_intent(
        self,
        mock_db,
        sample_host_user,
        in_progress_booking,
        completed_booking,
    ):
        """Test that completing captures the Stripe PaymentIntent."""
        capture_calls = []

        with (
            patch("app.routers.bookings.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.routers.bookings.BookingRepository") as mock_booking_repo_cls,
            patch("app.routers.bookings.HostProfileRepository") as mock_host_repo_cls,
            patch("app.routers.bookings.stripe_service") as mock_stripe,
            patch("app.routers.bookings.get_settings") as mock_settings,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_host_user.id), token_type="access"
            )

            with patch("app.core.deps.UserRepository") as mock_user_repo_cls:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_id.return_value = sample_host_user
                mock_user_repo_cls.return_value = mock_user_repo

                mock_settings_obj = MagicMock()
                mock_settings_obj.stripe_secret_key = "sk_test_123"
                mock_settings.return_value = mock_settings_obj

                mock_host_repo = AsyncMock()
                mock_host_profile = MagicMock()
                mock_host_profile.stripe_account_id = "acct_test123"
                mock_host_repo.get_by_id.return_value = mock_host_profile
                mock_host_repo_cls.return_value = mock_host_repo

                mock_booking_repo = AsyncMock()
                mock_booking_repo.get_by_id.side_effect = [
                    in_progress_booking,
                    completed_booking,
                ]
                mock_booking_repo.update_status.return_value = completed_booking
                mock_booking_repo_cls.return_value = mock_booking_repo

                async def capture_payment(*args, **kwargs):
                    capture_calls.append((args, kwargs))
                    return True

                mock_stripe.capture_payment_intent = capture_payment
                mock_stripe.create_transfer = AsyncMock(return_value="tr_test123")

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        f"/api/v1/bookings/{in_progress_booking.id}/complete",
                        headers=get_auth_header(sample_host_user.id),
                    )

        assert response.status_code == status.HTTP_200_OK
        # Verify capture_payment_intent was called
        assert len(capture_calls) == 1
        assert in_progress_booking.stripe_payment_intent_id in capture_calls[0][0]

    @pytest.mark.asyncio
    async def test_complete_booking_creates_transfer(
        self,
        mock_db,
        sample_host_user,
        in_progress_booking,
        completed_booking,
    ):
        """Test that completing creates a transfer to host's connected account."""
        transfer_calls = []

        with (
            patch("app.routers.bookings.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.routers.bookings.BookingRepository") as mock_booking_repo_cls,
            patch("app.routers.bookings.HostProfileRepository") as mock_host_repo_cls,
            patch("app.routers.bookings.stripe_service") as mock_stripe,
            patch("app.routers.bookings.get_settings") as mock_settings,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_host_user.id), token_type="access"
            )

            with patch("app.core.deps.UserRepository") as mock_user_repo_cls:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_id.return_value = sample_host_user
                mock_user_repo_cls.return_value = mock_user_repo

                mock_settings_obj = MagicMock()
                mock_settings_obj.stripe_secret_key = "sk_test_123"
                mock_settings.return_value = mock_settings_obj

                mock_host_repo = AsyncMock()
                mock_host_profile = MagicMock()
                mock_host_profile.stripe_account_id = "acct_test123"
                mock_host_repo.get_by_id.return_value = mock_host_profile
                mock_host_repo_cls.return_value = mock_host_repo

                mock_booking_repo = AsyncMock()
                mock_booking_repo.get_by_id.side_effect = [
                    in_progress_booking,
                    completed_booking,
                ]
                mock_booking_repo.update_status.return_value = completed_booking
                mock_booking_repo_cls.return_value = mock_booking_repo

                mock_stripe.capture_payment_intent = AsyncMock(return_value=True)

                async def create_transfer(*args, **kwargs):
                    transfer_calls.append((args, kwargs))
                    return "tr_test123"

                mock_stripe.create_transfer = create_transfer

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        f"/api/v1/bookings/{in_progress_booking.id}/complete",
                        headers=get_auth_header(sample_host_user.id),
                    )

        assert response.status_code == status.HTTP_200_OK
        # Verify create_transfer was called with correct host payout
        assert len(transfer_calls) == 1
        args, kwargs = transfer_calls[0]
        assert kwargs.get("amount_cents") == in_progress_booking.host_payout_cents
        assert kwargs.get("destination_account_id") == "acct_test123"

    @pytest.mark.asyncio
    async def test_complete_booking_only_host_can_complete(
        self,
        mock_db,
        sample_user,  # Client, not host
        in_progress_booking,
    ):
        """Test that only the host can complete the booking."""
        with (
            patch("app.routers.bookings.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.routers.bookings.BookingRepository") as mock_booking_repo_cls,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_user.id), token_type="access"
            )

            with patch("app.core.deps.UserRepository") as mock_user_repo_cls:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_id.return_value = sample_user
                mock_user_repo_cls.return_value = mock_user_repo

                mock_booking_repo = AsyncMock()
                mock_booking_repo.get_by_id.return_value = in_progress_booking
                mock_booking_repo_cls.return_value = mock_booking_repo

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        f"/api/v1/bookings/{in_progress_booking.id}/complete",
                        headers=get_auth_header(sample_user.id),
                    )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Only the host can complete" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_complete_booking_not_found_returns_404(
        self,
        mock_db,
        sample_host_user,
    ):
        """Test that completing a non-existent booking returns 404."""
        non_existent_id = uuid4()

        with (
            patch("app.routers.bookings.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.routers.bookings.BookingRepository") as mock_booking_repo_cls,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_host_user.id), token_type="access"
            )

            with patch("app.core.deps.UserRepository") as mock_user_repo_cls:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_id.return_value = sample_host_user
                mock_user_repo_cls.return_value = mock_user_repo

                mock_booking_repo = AsyncMock()
                mock_booking_repo.get_by_id.return_value = None
                mock_booking_repo_cls.return_value = mock_booking_repo

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        f"/api/v1/bookings/{non_existent_id}/complete",
                        headers=get_auth_header(sample_host_user.id),
                    )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_complete_booking_requires_authentication(self):
        """Test that completing a booking requires authentication."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                f"/api/v1/bookings/{uuid4()}/complete",
                # No auth header
            )

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    @pytest.mark.asyncio
    async def test_complete_booking_updates_status_to_completed(
        self,
        mock_db,
        sample_host_user,
        in_progress_booking,
        completed_booking,
    ):
        """Test that completing updates booking status to COMPLETED."""
        update_calls = []

        with (
            patch("app.routers.bookings.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.routers.bookings.BookingRepository") as mock_booking_repo_cls,
            patch("app.routers.bookings.HostProfileRepository") as mock_host_repo_cls,
            patch("app.routers.bookings.stripe_service") as mock_stripe,
            patch("app.routers.bookings.get_settings") as mock_settings,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_host_user.id), token_type="access"
            )

            with patch("app.core.deps.UserRepository") as mock_user_repo_cls:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_id.return_value = sample_host_user
                mock_user_repo_cls.return_value = mock_user_repo

                mock_settings_obj = MagicMock()
                mock_settings_obj.stripe_secret_key = "sk_test_123"
                mock_settings.return_value = mock_settings_obj

                mock_host_repo = AsyncMock()
                mock_host_profile = MagicMock()
                mock_host_profile.stripe_account_id = "acct_test123"
                mock_host_repo.get_by_id.return_value = mock_host_profile
                mock_host_repo_cls.return_value = mock_host_repo

                mock_booking_repo = AsyncMock()
                mock_booking_repo.get_by_id.side_effect = [
                    in_progress_booking,
                    completed_booking,
                ]

                async def mock_update_status(booking_id, new_status, **kwargs):
                    update_calls.append((booking_id, new_status, kwargs))
                    return completed_booking

                mock_booking_repo.update_status = mock_update_status
                mock_booking_repo_cls.return_value = mock_booking_repo

                mock_stripe.capture_payment_intent = AsyncMock(return_value=True)
                mock_stripe.create_transfer = AsyncMock(return_value="tr_test123")

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        f"/api/v1/bookings/{in_progress_booking.id}/complete",
                        headers=get_auth_header(sample_host_user.id),
                    )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == BookingStatus.COMPLETED.value

        # Verify update_status was called with COMPLETED status
        assert len(update_calls) == 1
        _, new_status, _ = update_calls[0]
        assert new_status == BookingStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_complete_booking_pending_status_returns_400(
        self,
        mock_db,
        sample_host_user,
        sample_booking,
    ):
        """Test that completing a PENDING booking returns 400."""
        sample_booking.status = BookingStatus.PENDING

        with (
            patch("app.routers.bookings.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.routers.bookings.BookingRepository") as mock_booking_repo_cls,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_host_user.id), token_type="access"
            )

            with patch("app.core.deps.UserRepository") as mock_user_repo_cls:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_id.return_value = sample_host_user
                mock_user_repo_cls.return_value = mock_user_repo

                mock_booking_repo = AsyncMock()
                mock_booking_repo.get_by_id.return_value = sample_booking
                mock_booking_repo_cls.return_value = mock_booking_repo

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        f"/api/v1/bookings/{sample_booking.id}/complete",
                        headers=get_auth_header(sample_host_user.id),
                    )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_complete_booking_cancelled_status_returns_400(
        self,
        mock_db,
        sample_host_user,
        sample_booking,
    ):
        """Test that completing a CANCELLED booking returns 400."""
        sample_booking.status = BookingStatus.CANCELLED

        with (
            patch("app.routers.bookings.get_db", return_value=mock_db),
            patch("app.core.deps.get_db", return_value=mock_db),
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.routers.bookings.BookingRepository") as mock_booking_repo_cls,
        ):
            mock_token_service.verify_token.return_value = MagicMock(
                sub=str(sample_host_user.id), token_type="access"
            )

            with patch("app.core.deps.UserRepository") as mock_user_repo_cls:
                mock_user_repo = AsyncMock()
                mock_user_repo.get_by_id.return_value = sample_host_user
                mock_user_repo_cls.return_value = mock_user_repo

                mock_booking_repo = AsyncMock()
                mock_booking_repo.get_by_id.return_value = sample_booking
                mock_booking_repo_cls.return_value = mock_booking_repo

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        f"/api/v1/bookings/{sample_booking.id}/complete",
                        headers=get_auth_header(sample_host_user.id),
                    )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
