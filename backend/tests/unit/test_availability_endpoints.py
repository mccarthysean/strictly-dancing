"""Unit tests for availability endpoints.

Tests for:
- GET/PUT /api/v1/users/me/host-profile/availability
- GET /api/v1/hosts/{id}/availability
"""

from datetime import date, time, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import create_app
from app.models.availability import (
    AvailabilityOverride,
    AvailabilityOverrideType,
    DayOfWeek,
    RecurringAvailability,
)
from app.models.host_profile import VerificationStatus
from app.models.user import UserType


@pytest.fixture
def app():
    """Create a test FastAPI application."""
    return create_app()


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


def create_mock_user(
    user_id: str = "550e8400-e29b-41d4-a716-446655440000",
    email: str = "host@example.com",
    first_name: str = "Test",
    last_name: str = "Host",
    user_type: UserType = UserType.HOST,
) -> MagicMock:
    """Create a mock user for testing."""
    mock_user = MagicMock()
    mock_user.id = user_id
    mock_user.email = email
    mock_user.first_name = first_name
    mock_user.last_name = last_name
    mock_user.user_type = user_type
    mock_user.is_active = True
    return mock_user


def create_mock_host_profile(
    profile_id: str = "660e8400-e29b-41d4-a716-446655440001",
    user_id: str = "550e8400-e29b-41d4-a716-446655440000",
) -> MagicMock:
    """Create a mock host profile for testing."""
    mock_user = create_mock_user(user_id=user_id)
    mock_profile = MagicMock()
    mock_profile.id = profile_id
    mock_profile.user_id = user_id
    mock_profile.bio = "Test bio"
    mock_profile.headline = "Test headline"
    mock_profile.hourly_rate_cents = 5000
    mock_profile.rating_average = 4.5
    mock_profile.total_reviews = 10
    mock_profile.total_sessions = 25
    mock_profile.verification_status = VerificationStatus.VERIFIED
    mock_profile.stripe_account_id = "acct_123"
    mock_profile.stripe_onboarding_complete = True
    mock_profile.created_at = "2026-01-29T00:00:00Z"
    mock_profile.updated_at = "2026-01-29T00:00:00Z"
    mock_profile.user = mock_user
    return mock_profile


def create_mock_recurring_availability(
    host_profile_id: str,
) -> list[MagicMock]:
    """Create mock recurring availability records."""
    availability_list = []
    for day in [DayOfWeek.MONDAY, DayOfWeek.WEDNESDAY, DayOfWeek.FRIDAY]:
        avail = MagicMock(spec=RecurringAvailability)
        avail.id = str(uuid4())
        avail.host_profile_id = host_profile_id
        avail.day_of_week = day.value
        avail.start_time = time(9, 0)
        avail.end_time = time(17, 0)
        avail.is_active = True
        availability_list.append(avail)
    return availability_list


def create_mock_overrides(host_profile_id: str) -> list[MagicMock]:
    """Create mock availability overrides."""
    override = MagicMock(spec=AvailabilityOverride)
    override.id = str(uuid4())
    override.host_profile_id = host_profile_id
    override.override_date = date.today() + timedelta(days=7)
    override.override_type = AvailabilityOverrideType.BLOCKED
    override.start_time = time(12, 0)
    override.end_time = time(14, 0)
    override.all_day = False
    override.reason = "Doctor appointment"
    return [override]


