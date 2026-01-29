"""Unit tests for users router endpoints."""

from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from PIL import Image

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


def create_mock_dance_style(
    dance_style_id: str = "770e8400-e29b-41d4-a716-446655440002",
    name: str = "Salsa",
    slug: str = "salsa",
    category: str = "latin",
) -> MagicMock:
    """Create a mock dance style for testing."""
    mock_style = MagicMock()
    mock_style.id = dance_style_id
    mock_style.name = name
    mock_style.slug = slug
    mock_style.category = category
    mock_style.description = f"A popular {category} dance"
    return mock_style


def create_mock_host_dance_style(
    dance_style_id: str = "770e8400-e29b-41d4-a716-446655440002",
    skill_level: int = 3,
    dance_style: MagicMock | None = None,
) -> MagicMock:
    """Create a mock host dance style junction for testing."""
    mock_hds = MagicMock()
    mock_hds.dance_style_id = dance_style_id
    mock_hds.skill_level = skill_level
    mock_hds.dance_style = dance_style or create_mock_dance_style(dance_style_id)
    return mock_hds


class TestGetMyHostProfileEndpoint:
    """Tests for GET /api/v1/users/me/host-profile endpoint."""

    def test_get_host_profile_endpoint_exists(self, client: TestClient) -> None:
        """Test that the get-host-profile endpoint exists and accepts GET."""
        # Without auth, should get 401, not 404
        response = client.get("/api/v1/users/me/host-profile")
        assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_get_host_profile_requires_authentication(self, client: TestClient) -> None:
        """Test that get-host-profile requires authentication."""
        response = client.get("/api/v1/users/me/host-profile")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_host_profile_returns_profile(self, client: TestClient) -> None:
        """Test that get-host-profile returns the user's host profile."""
        mock_user = create_mock_user(user_type=UserType.HOST)
        mock_profile = create_mock_host_profile(user_id=mock_user.id)
        mock_dance_style = create_mock_dance_style()
        mock_hds = create_mock_host_dance_style(dance_style=mock_dance_style)

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

            # Set up host profile repo mocks
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_user_id.return_value = mock_profile
            mock_host_repo.get_dance_styles.return_value = [mock_hds]

            response = client.get(
                "/api/v1/users/me/host-profile",
                headers={"Authorization": "Bearer valid_token"},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["id"] == mock_profile.id
            assert data["user_id"] == mock_profile.user_id
            assert len(data["dance_styles"]) == 1
            assert data["dance_styles"][0]["dance_style"]["name"] == "Salsa"

    def test_get_host_profile_returns_404_if_not_host(self, client: TestClient) -> None:
        """Test that get-host-profile returns 404 if user doesn't have profile."""
        mock_user = create_mock_user(user_type=UserType.CLIENT)

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

            # No host profile
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_user_id.return_value = None

            response = client.get(
                "/api/v1/users/me/host-profile",
                headers={"Authorization": "Bearer valid_token"},
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "host profile" in response.json()["detail"].lower()


class TestUpdateMyHostProfileEndpoint:
    """Tests for PATCH /api/v1/users/me/host-profile endpoint."""

    def test_update_host_profile_endpoint_exists(self, client: TestClient) -> None:
        """Test that the update-host-profile endpoint exists and accepts PATCH."""
        # Without auth, should get 401, not 404
        response = client.patch("/api/v1/users/me/host-profile")
        assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_update_host_profile_requires_authentication(
        self, client: TestClient
    ) -> None:
        """Test that update-host-profile requires authentication."""
        response = client.patch("/api/v1/users/me/host-profile")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_host_profile_updates_fields(self, client: TestClient) -> None:
        """Test that update-host-profile updates the provided fields."""
        mock_user = create_mock_user(user_type=UserType.HOST)
        mock_profile = create_mock_host_profile(user_id=mock_user.id)
        updated_profile = create_mock_host_profile(user_id=mock_user.id)
        updated_profile.bio = "Updated bio"
        updated_profile.headline = "Updated headline"
        updated_profile.hourly_rate_cents = 10000

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

            # Set up host profile repo mocks
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_user_id.return_value = mock_profile
            mock_host_repo.update.return_value = updated_profile
            mock_host_repo.get_dance_styles.return_value = []

            response = client.patch(
                "/api/v1/users/me/host-profile",
                headers={"Authorization": "Bearer valid_token"},
                json={
                    "bio": "Updated bio",
                    "headline": "Updated headline",
                    "hourly_rate_cents": 10000,
                },
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["bio"] == "Updated bio"
            assert data["headline"] == "Updated headline"
            assert data["hourly_rate_cents"] == 10000

    def test_update_host_profile_returns_404_if_not_host(
        self, client: TestClient
    ) -> None:
        """Test that update-host-profile returns 404 if user isn't a host."""
        mock_user = create_mock_user(user_type=UserType.CLIENT)

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

            # No host profile
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_user_id.return_value = None

            response = client.patch(
                "/api/v1/users/me/host-profile",
                headers={"Authorization": "Bearer valid_token"},
                json={"bio": "Updated bio"},
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_host_profile_with_location(self, client: TestClient) -> None:
        """Test that update-host-profile can update location."""
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

            # Set up host profile repo mocks
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_user_id.return_value = mock_profile
            mock_host_repo.update.return_value = mock_profile
            mock_host_repo.get_dance_styles.return_value = []

            response = client.patch(
                "/api/v1/users/me/host-profile",
                headers={"Authorization": "Bearer valid_token"},
                json={
                    "location": {
                        "latitude": 40.7128,
                        "longitude": -74.0060,
                    }
                },
            )

            assert response.status_code == status.HTTP_200_OK
            # Verify update was called with location
            mock_host_repo.update.assert_called_once()
            call_kwargs = mock_host_repo.update.call_args.kwargs
            assert call_kwargs["latitude"] == 40.7128
            assert call_kwargs["longitude"] == -74.0060
            assert call_kwargs["_update_location"] is True


class TestAddDanceStyleEndpoint:
    """Tests for POST /api/v1/users/me/host-profile/dance-styles endpoint."""

    def test_add_dance_style_endpoint_exists(self, client: TestClient) -> None:
        """Test that the add-dance-style endpoint exists and accepts POST."""
        # Without auth, should get 401, not 404
        response = client.post("/api/v1/users/me/host-profile/dance-styles")
        assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_add_dance_style_requires_authentication(self, client: TestClient) -> None:
        """Test that add-dance-style requires authentication."""
        response = client.post("/api/v1/users/me/host-profile/dance-styles")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_add_dance_style_creates_association(self, client: TestClient) -> None:
        """Test that add-dance-style creates a host-dance style association."""
        mock_user = create_mock_user(user_type=UserType.HOST)
        mock_profile = create_mock_host_profile(user_id=mock_user.id)
        mock_dance_style = create_mock_dance_style()
        mock_hds = create_mock_host_dance_style(
            dance_style_id=mock_dance_style.id,
            skill_level=4,
            dance_style=mock_dance_style,
        )

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

            # Set up host profile repo mocks
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_user_id.return_value = mock_profile
            mock_host_repo.get_dance_style_by_id.return_value = mock_dance_style
            mock_host_repo.add_dance_style.return_value = mock_hds

            response = client.post(
                "/api/v1/users/me/host-profile/dance-styles",
                headers={"Authorization": "Bearer valid_token"},
                json={
                    "dance_style_id": mock_dance_style.id,
                    "skill_level": 4,
                },
            )

            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["dance_style_id"] == mock_dance_style.id
            assert data["skill_level"] == 4
            assert data["dance_style"]["name"] == "Salsa"

    def test_add_dance_style_returns_404_if_not_host(self, client: TestClient) -> None:
        """Test that add-dance-style returns 404 if user isn't a host."""
        mock_user = create_mock_user(user_type=UserType.CLIENT)

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

            # No host profile
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_user_id.return_value = None

            response = client.post(
                "/api/v1/users/me/host-profile/dance-styles",
                headers={"Authorization": "Bearer valid_token"},
                json={
                    "dance_style_id": "770e8400-e29b-41d4-a716-446655440002",
                    "skill_level": 3,
                },
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "host profile" in response.json()["detail"].lower()

    def test_add_dance_style_returns_404_if_style_not_found(
        self, client: TestClient
    ) -> None:
        """Test that add-dance-style returns 404 if dance style doesn't exist."""
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

            # Dance style not found
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_user_id.return_value = mock_profile
            mock_host_repo.get_dance_style_by_id.return_value = None

            response = client.post(
                "/api/v1/users/me/host-profile/dance-styles",
                headers={"Authorization": "Bearer valid_token"},
                json={
                    "dance_style_id": "770e8400-e29b-41d4-a716-446655440002",
                    "skill_level": 3,
                },
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "dance style" in response.json()["detail"].lower()


class TestRemoveDanceStyleEndpoint:
    """Tests for DELETE /api/v1/users/me/host-profile/dance-styles/{id} endpoint."""

    def test_remove_dance_style_endpoint_exists(self, client: TestClient) -> None:
        """Test that the remove-dance-style endpoint exists and accepts DELETE."""
        # Without auth, should get 401, not 404
        response = client.delete(
            "/api/v1/users/me/host-profile/dance-styles/770e8400-e29b-41d4-a716-446655440002"
        )
        assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_remove_dance_style_requires_authentication(
        self, client: TestClient
    ) -> None:
        """Test that remove-dance-style requires authentication."""
        response = client.delete(
            "/api/v1/users/me/host-profile/dance-styles/770e8400-e29b-41d4-a716-446655440002"
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_remove_dance_style_removes_association(self, client: TestClient) -> None:
        """Test that remove-dance-style removes the dance style association."""
        mock_user = create_mock_user(user_type=UserType.HOST)
        mock_profile = create_mock_host_profile(user_id=mock_user.id)
        dance_style_id = "770e8400-e29b-41d4-a716-446655440002"

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

            # Set up host profile repo mocks
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_user_id.return_value = mock_profile
            mock_host_repo.remove_dance_style.return_value = True

            response = client.delete(
                f"/api/v1/users/me/host-profile/dance-styles/{dance_style_id}",
                headers={"Authorization": "Bearer valid_token"},
            )

            assert response.status_code == status.HTTP_204_NO_CONTENT
            mock_host_repo.remove_dance_style.assert_called_once()

    def test_remove_dance_style_returns_404_if_not_host(
        self, client: TestClient
    ) -> None:
        """Test that remove-dance-style returns 404 if user isn't a host."""
        mock_user = create_mock_user(user_type=UserType.CLIENT)
        dance_style_id = "770e8400-e29b-41d4-a716-446655440002"

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

            # No host profile
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_user_id.return_value = None

            response = client.delete(
                f"/api/v1/users/me/host-profile/dance-styles/{dance_style_id}",
                headers={"Authorization": "Bearer valid_token"},
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_remove_dance_style_returns_404_if_not_found(
        self, client: TestClient
    ) -> None:
        """Test that remove-dance-style returns 404 if dance style not found."""
        mock_user = create_mock_user(user_type=UserType.HOST)
        mock_profile = create_mock_host_profile(user_id=mock_user.id)
        dance_style_id = "770e8400-e29b-41d4-a716-446655440002"

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

            # Dance style not on profile
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_user_id.return_value = mock_profile
            mock_host_repo.remove_dance_style.return_value = False

            response = client.delete(
                f"/api/v1/users/me/host-profile/dance-styles/{dance_style_id}",
                headers={"Authorization": "Bearer valid_token"},
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "not found" in response.json()["detail"].lower()


class TestUploadAvatarEndpoint:
    """Tests for POST /api/v1/users/me/avatar endpoint."""

    def test_upload_avatar_endpoint_exists(self, client: TestClient) -> None:
        """Test that the upload-avatar endpoint exists and accepts POST."""
        # Without auth, should get 401, not 404
        response = client.post("/api/v1/users/me/avatar")
        assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_upload_avatar_requires_authentication(self, client: TestClient) -> None:
        """Test that upload-avatar requires authentication."""
        response = client.post("/api/v1/users/me/avatar")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_upload_avatar_success(self, client: TestClient) -> None:
        """Test successful avatar upload with valid image."""
        mock_user = create_mock_user()
        mock_user.avatar_url = None
        mock_user.avatar_thumbnail_url = None

        # Create a test image
        img = Image.new("RGB", (100, 100), color="red")
        buffer = BytesIO()
        img.save(buffer, format="JPEG")
        buffer.seek(0)

        with (
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_class,
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

            # Set up user repo for updating avatar
            mock_users_repo = AsyncMock()
            mock_users_repo_class.return_value = mock_users_repo

            response = client.post(
                "/api/v1/users/me/avatar",
                headers={"Authorization": "Bearer valid_token"},
                files={"file": ("avatar.jpg", buffer, "image/jpeg")},
            )

            # The endpoint should succeed and return avatar URLs
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "avatar_url" in data
            assert "avatar_thumbnail_url" in data
            # User repository should be called to update avatar
            mock_users_repo.update_avatar.assert_called_once()

    def test_upload_avatar_invalid_file(self, client: TestClient) -> None:
        """Test upload rejects invalid file type."""
        mock_user = create_mock_user()

        with (
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_class,
        ):
            # Set up auth mocks
            mock_token_payload = MagicMock()
            mock_token_payload.sub = mock_user.id
            mock_token_payload.token_type = "access"
            mock_token_service.verify_token.return_value = mock_token_payload

            mock_user_repo = AsyncMock()
            mock_user_repo_class.return_value = mock_user_repo
            mock_user_repo.get_by_id.return_value = mock_user

            response = client.post(
                "/api/v1/users/me/avatar",
                headers={"Authorization": "Bearer valid_token"},
                files={"file": ("test.txt", b"not an image", "text/plain")},
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Invalid" in response.json()["detail"]


class TestDeleteAvatarEndpoint:
    """Tests for DELETE /api/v1/users/me/avatar endpoint."""

    def test_delete_avatar_endpoint_exists(self, client: TestClient) -> None:
        """Test that the delete-avatar endpoint exists and accepts DELETE."""
        # Without auth, should get 401, not 404
        response = client.delete("/api/v1/users/me/avatar")
        assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_delete_avatar_requires_authentication(self, client: TestClient) -> None:
        """Test that delete-avatar requires authentication."""
        response = client.delete("/api/v1/users/me/avatar")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_avatar_success(self, client: TestClient) -> None:
        """Test successful avatar deletion."""
        mock_user = create_mock_user()
        mock_user.avatar_url = "https://example.com/avatars/user/abc/avatar.webp"
        mock_user.avatar_thumbnail_url = (
            "https://example.com/avatars/user/abc/thumb.webp"
        )

        with (
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_class,
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

            # Set up user repo for deleting avatar
            mock_users_repo = AsyncMock()
            mock_users_repo_class.return_value = mock_users_repo

            response = client.delete(
                "/api/v1/users/me/avatar",
                headers={"Authorization": "Bearer valid_token"},
            )

            assert response.status_code == status.HTTP_204_NO_CONTENT
            mock_users_repo.delete_avatar.assert_called_once()

    def test_delete_avatar_no_avatar_returns_404(self, client: TestClient) -> None:
        """Test that delete-avatar returns 404 if user has no avatar."""
        mock_user = create_mock_user()
        mock_user.avatar_url = None
        mock_user.avatar_thumbnail_url = None

        with (
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_user_repo_class,
            patch("app.routers.users.StorageService"),
        ):
            # Set up auth mocks
            mock_token_payload = MagicMock()
            mock_token_payload.sub = mock_user.id
            mock_token_payload.token_type = "access"
            mock_token_service.verify_token.return_value = mock_token_payload

            mock_user_repo = AsyncMock()
            mock_user_repo_class.return_value = mock_user_repo
            mock_user_repo.get_by_id.return_value = mock_user

            response = client.delete(
                "/api/v1/users/me/avatar",
                headers={"Authorization": "Bearer valid_token"},
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "no avatar" in response.json()["detail"].lower()
