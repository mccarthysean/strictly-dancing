"""Integration tests for booking flow.

Tests the complete booking lifecycle:
- Creating a booking
- Host confirming booking
- Starting a session
- Completing a session (with payment capture)
- Cancelling a booking

These tests use mocked repositories and services to simulate database
and Stripe interactions while testing the full API endpoint behavior.
"""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import create_app
from app.models.booking import BookingStatus
from app.models.user import UserType

from .conftest import (
    create_authenticated_client,
    make_mock_booking,
    make_mock_dance_style,
    make_mock_host_profile,
    make_mock_user,
)


class TestBookingFlowE2E:
    """End-to-end tests for complete booking flow."""

    @pytest.fixture
    def app(self):
        """Create a fresh app for each test."""
        return create_app()

    @pytest.fixture
    def client_user(self) -> MagicMock:
        """Create a mock client user."""
        return make_mock_user(
            user_id=str(uuid.uuid4()),
            email="client@example.com",
            first_name="Client",
            last_name="User",
            user_type=UserType.CLIENT,
        )

    @pytest.fixture
    def host_user(self) -> MagicMock:
        """Create a mock host user."""
        return make_mock_user(
            user_id=str(uuid.uuid4()),
            email="host@example.com",
            first_name="Host",
            last_name="User",
            user_type=UserType.HOST,
        )

    @pytest.fixture
    def host_profile(self, host_user) -> MagicMock:
        """Create a mock host profile."""
        return make_mock_host_profile(
            profile_id=str(uuid.uuid4()),
            user_id=host_user.id,
            hourly_rate_cents=6000,  # $60/hour
            stripe_account_id="acct_test_host",
            stripe_onboarding_complete=True,
        )

    @pytest.fixture
    def dance_style(self) -> MagicMock:
        """Create a mock dance style."""
        return make_mock_dance_style(
            style_id=str(uuid.uuid4()),
            name="Salsa",
            slug="salsa",
        )

    def test_complete_booking_flow_create_confirm_complete(
        self,
        app,
        client_user: MagicMock,
        host_user: MagicMock,
        host_profile: MagicMock,
        dance_style: MagicMock,
    ) -> None:
        """Test complete flow: create -> confirm -> complete.

        Note: The API goes directly from CONFIRMED to COMPLETED status.
        The IN_PROGRESS state is set internally during completion.
        """
        booking_id = str(uuid.uuid4())
        scheduled_start = datetime.now(UTC) + timedelta(days=1)
        scheduled_end = scheduled_start + timedelta(hours=1)

        # Step 1: Client creates a booking
        with (
            patch("app.routers.bookings.HostProfileRepository") as mock_hp_repo_class,
            patch("app.routers.bookings.AvailabilityRepository") as mock_av_repo_class,
            patch("app.routers.bookings.BookingRepository") as mock_bk_repo_class,
            patch("app.routers.bookings.stripe_service") as mock_stripe,
        ):
            mock_hp_repo = AsyncMock()
            mock_av_repo = AsyncMock()
            mock_bk_repo = AsyncMock()
            mock_hp_repo_class.return_value = mock_hp_repo
            mock_av_repo_class.return_value = mock_av_repo
            mock_bk_repo_class.return_value = mock_bk_repo

            # Setup mocks for booking creation
            host_profile.user = host_user
            mock_hp_repo.get_by_id.return_value = host_profile
            mock_hp_repo.get_dance_style_by_id.return_value = dance_style
            mock_av_repo.is_available_for_slot.return_value = True

            # Mock stripe payment intent
            mock_payment_intent = MagicMock()
            mock_payment_intent.id = "pi_test_123"
            mock_payment_intent.client_secret = "pi_secret_123"
            mock_stripe.create_payment_intent.return_value = mock_payment_intent

            # Mock created booking
            created_booking = make_mock_booking(
                booking_id=booking_id,
                client_id=client_user.id,
                host_id=host_user.id,
                host_profile_id=host_profile.id,
                dance_style_id=dance_style.id,
                status=BookingStatus.PENDING,
                scheduled_start=scheduled_start,
                scheduled_end=scheduled_end,
                duration_minutes=60,
                hourly_rate_cents=6000,
                amount_cents=6000,
                platform_fee_cents=900,
                host_payout_cents=5100,
                stripe_payment_intent_id="pi_test_123",
            )
            created_booking.client = client_user
            created_booking.host = host_user
            created_booking.host_profile = host_profile
            created_booking.dance_style = dance_style
            mock_bk_repo.create.return_value = created_booking
            mock_bk_repo.get_by_id.return_value = created_booking

            # Create authenticated client and make booking
            client_app = create_authenticated_client(app, client_user)
            create_response = client_app.post(
                "/api/v1/bookings",
                json={
                    "host_id": host_profile.id,
                    "dance_style_id": dance_style.id,
                    "scheduled_start": scheduled_start.isoformat(),
                    "duration_minutes": 60,
                },
            )

            assert create_response.status_code == status.HTTP_201_CREATED
            create_data = create_response.json()
            assert create_data["status"] == "pending"
            assert create_data["amount_cents"] == 6000

        # Step 2: Host confirms the booking
        with (
            patch("app.routers.bookings.BookingRepository") as mock_bk_repo_class,
        ):
            mock_bk_repo = AsyncMock()
            mock_bk_repo_class.return_value = mock_bk_repo

            # Setup booking for confirmation
            pending_booking = make_mock_booking(
                booking_id=booking_id,
                client_id=client_user.id,
                host_id=host_user.id,
                status=BookingStatus.PENDING,
            )
            pending_booking.client = client_user
            pending_booking.host = host_user
            pending_booking.host_profile = host_profile
            pending_booking.dance_style = dance_style

            confirmed_booking = make_mock_booking(
                booking_id=booking_id,
                client_id=client_user.id,
                host_id=host_user.id,
                status=BookingStatus.CONFIRMED,
            )
            confirmed_booking.client = client_user
            confirmed_booking.host = host_user
            confirmed_booking.host_profile = host_profile
            confirmed_booking.dance_style = dance_style

            mock_bk_repo.get_by_id.side_effect = [pending_booking, confirmed_booking]
            mock_bk_repo.update_status.return_value = confirmed_booking

            # Host confirms
            host_app = create_authenticated_client(app, host_user)
            confirm_response = host_app.post(f"/api/v1/bookings/{booking_id}/confirm")

            assert confirm_response.status_code == status.HTTP_200_OK
            confirm_data = confirm_response.json()
            assert confirm_data["status"] == "confirmed"

        # Step 3: Host completes the session
        # Note: The complete endpoint expects IN_PROGRESS status
        # In a real scenario, there would be a separate flow to transition
        # from CONFIRMED to IN_PROGRESS. For this test, we mock it directly.
        with (
            patch("app.routers.bookings.BookingRepository") as mock_bk_repo_class,
            patch("app.routers.bookings.stripe_service") as mock_stripe,
            patch("app.routers.bookings.HostProfileRepository") as mock_hp_repo_class,
        ):
            mock_bk_repo = AsyncMock()
            mock_hp_repo = AsyncMock()
            mock_bk_repo_class.return_value = mock_bk_repo
            mock_hp_repo_class.return_value = mock_hp_repo

            # Setup booking for completion - in_progress status
            in_progress_booking = make_mock_booking(
                booking_id=booking_id,
                client_id=client_user.id,
                host_id=host_user.id,
                host_profile_id=host_profile.id,
                status=BookingStatus.IN_PROGRESS,
                stripe_payment_intent_id="pi_test_123",
                host_payout_cents=5100,
            )
            in_progress_booking.client = client_user
            in_progress_booking.host = host_user
            in_progress_booking.host_profile = host_profile
            in_progress_booking.dance_style = dance_style

            completed_booking = make_mock_booking(
                booking_id=booking_id,
                client_id=client_user.id,
                host_id=host_user.id,
                status=BookingStatus.COMPLETED,
            )
            completed_booking.stripe_transfer_id = "tr_test_123"
            completed_booking.actual_end = datetime.now(UTC)
            completed_booking.client = client_user
            completed_booking.host = host_user
            completed_booking.host_profile = host_profile
            completed_booking.dance_style = dance_style

            mock_bk_repo.get_by_id.side_effect = [
                in_progress_booking,
                completed_booking,
            ]
            mock_bk_repo.update_status.return_value = completed_booking

            # Mock Stripe capture and transfer
            mock_capture = MagicMock()
            mock_capture.id = "pi_test_123"
            mock_stripe.capture_payment_intent.return_value = mock_capture

            mock_transfer = MagicMock()
            mock_transfer.id = "tr_test_123"
            mock_stripe.create_transfer.return_value = mock_transfer

            mock_hp_repo.get_by_id.return_value = host_profile

            complete_response = host_app.post(f"/api/v1/bookings/{booking_id}/complete")

            assert complete_response.status_code == status.HTTP_200_OK
            complete_data = complete_response.json()
            assert complete_data["status"] == "completed"


