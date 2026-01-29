"""Fixtures for integration tests.

These fixtures provide real application instances with mocked database
sessions, enabling full API testing with proper request/response cycles.
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.core.deps import get_current_user
from app.main import create_app
from app.models.booking import Booking, BookingStatus
from app.models.dance_style import DanceStyle, DanceStyleCategory
from app.models.host_profile import HostProfile, VerificationStatus
from app.models.user import User, UserType
from app.services.token import token_service


@pytest.fixture
def integration_app():
    """Create a FastAPI application for integration testing."""
    return create_app()


@pytest.fixture
def integration_client(integration_app) -> TestClient:
    """Create a test client for integration testing."""
    return TestClient(integration_app)


def make_mock_user(
    user_id: str | None = None,
    email: str = "test@example.com",
    first_name: str = "Test",
    last_name: str = "User",
    user_type: UserType = UserType.CLIENT,
    is_active: bool = True,
    email_verified: bool = False,
    password_hash: str = "$argon2id$v=19$m=65536,t=3,p=4$hash",
) -> MagicMock:
    """Create a mock User object with specified attributes."""
    mock_user = MagicMock(spec=User)
    mock_user.id = user_id or str(uuid.uuid4())
    mock_user.email = email
    mock_user.first_name = first_name
    mock_user.last_name = last_name
    mock_user.user_type = user_type
    mock_user.is_active = is_active
    mock_user.email_verified = email_verified
    mock_user.password_hash = password_hash
    mock_user.created_at = datetime.now(UTC)
    mock_user.updated_at = datetime.now(UTC)
    return mock_user


def make_mock_host_profile(
    profile_id: str | None = None,
    user_id: str | None = None,
    bio: str = "Test host bio",
    headline: str = "Professional Dance Instructor",
    hourly_rate_cents: int = 5000,
    rating_average: float = 4.5,
    total_reviews: int = 10,
    total_sessions: int = 25,
    verification_status: VerificationStatus = VerificationStatus.VERIFIED,
    stripe_account_id: str | None = "acct_test123",
    stripe_onboarding_complete: bool = True,
    latitude: float | None = 40.7128,
    longitude: float | None = -74.0060,
) -> MagicMock:
    """Create a mock HostProfile object with specified attributes."""
    mock_profile = MagicMock(spec=HostProfile)
    mock_profile.id = profile_id or str(uuid.uuid4())
    mock_profile.user_id = user_id or str(uuid.uuid4())
    mock_profile.bio = bio
    mock_profile.headline = headline
    mock_profile.hourly_rate_cents = hourly_rate_cents
    mock_profile.rating_average = rating_average
    mock_profile.total_reviews = total_reviews
    mock_profile.total_sessions = total_sessions
    mock_profile.verification_status = verification_status
    mock_profile.stripe_account_id = stripe_account_id
    mock_profile.stripe_onboarding_complete = stripe_onboarding_complete
    mock_profile.created_at = datetime.now(UTC)
    mock_profile.updated_at = datetime.now(UTC)

    # Location handling
    if latitude is not None and longitude is not None:
        mock_location = MagicMock()
        mock_location.x = longitude
        mock_location.y = latitude
        mock_profile.location = mock_location
    else:
        mock_profile.location = None

    # Initialize dance styles as empty list by default
    mock_profile.dance_styles = []

    return mock_profile


def make_mock_dance_style(
    style_id: str | None = None,
    name: str = "Salsa",
    slug: str = "salsa",
    category: DanceStyleCategory = DanceStyleCategory.LATIN,
    description: str = "A popular Latin dance",
) -> MagicMock:
    """Create a mock DanceStyle object."""
    mock_style = MagicMock(spec=DanceStyle)
    mock_style.id = style_id or str(uuid.uuid4())
    mock_style.name = name
    mock_style.slug = slug
    mock_style.category = category
    mock_style.description = description
    mock_style.created_at = datetime.now(UTC)
    mock_style.updated_at = datetime.now(UTC)
    return mock_style


def make_mock_booking(
    booking_id: str | None = None,
    client_id: str | None = None,
    host_id: str | None = None,
    host_profile_id: str | None = None,
    dance_style_id: str | None = None,
    status: BookingStatus = BookingStatus.PENDING,
    scheduled_start: datetime | None = None,
    scheduled_end: datetime | None = None,
    duration_minutes: int = 60,
    hourly_rate_cents: int = 5000,
    amount_cents: int = 5000,
    platform_fee_cents: int = 750,
    host_payout_cents: int = 4250,
    stripe_payment_intent_id: str | None = "pi_test123",
) -> MagicMock:
    """Create a mock Booking object."""
    mock_booking = MagicMock(spec=Booking)
    mock_booking.id = booking_id or str(uuid.uuid4())
    mock_booking.client_id = client_id or str(uuid.uuid4())
    mock_booking.host_id = host_id or str(uuid.uuid4())
    mock_booking.host_profile_id = host_profile_id or str(uuid.uuid4())
    mock_booking.dance_style_id = dance_style_id or str(uuid.uuid4())
    mock_booking.status = status
    mock_booking.scheduled_start = scheduled_start or datetime.now(UTC)
    mock_booking.scheduled_end = scheduled_end or datetime.now(UTC)
    mock_booking.duration_minutes = duration_minutes
    mock_booking.hourly_rate_cents = hourly_rate_cents
    mock_booking.amount_cents = amount_cents
    mock_booking.platform_fee_cents = platform_fee_cents
    mock_booking.host_payout_cents = host_payout_cents
    mock_booking.stripe_payment_intent_id = stripe_payment_intent_id
    mock_booking.stripe_transfer_id = None
    mock_booking.location = None
    mock_booking.location_name = None
    mock_booking.location_notes = None
    mock_booking.client_notes = None
    mock_booking.host_notes = None
    mock_booking.actual_start = None
    mock_booking.actual_end = None
    mock_booking.cancellation_reason = None
    mock_booking.cancelled_by_id = None
    mock_booking.cancelled_at = None
    mock_booking.created_at = datetime.now(UTC)
    mock_booking.updated_at = datetime.now(UTC)
    return mock_booking


@pytest.fixture
def mock_user() -> MagicMock:
    """Provide a basic mock user."""
    return make_mock_user()


@pytest.fixture
def mock_host_user() -> MagicMock:
    """Provide a mock user with HOST type."""
    return make_mock_user(
        user_type=UserType.HOST,
        email="host@example.com",
        first_name="Host",
        last_name="User",
    )


@pytest.fixture
def mock_client_user() -> MagicMock:
    """Provide a mock user with CLIENT type."""
    return make_mock_user(
        user_type=UserType.CLIENT,
        email="client@example.com",
        first_name="Client",
        last_name="User",
    )


@pytest.fixture
def auth_headers(mock_user: MagicMock) -> dict[str, str]:
    """Generate valid authentication headers for a mock user."""
    access_token = token_service.create_access_token(str(mock_user.id))
    return {"Authorization": f"Bearer {access_token}"}


def create_authenticated_client(
    app,
    user: MagicMock,
) -> TestClient:
    """Create a test client with dependency override for authentication.

    This allows testing authenticated endpoints without going through
    the full token verification flow.
    """
    app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)