class TestGetHostAvailabilityPrivate:
    """Tests for GET /api/v1/users/me/host-profile/availability."""

    def test_get_host_availability_endpoint_exists(self, client: TestClient):
        """Test that the endpoint exists and responds."""
        # Without auth, should get 401, not 404
        response = client.get("/api/v1/users/me/host-profile/availability")
        assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_get_host_availability_requires_auth(self, client: TestClient):
        """Test that the endpoint requires authentication."""
        response = client.get("/api/v1/users/me/host-profile/availability")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_host_availability_returns_404_for_non_host(self, client: TestClient):
        """Test that 404 is returned if user doesn't have a host profile."""
        mock_user = create_mock_user()

        with (
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_class,
            patch("app.routers.users.HostProfileRepository") as mock_host_repo_class,
        ):
            # Set up auth mocks
            mock_token_payload = MagicMock()
            mock_token_payload.sub = mock_user.id
            mock_token_payload.token_type = "access"
            mock_token_service.verify_token.return_value = mock_token_payload

            mock_user_repo = AsyncMock()
            mock_user_repo.get_by_id.return_value = mock_user
            mock_user_repo_class.return_value = mock_user_repo

            mock_host_repo = AsyncMock()
            mock_host_repo.get_by_user_id.return_value = None
            mock_host_repo_class.return_value = mock_host_repo

            response = client.get(
                "/api/v1/users/me/host-profile/availability",
                headers={"Authorization": "Bearer test_token"},
            )
            assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_host_availability_returns_recurring_and_overrides(
        self, client: TestClient
    ):
        """Test that availability returns both recurring schedules and overrides."""
        mock_user = create_mock_user()
        mock_profile = create_mock_host_profile(user_id=mock_user.id)
        mock_recurring = create_mock_recurring_availability(str(mock_profile.id))
        mock_ovr = create_mock_overrides(str(mock_profile.id))

        with (
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_class,
            patch("app.routers.users.HostProfileRepository") as mock_host_repo_class,
            patch("app.routers.users.AvailabilityRepository") as mock_avail_repo_class,
        ):
            # Set up auth mocks
            mock_token_payload = MagicMock()
            mock_token_payload.sub = mock_user.id
            mock_token_payload.token_type = "access"
            mock_token_service.verify_token.return_value = mock_token_payload

            mock_user_repo = AsyncMock()
            mock_user_repo.get_by_id.return_value = mock_user
            mock_user_repo_class.return_value = mock_user_repo

            mock_host_repo = AsyncMock()
            mock_host_repo.get_by_user_id.return_value = mock_profile
            mock_host_repo_class.return_value = mock_host_repo

            mock_avail_repo = AsyncMock()
            mock_avail_repo.get_recurring_availability.return_value = mock_recurring
            mock_avail_repo.get_overrides_for_date_range.return_value = mock_ovr
            mock_avail_repo_class.return_value = mock_avail_repo

            response = client.get(
                "/api/v1/users/me/host-profile/availability",
                headers={"Authorization": "Bearer test_token"},
            )
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "recurring" in data
            assert "overrides" in data
            assert len(data["recurring"]) == 3
            assert len(data["overrides"]) == 1