class TestBookingCreationIntegration:
    """Integration tests for booking creation endpoint."""

    @pytest.fixture
    def app(self):
        """Create a fresh app for each test."""
        return create_app()

    @pytest.fixture
    def client_user(self) -> MagicMock:
        """Create a mock client user."""
        return make_mock_user(
            user_id=str(uuid.uuid4()),
            email="client@example.com",
            user_type=UserType.CLIENT,
        )

    @pytest.fixture
    def host_user(self) -> MagicMock:
        """Create a mock host user."""
        return make_mock_user(
            user_id=str(uuid.uuid4()),
            email="host@example.com",
            user_type=UserType.HOST,
        )

    @pytest.fixture
    def host_profile(self, host_user) -> MagicMock:
        """Create a mock host profile."""
        profile = make_mock_host_profile(
            profile_id=str(uuid.uuid4()),
            user_id=host_user.id,
            hourly_rate_cents=5000,
            stripe_account_id="acct_test",
        )
        profile.user = host_user
        return profile

    @pytest.fixture
    def dance_style(self) -> MagicMock:
        """Create a mock dance style."""
        return make_mock_dance_style(style_id=str(uuid.uuid4()))

    def test_create_booking_success(
        self,
        app,
        client_user: MagicMock,
        host_user: MagicMock,
        host_profile: MagicMock,
        dance_style: MagicMock,
    ) -> None:
        """Test successful booking creation."""
        booking_id = str(uuid.uuid4())
        scheduled_start = datetime.now(UTC) + timedelta(days=1)

        with (
            patch("app.routers.bookings.HostProfileRepository") as mock_hp_repo_class,
            patch("app.routers.bookings.AvailabilityRepository") as mock_av_repo_class,
            patch("app.routers.bookings.BookingRepository") as mock_bk_repo_class,
            patch("app.routers.bookings.stripe_service") as mock_stripe,
        ):
            mock_hp_repo = AsyncMock()
            mock_av_repo = AsyncMock()
            mock_bk_repo = AsyncMock()
            mock_hp_repo_class.return_value = mock_hp_repo
            mock_av_repo_class.return_value = mock_av_repo
            mock_bk_repo_class.return_value = mock_bk_repo

            mock_hp_repo.get_by_id.return_value = host_profile
            mock_hp_repo.get_dance_style_by_id.return_value = dance_style
            mock_av_repo.is_available_for_slot.return_value = True

            mock_payment_intent = MagicMock()
            mock_payment_intent.id = "pi_test_123"
            mock_payment_intent.client_secret = "pi_secret_123"
            mock_stripe.create_payment_intent.return_value = mock_payment_intent

            created_booking = make_mock_booking(
                booking_id=booking_id,
                client_id=client_user.id,
                host_id=host_user.id,
                host_profile_id=host_profile.id,
                dance_style_id=dance_style.id,
                status=BookingStatus.PENDING,
                amount_cents=5000,
                platform_fee_cents=750,
                host_payout_cents=4250,
            )
            created_booking.client = client_user
            created_booking.host = host_user
            created_booking.host_profile = host_profile
            created_booking.dance_style = dance_style
            mock_bk_repo.create.return_value = created_booking
            mock_bk_repo.get_by_id.return_value = created_booking

            client_app = create_authenticated_client(app, client_user)
            response = client_app.post(
                "/api/v1/bookings",
                json={
                    "host_id": host_profile.id,
                    "dance_style_id": dance_style.id,
                    "scheduled_start": scheduled_start.isoformat(),
                    "duration_minutes": 60,
                },
            )

            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["status"] == "pending"
            assert data["amount_cents"] == 5000

    def test_create_booking_unavailable_slot_returns_409(
        self,
        app,
        client_user: MagicMock,
        host_profile: MagicMock,
        dance_style: MagicMock,
    ) -> None:
        """Test that unavailable time slot returns 409."""
        scheduled_start = datetime.now(UTC) + timedelta(days=1)

        with (
            patch("app.routers.bookings.HostProfileRepository") as mock_hp_repo_class,
            patch("app.routers.bookings.AvailabilityRepository") as mock_av_repo_class,
            patch("app.routers.bookings.BookingRepository") as mock_bk_repo_class,
        ):
            mock_hp_repo = AsyncMock()
            mock_av_repo = AsyncMock()
            mock_bk_repo = AsyncMock()
            mock_hp_repo_class.return_value = mock_hp_repo
            mock_av_repo_class.return_value = mock_av_repo
            mock_bk_repo_class.return_value = mock_bk_repo

            mock_hp_repo.get_by_id.return_value = host_profile
            mock_hp_repo.get_dance_style_by_id.return_value = dance_style
            mock_av_repo.is_available_for_slot.return_value = False  # Not available

            client_app = create_authenticated_client(app, client_user)
            response = client_app.post(
                "/api/v1/bookings",
                json={
                    "host_id": host_profile.id,
                    "dance_style_id": dance_style.id,
                    "scheduled_start": scheduled_start.isoformat(),
                    "duration_minutes": 60,
                },
            )

            assert response.status_code == status.HTTP_409_CONFLICT

    def test_create_booking_requires_authentication(self, app) -> None:
        """Test that booking creation requires authentication."""
        client = TestClient(app)
        response = client.post(
            "/api/v1/bookings",
            json={
                "host_id": "some-id",
                "dance_style_id": "some-id",
                "scheduled_start": datetime.now(UTC).isoformat(),
                "duration_minutes": 60,
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestBookingConfirmationIntegration:
    """Integration tests for booking confirmation endpoint."""

    @pytest.fixture
    def app(self):
        """Create a fresh app for each test."""
        return create_app()

    @pytest.fixture
    def client_user(self) -> MagicMock:
        """Create a mock client user."""
        return make_mock_user(
            user_id=str(uuid.uuid4()),
            user_type=UserType.CLIENT,
        )

    @pytest.fixture
    def host_user(self) -> MagicMock:
        """Create a mock host user."""
        return make_mock_user(
            user_id=str(uuid.uuid4()),
            user_type=UserType.HOST,
        )

    def test_confirm_booking_by_host_succeeds(
        self,
        app,
        client_user: MagicMock,
        host_user: MagicMock,
    ) -> None:
        """Test that host can confirm their booking."""
        booking_id = str(uuid.uuid4())

        with patch("app.routers.bookings.BookingRepository") as mock_bk_repo_class:
            mock_bk_repo = AsyncMock()
            mock_bk_repo_class.return_value = mock_bk_repo

            host_profile = make_mock_host_profile(user_id=host_user.id)
            dance_style = make_mock_dance_style()

            pending_booking = make_mock_booking(
                booking_id=booking_id,
                client_id=client_user.id,
                host_id=host_user.id,
                status=BookingStatus.PENDING,
            )
            pending_booking.client = client_user
            pending_booking.host = host_user
            pending_booking.host_profile = host_profile
            pending_booking.dance_style = dance_style

            confirmed_booking = make_mock_booking(
                booking_id=booking_id,
                client_id=client_user.id,
                host_id=host_user.id,
                status=BookingStatus.CONFIRMED,
            )
            confirmed_booking.client = client_user
            confirmed_booking.host = host_user
            confirmed_booking.host_profile = host_profile
            confirmed_booking.dance_style = dance_style

            mock_bk_repo.get_by_id.side_effect = [pending_booking, confirmed_booking]
            mock_bk_repo.update_status.return_value = confirmed_booking

            host_app = create_authenticated_client(app, host_user)
            response = host_app.post(f"/api/v1/bookings/{booking_id}/confirm")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "confirmed"

    def test_confirm_booking_by_client_returns_403(
        self,
        app,
        client_user: MagicMock,
        host_user: MagicMock,
    ) -> None:
        """Test that client cannot confirm booking."""
        booking_id = str(uuid.uuid4())

        with patch("app.routers.bookings.BookingRepository") as mock_bk_repo_class:
            mock_bk_repo = AsyncMock()
            mock_bk_repo_class.return_value = mock_bk_repo

            pending_booking = make_mock_booking(
                booking_id=booking_id,
                client_id=client_user.id,
                host_id=host_user.id,
                status=BookingStatus.PENDING,
            )
            mock_bk_repo.get_by_id.return_value = pending_booking

            client_app = create_authenticated_client(app, client_user)
            response = client_app.post(f"/api/v1/bookings/{booking_id}/confirm")

            assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_confirm_booking_not_pending_returns_400(
        self,
        app,
        host_user: MagicMock,
    ) -> None:
        """Test that confirming non-pending booking returns 400."""
        booking_id = str(uuid.uuid4())

        with patch("app.routers.bookings.BookingRepository") as mock_bk_repo_class:
            mock_bk_repo = AsyncMock()
            mock_bk_repo_class.return_value = mock_bk_repo

            confirmed_booking = make_mock_booking(
                booking_id=booking_id,
                host_id=host_user.id,
                status=BookingStatus.CONFIRMED,  # Already confirmed
            )
            mock_bk_repo.get_by_id.return_value = confirmed_booking

            host_app = create_authenticated_client(app, host_user)
            response = host_app.post(f"/api/v1/bookings/{booking_id}/confirm")

            assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestBookingCancellationIntegration:
    """Integration tests for booking cancellation endpoint."""

    @pytest.fixture
    def app(self):
        """Create a fresh app for each test."""
        return create_app()

    @pytest.fixture
    def client_user(self) -> MagicMock:
        """Create a mock client user."""
        return make_mock_user(
            user_id=str(uuid.uuid4()),
            user_type=UserType.CLIENT,
        )

    @pytest.fixture
    def host_user(self) -> MagicMock:
        """Create a mock host user."""
        return make_mock_user(
            user_id=str(uuid.uuid4()),
            user_type=UserType.HOST,
        )

    def test_cancel_booking_by_client_succeeds(
        self,
        app,
        client_user: MagicMock,
        host_user: MagicMock,
    ) -> None:
        """Test that client can cancel their booking."""
        booking_id = str(uuid.uuid4())

        with (
            patch("app.routers.bookings.BookingRepository") as mock_bk_repo_class,
            patch("app.routers.bookings.stripe_service") as mock_stripe,
        ):
            mock_bk_repo = AsyncMock()
            mock_bk_repo_class.return_value = mock_bk_repo

            host_profile = make_mock_host_profile(user_id=host_user.id)
            dance_style = make_mock_dance_style()

            pending_booking = make_mock_booking(
                booking_id=booking_id,
                client_id=client_user.id,
                host_id=host_user.id,
                status=BookingStatus.PENDING,
                stripe_payment_intent_id="pi_test_123",
            )
            pending_booking.client = client_user
            pending_booking.host = host_user
            pending_booking.host_profile = host_profile
            pending_booking.dance_style = dance_style

            cancelled_booking = make_mock_booking(
                booking_id=booking_id,
                client_id=client_user.id,
                host_id=host_user.id,
                status=BookingStatus.CANCELLED,
            )
            cancelled_booking.client = client_user
            cancelled_booking.host = host_user
            cancelled_booking.host_profile = host_profile
            cancelled_booking.dance_style = dance_style
            cancelled_booking.cancelled_by_id = client_user.id
            cancelled_booking.cancellation_reason = "Changed my mind"

            mock_bk_repo.get_by_id.side_effect = [pending_booking, cancelled_booking]
            mock_bk_repo.update_status.return_value = cancelled_booking

            mock_cancelled_pi = MagicMock()
            mock_stripe.cancel_payment_intent.return_value = mock_cancelled_pi

            client_app = create_authenticated_client(app, client_user)
            response = client_app.post(
                f"/api/v1/bookings/{booking_id}/cancel",
                json={"reason": "Changed my mind"},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "cancelled"

    def test_cancel_booking_by_host_succeeds(
        self,
        app,
        client_user: MagicMock,
        host_user: MagicMock,
    ) -> None:
        """Test that host can cancel booking."""
        booking_id = str(uuid.uuid4())

        with (
            patch("app.routers.bookings.BookingRepository") as mock_bk_repo_class,
            patch("app.routers.bookings.stripe_service"),
        ):
            mock_bk_repo = AsyncMock()
            mock_bk_repo_class.return_value = mock_bk_repo

            host_profile = make_mock_host_profile(user_id=host_user.id)
            dance_style = make_mock_dance_style()

            confirmed_booking = make_mock_booking(
                booking_id=booking_id,
                client_id=client_user.id,
                host_id=host_user.id,
                status=BookingStatus.CONFIRMED,
            )
            confirmed_booking.client = client_user
            confirmed_booking.host = host_user
            confirmed_booking.host_profile = host_profile
            confirmed_booking.dance_style = dance_style

            cancelled_booking = make_mock_booking(
                booking_id=booking_id,
                client_id=client_user.id,
                host_id=host_user.id,
                status=BookingStatus.CANCELLED,
            )
            cancelled_booking.client = client_user
            cancelled_booking.host = host_user
            cancelled_booking.host_profile = host_profile
            cancelled_booking.dance_style = dance_style

            mock_bk_repo.get_by_id.side_effect = [confirmed_booking, cancelled_booking]
            mock_bk_repo.update_status.return_value = cancelled_booking

            host_app = create_authenticated_client(app, host_user)
            response = host_app.post(f"/api/v1/bookings/{booking_id}/cancel")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "cancelled"

    def test_cancel_completed_booking_returns_400(
        self,
        app,
        client_user: MagicMock,
    ) -> None:
        """Test that cancelling completed booking returns 400."""
        booking_id = str(uuid.uuid4())

        with patch("app.routers.bookings.BookingRepository") as mock_bk_repo_class:
            mock_bk_repo = AsyncMock()
            mock_bk_repo_class.return_value = mock_bk_repo

            completed_booking = make_mock_booking(
                booking_id=booking_id,
                client_id=client_user.id,
                status=BookingStatus.COMPLETED,
            )
            mock_bk_repo.get_by_id.return_value = completed_booking

            client_app = create_authenticated_client(app, client_user)
            response = client_app.post(f"/api/v1/bookings/{booking_id}/cancel")

            assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestBookingCompletionIntegration:
    """Integration tests for booking completion endpoint."""

    @pytest.fixture
    def app(self):
        """Create a fresh app for each test."""
        return create_app()

    @pytest.fixture
    def host_user(self) -> MagicMock:
        """Create a mock host user."""
        return make_mock_user(
            user_id=str(uuid.uuid4()),
            user_type=UserType.HOST,
        )

    @pytest.fixture
    def client_user(self) -> MagicMock:
        """Create a mock client user."""
        return make_mock_user(
            user_id=str(uuid.uuid4()),
            user_type=UserType.CLIENT,
        )

    def test_complete_booking_by_host_succeeds(
        self,
        app,
        host_user: MagicMock,
        client_user: MagicMock,
    ) -> None:
        """Test that host can complete in_progress booking."""
        booking_id = str(uuid.uuid4())

        with (
            patch("app.routers.bookings.BookingRepository") as mock_bk_repo_class,
            patch("app.routers.bookings.stripe_service") as mock_stripe,
            patch("app.routers.bookings.HostProfileRepository") as mock_hp_repo_class,
        ):
            mock_bk_repo = AsyncMock()
            mock_hp_repo = AsyncMock()
            mock_bk_repo_class.return_value = mock_bk_repo
            mock_hp_repo_class.return_value = mock_hp_repo

            host_profile = make_mock_host_profile(
                user_id=host_user.id,
                stripe_account_id="acct_test",
            )
            dance_style = make_mock_dance_style()

            in_progress_booking = make_mock_booking(
                booking_id=booking_id,
                client_id=client_user.id,
                host_id=host_user.id,
                host_profile_id=host_profile.id,
                status=BookingStatus.IN_PROGRESS,
                stripe_payment_intent_id="pi_test_123",
                host_payout_cents=4250,
            )
            in_progress_booking.client = client_user
            in_progress_booking.host = host_user
            in_progress_booking.host_profile = host_profile
            in_progress_booking.dance_style = dance_style

            completed_booking = make_mock_booking(
                booking_id=booking_id,
                client_id=client_user.id,
                host_id=host_user.id,
                status=BookingStatus.COMPLETED,
            )
            completed_booking.stripe_transfer_id = "tr_test_123"
            completed_booking.client = client_user
            completed_booking.host = host_user
            completed_booking.host_profile = host_profile
            completed_booking.dance_style = dance_style

            mock_bk_repo.get_by_id.side_effect = [
                in_progress_booking,
                completed_booking,
            ]
            mock_bk_repo.update_status.return_value = completed_booking

            mock_capture = MagicMock()
            mock_capture.id = "pi_test_123"
            mock_stripe.capture_payment_intent.return_value = mock_capture

            mock_transfer = MagicMock()
            mock_transfer.id = "tr_test_123"
            mock_stripe.create_transfer.return_value = mock_transfer

            mock_hp_repo.get_by_id.return_value = host_profile

            host_app = create_authenticated_client(app, host_user)
            response = host_app.post(f"/api/v1/bookings/{booking_id}/complete")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "completed"
            # stripe_transfer_id is not exposed in BookingResponse schema

    def test_complete_booking_not_in_progress_returns_400(
        self,
        app,
        host_user: MagicMock,
    ) -> None:
        """Test that completing non-in_progress booking returns 400."""
        booking_id = str(uuid.uuid4())

        with patch("app.routers.bookings.BookingRepository") as mock_bk_repo_class:
            mock_bk_repo = AsyncMock()
            mock_bk_repo_class.return_value = mock_bk_repo

            confirmed_booking = make_mock_booking(
                booking_id=booking_id,
                host_id=host_user.id,
                status=BookingStatus.CONFIRMED,  # Not in_progress
            )
            mock_bk_repo.get_by_id.return_value = confirmed_booking

            host_app = create_authenticated_client(app, host_user)
            response = host_app.post(f"/api/v1/bookings/{booking_id}/complete")

            assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_complete_booking_by_client_returns_403(
        self,
        app,
        host_user: MagicMock,
        client_user: MagicMock,
    ) -> None:
        """Test that client cannot complete booking."""
        booking_id = str(uuid.uuid4())

        with patch("app.routers.bookings.BookingRepository") as mock_bk_repo_class:
            mock_bk_repo = AsyncMock()
            mock_bk_repo_class.return_value = mock_bk_repo

            in_progress_booking = make_mock_booking(
                booking_id=booking_id,
                client_id=client_user.id,
                host_id=host_user.id,
                status=BookingStatus.IN_PROGRESS,
            )
            mock_bk_repo.get_by_id.return_value = in_progress_booking

            client_app = create_authenticated_client(app, client_user)
            response = client_app.post(f"/api/v1/bookings/{booking_id}/complete")

            assert response.status_code == status.HTTP_403_FORBIDDEN


class TestBookingListIntegration:
    """Integration tests for booking list endpoint."""

    @pytest.fixture
    def app(self):
        """Create a fresh app for each test."""
        return create_app()

    @pytest.fixture
    def user(self) -> MagicMock:
        """Create a mock user."""
        return make_mock_user(user_id=str(uuid.uuid4()))

    def test_list_bookings_returns_user_bookings(self, app, user: MagicMock) -> None:
        """Test that list returns user's bookings."""
        with patch("app.routers.bookings.BookingRepository") as mock_bk_repo_class:
            mock_bk_repo = AsyncMock()
            mock_bk_repo_class.return_value = mock_bk_repo

            host_profile = make_mock_host_profile()
            dance_style = make_mock_dance_style()

            booking1 = make_mock_booking(
                client_id=user.id,
                status=BookingStatus.PENDING,
            )
            booking1.client = user
            booking1.host = make_mock_user()
            booking1.host_profile = host_profile
            booking1.dance_style = dance_style

            booking2 = make_mock_booking(
                client_id=user.id,
                status=BookingStatus.COMPLETED,
            )
            booking2.client = user
            booking2.host = make_mock_user()
            booking2.host_profile = host_profile
            booking2.dance_style = dance_style

            mock_bk_repo.get_for_user_with_cursor.return_value = [booking1, booking2]

            client_app = create_authenticated_client(app, user)
            response = client_app.get("/api/v1/bookings")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "items" in data
            assert len(data["items"]) == 2

    def test_list_bookings_filter_by_status(self, app, user: MagicMock) -> None:
        """Test that list can filter by status."""
        with patch("app.routers.bookings.BookingRepository") as mock_bk_repo_class:
            mock_bk_repo = AsyncMock()
            mock_bk_repo_class.return_value = mock_bk_repo

            host_profile = make_mock_host_profile()
            dance_style = make_mock_dance_style()

            pending_booking = make_mock_booking(
                client_id=user.id,
                status=BookingStatus.PENDING,
            )
            pending_booking.client = user
            pending_booking.host = make_mock_user()
            pending_booking.host_profile = host_profile
            pending_booking.dance_style = dance_style

            mock_bk_repo.get_for_user_with_cursor.return_value = [pending_booking]

            client_app = create_authenticated_client(app, user)
            response = client_app.get("/api/v1/bookings?status=pending")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data["items"]) == 1
            assert data["items"][0]["status"] == "pending"

    def test_list_bookings_requires_authentication(self, app) -> None:
        """Test that list requires authentication."""
        client = TestClient(app)
        response = client.get("/api/v1/bookings")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
