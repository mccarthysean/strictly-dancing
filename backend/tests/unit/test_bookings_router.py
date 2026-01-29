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