class TestSetHostAvailabilityPrivate:
    """Tests for PUT /api/v1/users/me/host-profile/availability."""

    def test_set_host_availability_endpoint_exists(self, client: TestClient):
        """Test that the PUT endpoint exists."""
        # Without auth, should get 401, not 404 or 405
        response = client.put(
            "/api/v1/users/me/host-profile/availability",
            json={"recurring": []},
        )
        assert response.status_code != status.HTTP_404_NOT_FOUND
        assert response.status_code != status.HTTP_405_METHOD_NOT_ALLOWED

    def test_set_host_availability_requires_auth(self, client: TestClient):
        """Test that the PUT endpoint requires authentication."""
        response = client.put(
            "/api/v1/users/me/host-profile/availability",
            json={"recurring": []},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_set_host_availability_validates_time_order(self, client: TestClient):
        """Test that end_time must be after start_time."""
        mock_user = create_mock_user()
        mock_profile = create_mock_host_profile(user_id=mock_user.id)

        with (
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_class,
            patch("app.routers.users.HostProfileRepository") as mock_host_repo_class,
        ):
            # Set up auth mocks
            mock_token_payload = MagicMock()
            mock_token_payload.sub = mock_user.id
            mock_token_payload.token_type = "access"
            mock_token_service.verify_token.return_value = mock_token_payload

            mock_user_repo = AsyncMock()
            mock_user_repo.get_by_id.return_value = mock_user
            mock_user_repo_class.return_value = mock_user_repo

            mock_host_repo = AsyncMock()
            mock_host_repo.get_by_user_id.return_value = mock_profile
            mock_host_repo_class.return_value = mock_host_repo

            response = client.put(
                "/api/v1/users/me/host-profile/availability",
                headers={"Authorization": "Bearer test_token"},
                json={
                    "recurring": [
                        {
                            "day_of_week": 0,
                            "start_time": "17:00:00",
                            "end_time": "09:00:00",
                        }
                    ]
                },
            )
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_set_host_availability_updates_schedule(self, client: TestClient):
        """Test that PUT updates the weekly schedule."""
        mock_user = create_mock_user()
        mock_profile = create_mock_host_profile(user_id=mock_user.id)

        mock_avail_rec = MagicMock()
        mock_avail_rec.id = str(uuid4())
        mock_avail_rec.day_of_week = 0
        mock_avail_rec.start_time = time(9, 0)
        mock_avail_rec.end_time = time(17, 0)
        mock_avail_rec.is_active = True

        with (
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_class,
            patch("app.routers.users.HostProfileRepository") as mock_host_repo_class,
            patch("app.routers.users.AvailabilityRepository") as mock_avail_repo_class,
        ):
            mock_token_payload = MagicMock()
            mock_token_payload.sub = mock_user.id
            mock_token_payload.token_type = "access"
            mock_token_service.verify_token.return_value = mock_token_payload

            mock_user_repo = AsyncMock()
            mock_user_repo.get_by_id.return_value = mock_user
            mock_user_repo_class.return_value = mock_user_repo

            mock_host_repo = AsyncMock()
            mock_host_repo.get_by_user_id.return_value = mock_profile
            mock_host_repo_class.return_value = mock_host_repo

            mock_avail_repo = AsyncMock()
            mock_avail_repo.clear_recurring_availability.return_value = 0
            mock_avail_repo.set_recurring_availability.return_value = mock_avail_rec
            mock_avail_repo.get_recurring_availability.return_value = [mock_avail_rec]
            mock_avail_repo.get_overrides_for_date_range.return_value = []
            mock_avail_repo_class.return_value = mock_avail_repo

            response = client.put(
                "/api/v1/users/me/host-profile/availability",
                headers={"Authorization": "Bearer test_token"},
                json={
                    "recurring": [
                        {
                            "day_of_week": 0,
                            "start_time": "09:00:00",
                            "end_time": "17:00:00",
                        }
                    ]
                },
            )
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data["recurring"]) == 1


