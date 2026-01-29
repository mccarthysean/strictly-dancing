"""Unit tests for users router endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import create_app
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
    email: str = "test@example.com",
    first_name: str = "Test",
    last_name: str = "User",
    user_type: UserType = UserType.CLIENT,
) -> MagicMock:
    """Create a mock user for testing."""
    mock_user = MagicMock()
    mock_user.id = user_id
    mock_user.email = email
    mock_user.first_name = first_name
    mock_user.last_name = last_name
    mock_user.user_type = user_type
    mock_user.email_verified = False
    mock_user.is_active = True
    mock_user.created_at = "2026-01-29T00:00:00Z"
    mock_user.updated_at = "2026-01-29T00:00:00Z"
    return mock_user


def create_mock_host_profile(
    profile_id: str = "660e8400-e29b-41d4-a716-446655440001",
    user_id: str = "550e8400-e29b-41d4-a716-446655440000",
) -> MagicMock:
    """Create a mock host profile for testing."""
    mock_profile = MagicMock()
    mock_profile.id = profile_id
    mock_profile.user_id = user_id
    mock_profile.bio = None
    mock_profile.headline = None
    mock_profile.hourly_rate_cents = 5000
    mock_profile.rating_average = None
    mock_profile.total_reviews = 0
    mock_profile.total_sessions = 0
    mock_profile.verification_status = VerificationStatus.UNVERIFIED
    mock_profile.location = None
    mock_profile.stripe_account_id = None
    mock_profile.stripe_onboarding_complete = False
    mock_profile.created_at = "2026-01-29T00:00:00Z"
    mock_profile.updated_at = "2026-01-29T00:00:00Z"
    mock_profile.host_dance_styles = []
    return mock_profile


class TestBecomeHostEndpoint:
    """Tests for POST /api/v1/users/me/become-host endpoint."""

    def test_become_host_endpoint_exists(self, client: TestClient) -> None:
        """Test that the become-host endpoint exists and accepts POST."""
        # Without auth, should get 401, not 404
        response = client.post("/api/v1/users/me/become-host")
        assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_become_host_requires_authentication(self, client: TestClient) -> None:
        """Test that become-host requires authentication."""
        response = client.post("/api/v1/users/me/become-host")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_become_host_creates_profile_returns_201(self, client: TestClient) -> None:
        """Test that successful become-host returns 201 Created."""
        mock_user = create_mock_user(user_type=UserType.CLIENT)
        mock_profile = create_mock_host_profile(user_id=mock_user.id)

        with (
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_class,
            patch("app.routers.users.HostProfileRepository") as mock_host_repo_class,
            patch("app.routers.users.UserRepository") as mock_users_repo_class,
        ):
            # Set up auth mocks
            mock_token_payload = MagicMock()
            mock_token_payload.sub = mock_user.id
            mock_token_payload.token_type = "access"
            mock_token_service.verify_token.return_value = mock_token_payload

            mock_user_repo = AsyncMock()
            mock_user_repo_class.return_value = mock_user_repo
            mock_user_repo.get_by_id.return_value = mock_user

            # Set up host profile repo mocks
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_user_id.return_value = None  # No existing profile
            mock_host_repo.create.return_value = mock_profile
            mock_host_repo.get_dance_styles.return_value = []

            # Set up user repo mock for update
            mock_users_repo = AsyncMock()
            mock_users_repo_class.return_value = mock_users_repo

            response = client.post(
                "/api/v1/users/me/become-host",
                headers={"Authorization": "Bearer valid_token"},
                json={},
            )
            assert response.status_code == status.HTTP_201_CREATED

    def test_become_host_creates_host_profile_linked_to_user(
        self, client: TestClient
    ) -> None:
        """Test that become-host creates a HostProfile linked to the current user."""
        mock_user = create_mock_user(user_type=UserType.CLIENT)
        mock_profile = create_mock_host_profile(user_id=mock_user.id)

        with (
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_class,
            patch("app.routers.users.HostProfileRepository") as mock_host_repo_class,
            patch("app.routers.users.UserRepository") as mock_users_repo_class,
        ):
            # Set up auth mocks
            mock_token_payload = MagicMock()
            mock_token_payload.sub = mock_user.id
            mock_token_payload.token_type = "access"
            mock_token_service.verify_token.return_value = mock_token_payload

            mock_user_repo = AsyncMock()
            mock_user_repo_class.return_value = mock_user_repo
            mock_user_repo.get_by_id.return_value = mock_user

            # Set up host profile repo mocks
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_user_id.return_value = None
            mock_host_repo.create.return_value = mock_profile
            mock_host_repo.get_dance_styles.return_value = []

            # Set up user repo mock for update
            mock_users_repo = AsyncMock()
            mock_users_repo_class.return_value = mock_users_repo

            response = client.post(
                "/api/v1/users/me/become-host",
                headers={"Authorization": "Bearer valid_token"},
                json={},
            )

            assert response.status_code == status.HTTP_201_CREATED
            # Verify profile was created with user ID
            mock_host_repo.create.assert_called_once()
            call_kwargs = mock_host_repo.create.call_args
            assert str(call_kwargs.kwargs["user_id"]) == mock_user.id

    def test_become_host_updates_user_type_to_host(self, client: TestClient) -> None:
        """Test that become-host updates user_type to include host."""
        mock_user = create_mock_user(user_type=UserType.CLIENT)
        mock_profile = create_mock_host_profile(user_id=mock_user.id)

        with (
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_class,
            patch("app.routers.users.HostProfileRepository") as mock_host_repo_class,
            patch("app.routers.users.UserRepository") as mock_users_repo_class,
        ):
            # Set up auth mocks
            mock_token_payload = MagicMock()
            mock_token_payload.sub = mock_user.id
            mock_token_payload.token_type = "access"
            mock_token_service.verify_token.return_value = mock_token_payload

            mock_user_repo = AsyncMock()
            mock_user_repo_class.return_value = mock_user_repo
            mock_user_repo.get_by_id.return_value = mock_user

            # Set up host profile repo mocks
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_user_id.return_value = None
            mock_host_repo.create.return_value = mock_profile
            mock_host_repo.get_dance_styles.return_value = []

            # Set up user repo mock for update
            mock_users_repo = AsyncMock()
            mock_users_repo_class.return_value = mock_users_repo

            response = client.post(
                "/api/v1/users/me/become-host",
                headers={"Authorization": "Bearer valid_token"},
                json={},
            )

            assert response.status_code == status.HTTP_201_CREATED
            # Verify user type was updated
            mock_users_repo.update_user_type.assert_called_once()

    def test_become_host_already_host_returns_409(self, client: TestClient) -> None:
        """Test that become-host returns 409 if user is already a host."""
        mock_user = create_mock_user(user_type=UserType.HOST)
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
            mock_user_repo_class.return_value = mock_user_repo
            mock_user_repo.get_by_id.return_value = mock_user

            # Set up host profile repo - profile already exists
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_user_id.return_value = mock_profile

            response = client.post(
                "/api/v1/users/me/become-host",
                headers={"Authorization": "Bearer valid_token"},
                json={},
            )

            assert response.status_code == status.HTTP_409_CONFLICT
            assert "already a host" in response.json()["detail"].lower()

    def test_become_host_with_profile_data(self, client: TestClient) -> None:
        """Test that become-host accepts optional profile data."""
        mock_user = create_mock_user(user_type=UserType.CLIENT)
        mock_profile = create_mock_host_profile(user_id=mock_user.id)
        mock_profile.bio = "Experienced dancer"
        mock_profile.headline = "Professional Salsa Instructor"
        mock_profile.hourly_rate_cents = 7500

        with (
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_class,
            patch("app.routers.users.HostProfileRepository") as mock_host_repo_class,
            patch("app.routers.users.UserRepository") as mock_users_repo_class,
        ):
            # Set up auth mocks
            mock_token_payload = MagicMock()
            mock_token_payload.sub = mock_user.id
            mock_token_payload.token_type = "access"
            mock_token_service.verify_token.return_value = mock_token_payload

            mock_user_repo = AsyncMock()
            mock_user_repo_class.return_value = mock_user_repo
            mock_user_repo.get_by_id.return_value = mock_user

            # Set up host profile repo mocks
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_user_id.return_value = None
            mock_host_repo.create.return_value = mock_profile
            mock_host_repo.get_dance_styles.return_value = []

            # Set up user repo mock for update
            mock_users_repo = AsyncMock()
            mock_users_repo_class.return_value = mock_users_repo

            response = client.post(
                "/api/v1/users/me/become-host",
                headers={"Authorization": "Bearer valid_token"},
                json={
                    "bio": "Experienced dancer",
                    "headline": "Professional Salsa Instructor",
                    "hourly_rate_cents": 7500,
                },
            )

            assert response.status_code == status.HTTP_201_CREATED
            # Verify profile data was passed
            mock_host_repo.create.assert_called_once()
            call_kwargs = mock_host_repo.create.call_args.kwargs
            assert call_kwargs["bio"] == "Experienced dancer"
            assert call_kwargs["headline"] == "Professional Salsa Instructor"
            assert call_kwargs["hourly_rate_cents"] == 7500

    def test_become_host_returns_host_profile_response(
        self, client: TestClient
    ) -> None:
        """Test that become-host returns the created host profile."""
        mock_user = create_mock_user(user_type=UserType.CLIENT)
        mock_profile = create_mock_host_profile(user_id=mock_user.id)

        with (
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_class,
            patch("app.routers.users.HostProfileRepository") as mock_host_repo_class,
            patch("app.routers.users.UserRepository") as mock_users_repo_class,
        ):
            # Set up auth mocks
            mock_token_payload = MagicMock()
            mock_token_payload.sub = mock_user.id
            mock_token_payload.token_type = "access"
            mock_token_service.verify_token.return_value = mock_token_payload

            mock_user_repo = AsyncMock()
            mock_user_repo_class.return_value = mock_user_repo
            mock_user_repo.get_by_id.return_value = mock_user

            # Set up host profile repo mocks
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_user_id.return_value = None
            mock_host_repo.create.return_value = mock_profile
            mock_host_repo.get_dance_styles.return_value = []

            # Set up user repo mock for update
            mock_users_repo = AsyncMock()
            mock_users_repo_class.return_value = mock_users_repo

            response = client.post(
                "/api/v1/users/me/become-host",
                headers={"Authorization": "Bearer valid_token"},
                json={},
            )

            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["id"] == mock_profile.id
            assert data["user_id"] == mock_profile.user_id
            assert data["hourly_rate_cents"] == 5000
            assert data["verification_status"] == "unverified"

    def test_become_host_user_type_both_if_already_client(
        self, client: TestClient
    ) -> None:
        """Test that user_type becomes BOTH if user was already CLIENT."""
        mock_user = create_mock_user(user_type=UserType.CLIENT)
        mock_profile = create_mock_host_profile(user_id=mock_user.id)

        with (
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_class,
            patch("app.routers.users.HostProfileRepository") as mock_host_repo_class,
            patch("app.routers.users.UserRepository") as mock_users_repo_class,
        ):
            # Set up auth mocks
            mock_token_payload = MagicMock()
            mock_token_payload.sub = mock_user.id
            mock_token_payload.token_type = "access"
            mock_token_service.verify_token.return_value = mock_token_payload

            mock_user_repo = AsyncMock()
            mock_user_repo_class.return_value = mock_user_repo
            mock_user_repo.get_by_id.return_value = mock_user

            # Set up host profile repo mocks
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_user_id.return_value = None
            mock_host_repo.create.return_value = mock_profile
            mock_host_repo.get_dance_styles.return_value = []

            # Set up user repo mock for update
            mock_users_repo = AsyncMock()
            mock_users_repo_class.return_value = mock_users_repo

            response = client.post(
                "/api/v1/users/me/become-host",
                headers={"Authorization": "Bearer valid_token"},
                json={},
            )

            assert response.status_code == status.HTTP_201_CREATED
            # Verify update was called with BOTH (since user was CLIENT)
            mock_users_repo.update_user_type.assert_called_once()
            call_args = mock_users_repo.update_user_type.call_args
            assert call_args.kwargs["user_type"] == UserType.BOTH

    def test_become_host_with_location(self, client: TestClient) -> None:
        """Test that become-host accepts location data."""
        mock_user = create_mock_user(user_type=UserType.CLIENT)
        mock_profile = create_mock_host_profile(user_id=mock_user.id)

        with (
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_class,
            patch("app.routers.users.HostProfileRepository") as mock_host_repo_class,
            patch("app.routers.users.UserRepository") as mock_users_repo_class,
        ):
            # Set up auth mocks
            mock_token_payload = MagicMock()
            mock_token_payload.sub = mock_user.id
            mock_token_payload.token_type = "access"
            mock_token_service.verify_token.return_value = mock_token_payload

            mock_user_repo = AsyncMock()
            mock_user_repo_class.return_value = mock_user_repo
            mock_user_repo.get_by_id.return_value = mock_user

            # Set up host profile repo mocks
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_user_id.return_value = None
            mock_host_repo.create.return_value = mock_profile
            mock_host_repo.get_dance_styles.return_value = []

            # Set up user repo mock for update
            mock_users_repo = AsyncMock()
            mock_users_repo_class.return_value = mock_users_repo

            response = client.post(
                "/api/v1/users/me/become-host",
                headers={"Authorization": "Bearer valid_token"},
                json={
                    "location": {
                        "latitude": 40.7128,
                        "longitude": -74.0060,
                    }
                },
            )

            assert response.status_code == status.HTTP_201_CREATED
            # Verify location was passed
            mock_host_repo.create.assert_called_once()
            call_kwargs = mock_host_repo.create.call_args.kwargs
            assert call_kwargs["latitude"] == 40.7128
            assert call_kwargs["longitude"] == -74.0060