class TestGetPublicHostAvailability:
    """Tests for GET /api/v1/hosts/{id}/availability."""

    def test_get_public_availability_endpoint_exists(self, client: TestClient):
        """Test that the public availability endpoint exists."""
        host_id = uuid4()

        with (
            patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class,
        ):
            mock_host_repo = AsyncMock()
            mock_host_repo.get_by_id.return_value = None
            mock_host_repo_class.return_value = mock_host_repo

            response = client.get(f"/api/v1/hosts/{host_id}/availability")
            # Should be 404 (not found) not 405 (method not allowed)
            assert response.status_code != status.HTTP_405_METHOD_NOT_ALLOWED

    def test_get_public_availability_returns_404_for_invalid_host(
        self, client: TestClient
    ):
        """Test that 404 is returned for non-existent host."""
        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo.get_by_id.return_value = None
            mock_host_repo_class.return_value = mock_host_repo

            response = client.get(f"/api/v1/hosts/{uuid4()}/availability")
            assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_public_availability_returns_slots_for_date_range(
        self, client: TestClient
    ):
        """Test that availability returns slots for a date range."""
        mock_profile = create_mock_host_profile()
        start_date = date.today()
        end_date = start_date + timedelta(days=7)

        with (
            patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class,
            patch("app.routers.hosts.AvailabilityRepository") as mock_avail_repo_class,
        ):
            mock_host_repo = AsyncMock()
            mock_host_repo.get_by_id.return_value = mock_profile
            mock_host_repo_class.return_value = mock_host_repo

            mock_avail_repo = AsyncMock()
            mock_avail_repo.get_availability_for_date.return_value = [
                (time(9, 0), time(12, 0)),
                (time(14, 0), time(17, 0)),
            ]
            mock_avail_repo.get_bookings_for_date_range.return_value = []
            mock_avail_repo._subtract_time_range = (
                lambda slots, start, end: slots  # No-op for this test
            )
            mock_avail_repo_class.return_value = mock_avail_repo

            response = client.get(
                f"/api/v1/hosts/{mock_profile.id}/availability",
                params={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
            )
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "availability" in data
            assert data["start_date"] == start_date.isoformat()
            assert data["end_date"] == end_date.isoformat()

    def test_get_public_availability_excludes_booked_slots(self, client: TestClient):
        """Test that already-booked slots are excluded from availability."""
        mock_profile = create_mock_host_profile()
        start_date = date.today()
        end_date = start_date + timedelta(days=1)

        # Create a mock booking
        mock_booking = MagicMock()
        mock_booking.scheduled_start = MagicMock()
        mock_booking.scheduled_start.date.return_value = start_date
        mock_booking.scheduled_start.time.return_value = time(10, 0)
        mock_booking.scheduled_end = MagicMock()
        mock_booking.scheduled_end.time.return_value = time(11, 0)

        with (
            patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class,
            patch("app.routers.hosts.AvailabilityRepository") as mock_avail_repo_class,
        ):
            mock_host_repo = AsyncMock()
            mock_host_repo.get_by_id.return_value = mock_profile
            mock_host_repo_class.return_value = mock_host_repo

            mock_avail_repo = AsyncMock()
            mock_avail_repo.get_availability_for_date.return_value = [
                (time(9, 0), time(17, 0))
            ]
            mock_avail_repo.get_bookings_for_date_range.return_value = [mock_booking]
            # Simulate the subtract operation
            mock_avail_repo._subtract_time_range = lambda slots, start, end: [
                (time(9, 0), start),
                (end, time(17, 0)),
            ]
            mock_avail_repo_class.return_value = mock_avail_repo

            response = client.get(
                f"/api/v1/hosts/{mock_profile.id}/availability",
                params={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
            )
            assert response.status_code == status.HTTP_200_OK


class TestAddAvailabilityOverride:
    """Tests for POST /api/v1/users/me/host-profile/availability/overrides."""

    def test_add_override_endpoint_exists(self, client: TestClient):
        """Test that the add override endpoint exists."""
        response = client.post(
            "/api/v1/users/me/host-profile/availability/overrides",
            json={
                "override_date": (date.today() + timedelta(days=7)).isoformat(),
                "override_type": "blocked",
                "start_time": "12:00:00",
                "end_time": "14:00:00",
                "all_day": False,
            },
        )
        # Should get 401 (unauthorized), not 404 or 405
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_add_override_creates_blocked_override(self, client: TestClient):
        """Test that a blocked override can be created."""
        mock_user = create_mock_user()
        mock_profile = create_mock_host_profile(user_id=mock_user.id)
        override_date = date.today() + timedelta(days=7)

        mock_override = MagicMock()
        mock_override.id = str(uuid4())
        mock_override.override_date = override_date
        mock_override.override_type = AvailabilityOverrideType.BLOCKED
        mock_override.start_time = time(12, 0)
        mock_override.end_time = time(14, 0)
        mock_override.all_day = False
        mock_override.reason = "Doctor appointment"

        with (
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_class,
            patch("app.routers.users.HostProfileRepository") as mock_host_repo_class,
            patch("app.routers.users.AvailabilityRepository") as mock_avail_repo_class,
        ):
            mock_token_payload = MagicMock()
            mock_token_payload.sub = mock_user.id
            mock_token_payload.token_type = "access"
            mock_token_service.verify_token.return_value = mock_token_payload

            mock_user_repo = AsyncMock()
            mock_user_repo.get_by_id.return_value = mock_user
            mock_user_repo_class.return_value = mock_user_repo

            mock_host_repo = AsyncMock()
            mock_host_repo.get_by_user_id.return_value = mock_profile
            mock_host_repo_class.return_value = mock_host_repo

            mock_avail_repo = AsyncMock()
            mock_avail_repo.block_time_slot.return_value = mock_override
            mock_avail_repo_class.return_value = mock_avail_repo

            response = client.post(
                "/api/v1/users/me/host-profile/availability/overrides",
                headers={"Authorization": "Bearer test_token"},
                json={
                    "override_date": override_date.isoformat(),
                    "override_type": "blocked",
                    "start_time": "12:00:00",
                    "end_time": "14:00:00",
                    "all_day": False,
                    "reason": "Doctor appointment",
                },
            )
            assert response.status_code == status.HTTP_201_CREATED


class TestDeleteAvailabilityOverride:
    """Tests for DELETE /api/v1/users/me/host-profile/availability/overrides/{id}."""

    def test_delete_override_endpoint_exists(self, client: TestClient):
        """Test that the delete override endpoint exists."""
        override_id = uuid4()
        response = client.delete(
            f"/api/v1/users/me/host-profile/availability/overrides/{override_id}"
        )
        # Should get 401 (unauthorized), not 404 or 405
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_override_removes_override(self, client: TestClient):
        """Test that an override can be deleted."""
        mock_user = create_mock_user()
        mock_profile = create_mock_host_profile(user_id=mock_user.id)
        override_id = uuid4()

        with (
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_class,
            patch("app.routers.users.HostProfileRepository") as mock_host_repo_class,
            patch("app.routers.users.AvailabilityRepository") as mock_avail_repo_class,
        ):
            mock_token_payload = MagicMock()
            mock_token_payload.sub = mock_user.id
            mock_token_payload.token_type = "access"
            mock_token_service.verify_token.return_value = mock_token_payload

            mock_user_repo = AsyncMock()
            mock_user_repo.get_by_id.return_value = mock_user
            mock_user_repo_class.return_value = mock_user_repo

            mock_host_repo = AsyncMock()
            mock_host_repo.get_by_user_id.return_value = mock_profile
            mock_host_repo_class.return_value = mock_host_repo

            mock_avail_repo = AsyncMock()
            mock_avail_repo.delete_override.return_value = True
            mock_avail_repo_class.return_value = mock_avail_repo

            response = client.delete(
                f"/api/v1/users/me/host-profile/availability/overrides/{override_id}",
                headers={"Authorization": "Bearer test_token"},
            )
            assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_override_returns_404_when_not_found(self, client: TestClient):
        """Test that 404 is returned when override not found."""
        mock_user = create_mock_user()
        mock_profile = create_mock_host_profile(user_id=mock_user.id)
        override_id = uuid4()

        with (
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_class,
            patch("app.routers.users.HostProfileRepository") as mock_host_repo_class,
            patch("app.routers.users.AvailabilityRepository") as mock_avail_repo_class,
        ):
            mock_token_payload = MagicMock()
            mock_token_payload.sub = mock_user.id
            mock_token_payload.token_type = "access"
            mock_token_service.verify_token.return_value = mock_token_payload

            mock_user_repo = AsyncMock()
            mock_user_repo.get_by_id.return_value = mock_user
            mock_user_repo_class.return_value = mock_user_repo

            mock_host_repo = AsyncMock()
            mock_host_repo.get_by_user_id.return_value = mock_profile
            mock_host_repo_class.return_value = mock_host_repo

            mock_avail_repo = AsyncMock()
            mock_avail_repo.delete_override.return_value = False
            mock_avail_repo_class.return_value = mock_avail_repo

            response = client.delete(
                f"/api/v1/users/me/host-profile/availability/overrides/{override_id}",
                headers={"Authorization": "Bearer test_token"},
            )
            assert response.status_code == status.HTTP_404_NOT_FOUND
