"""Unit tests for authentication router endpoints (passwordless)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import create_app
from app.models.user import UserType


@pytest.fixture
def app():
    """Create a test FastAPI application."""
    return create_app()


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


class TestRegistrationEndpoint:
    """Tests for POST /api/v1/auth/register endpoint (passwordless)."""

    def test_registration_endpoint_exists(self, client: TestClient) -> None:
        """Test that the registration endpoint exists and accepts POST."""
        with (
            patch("app.routers.auth.UserRepository") as mock_repo_class,
            patch("app.routers.auth.send_welcome_email") as mock_welcome_email,
        ):
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo
            mock_repo.exists_by_email.return_value = False

            mock_user = MagicMock()
            mock_user.id = "550e8400-e29b-41d4-a716-446655440000"
            mock_user.email = "test@example.com"
            mock_user.first_name = "Test"
            mock_user.last_name = "User"
            mock_user.user_type = UserType.CLIENT
            mock_user.email_verified = False
            mock_user.is_active = True
            mock_user.created_at = "2026-01-29T00:00:00Z"
            mock_user.updated_at = "2026-01-29T00:00:00Z"
            mock_repo.create_passwordless.return_value = mock_user
            mock_welcome_email.delay = MagicMock()

            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "test@example.com",
                    "first_name": "Test",
                    "last_name": "User",
                },
            )
            # Should not be 404 (endpoint exists)
            assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_registration_returns_201_on_success(self, client: TestClient) -> None:
        """Test that successful registration returns 201 Created."""
        with (
            patch("app.routers.auth.UserRepository") as mock_repo_class,
            patch("app.routers.auth.send_welcome_email") as mock_welcome_email,
        ):
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo
            mock_repo.exists_by_email.return_value = False

            mock_user = MagicMock()
            mock_user.id = "550e8400-e29b-41d4-a716-446655440000"
            mock_user.email = "test@example.com"
            mock_user.first_name = "Test"
            mock_user.last_name = "User"
            mock_user.user_type = UserType.CLIENT
            mock_user.email_verified = False
            mock_user.is_active = True
            mock_user.created_at = "2026-01-29T00:00:00Z"
            mock_user.updated_at = "2026-01-29T00:00:00Z"
            mock_repo.create_passwordless.return_value = mock_user
            mock_welcome_email.delay = MagicMock()

            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "test@example.com",
                    "first_name": "Test",
                    "last_name": "User",
                },
            )
            assert response.status_code == status.HTTP_201_CREATED

    def test_registration_returns_user_response(self, client: TestClient) -> None:
        """Test that registration returns UserResponse with correct data."""
        with (
            patch("app.routers.auth.UserRepository") as mock_repo_class,
            patch("app.routers.auth.send_welcome_email") as mock_welcome_email,
        ):
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo
            mock_repo.exists_by_email.return_value = False

            mock_user = MagicMock()
            mock_user.id = "550e8400-e29b-41d4-a716-446655440000"
            mock_user.email = "test@example.com"
            mock_user.first_name = "Test"
            mock_user.last_name = "User"
            mock_user.user_type = UserType.CLIENT
            mock_user.email_verified = False
            mock_user.is_active = True
            mock_user.created_at = "2026-01-29T00:00:00Z"
            mock_user.updated_at = "2026-01-29T00:00:00Z"
            mock_repo.create_passwordless.return_value = mock_user
            mock_welcome_email.delay = MagicMock()

            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "test@example.com",
                    "first_name": "Test",
                    "last_name": "User",
                },
            )

            data = response.json()
            assert data["email"] == "test@example.com"
            assert data["first_name"] == "Test"
            assert data["last_name"] == "User"
            assert data["user_type"] == "client"
            assert "password_hash" not in data
            assert "password" not in data

    def test_registration_duplicate_email_returns_409(self, client: TestClient) -> None:
        """Test that registering with existing email returns 409 Conflict."""
        with patch("app.routers.auth.UserRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo
            mock_repo.exists_by_email.return_value = True

            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "existing@example.com",
                    "first_name": "Test",
                    "last_name": "User",
                },
            )
            assert response.status_code == status.HTTP_409_CONFLICT
            assert "already registered" in response.json()["detail"].lower()

    def test_registration_case_insensitive_email_check(
        self, client: TestClient
    ) -> None:
        """Test that email duplicate check is case-insensitive."""
        with patch("app.routers.auth.UserRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo
            mock_repo.exists_by_email.return_value = True

            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "EXISTING@EXAMPLE.COM",
                    "first_name": "Test",
                    "last_name": "User",
                },
            )
            assert response.status_code == status.HTTP_409_CONFLICT

    def test_registration_sends_welcome_email(self, client: TestClient) -> None:
        """Test that registration sends welcome email."""
        with (
            patch("app.routers.auth.UserRepository") as mock_repo_class,
            patch("app.routers.auth.send_welcome_email") as mock_welcome_email,
        ):
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo
            mock_repo.exists_by_email.return_value = False

            mock_user = MagicMock()
            mock_user.id = "550e8400-e29b-41d4-a716-446655440000"
            mock_user.email = "newuser@example.com"
            mock_user.first_name = "New"
            mock_user.last_name = "User"
            mock_user.user_type = UserType.CLIENT
            mock_user.email_verified = False
            mock_user.is_active = True
            mock_user.created_at = "2026-01-29T00:00:00Z"
            mock_user.updated_at = "2026-01-29T00:00:00Z"
            mock_repo.create_passwordless.return_value = mock_user
            mock_welcome_email.delay = MagicMock()

            client.post(
                "/api/v1/auth/register",
                json={
                    "email": "newuser@example.com",
                    "first_name": "New",
                    "last_name": "User",
                },
            )

            mock_welcome_email.delay.assert_called_once_with(
                to_email="newuser@example.com",
                name="New",
            )

    def test_registration_creates_user_without_password(
        self, client: TestClient
    ) -> None:
        """Test that registration creates user via create_passwordless."""
        with (
            patch("app.routers.auth.UserRepository") as mock_repo_class,
            patch("app.routers.auth.send_welcome_email") as mock_welcome_email,
        ):
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo
            mock_repo.exists_by_email.return_value = False

            mock_user = MagicMock()
            mock_user.id = "550e8400-e29b-41d4-a716-446655440000"
            mock_user.email = "newuser@example.com"
            mock_user.first_name = "New"
            mock_user.last_name = "User"
            mock_user.user_type = UserType.CLIENT
            mock_user.email_verified = False
            mock_user.is_active = True
            mock_user.created_at = "2026-01-29T00:00:00Z"
            mock_user.updated_at = "2026-01-29T00:00:00Z"
            mock_repo.create_passwordless.return_value = mock_user
            mock_welcome_email.delay = MagicMock()

            client.post(
                "/api/v1/auth/register",
                json={
                    "email": "newuser@example.com",
                    "first_name": "New",
                    "last_name": "User",
                    "user_type": "client",
                },
            )

            mock_repo.create_passwordless.assert_called_once()
            # Should not call the old create method
            mock_repo.create.assert_not_called()

    def test_registration_invalid_email_returns_422(self, client: TestClient) -> None:
        """Test that invalid email format returns 422."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "first_name": "Test",
                "last_name": "User",
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_registration_missing_fields_returns_422(self, client: TestClient) -> None:
        """Test that missing required fields returns 422."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                # Missing first_name, last_name
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestRequestMagicLinkEndpoint:
    """Tests for POST /api/v1/auth/request-magic-link endpoint."""

    def test_request_magic_link_endpoint_exists(self, client: TestClient) -> None:
        """Test that the request-magic-link endpoint exists and accepts POST."""
        with (
            patch("app.routers.auth.UserRepository") as mock_repo_class,
            patch("app.routers.auth.magic_link_service"),
            patch("app.routers.auth.send_magic_link_email"),
        ):
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo
            mock_repo.get_by_email.return_value = None

            response = client.post(
                "/api/v1/auth/request-magic-link",
                json={"email": "test@example.com"},
            )
            assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_request_magic_link_returns_200_for_existing_user(
        self, client: TestClient
    ) -> None:
        """Test that request returns 200 OK for existing user."""
        with (
            patch("app.routers.auth.UserRepository") as mock_repo_class,
            patch("app.routers.auth.magic_link_service") as mock_magic_link,
            patch("app.routers.auth.send_magic_link_email") as mock_email,
        ):
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            mock_user = MagicMock()
            mock_user.email = "test@example.com"
            mock_user.first_name = "Test"
            mock_user.is_active = True
            mock_repo.get_by_email.return_value = mock_user

            mock_magic_link.create_code = AsyncMock(return_value="123456")
            mock_magic_link.DEFAULT_EXPIRY_MINUTES = 15
            mock_email.delay = MagicMock()

            response = client.post(
                "/api/v1/auth/request-magic-link",
                json={"email": "test@example.com"},
            )
            assert response.status_code == status.HTTP_200_OK

    def test_request_magic_link_returns_200_for_nonexistent_user(
        self, client: TestClient
    ) -> None:
        """Test that request returns 200 OK even for nonexistent user (security)."""
        with (
            patch("app.routers.auth.UserRepository") as mock_repo_class,
            patch("app.routers.auth.magic_link_service") as mock_magic_link,
            patch("app.routers.auth.send_magic_link_email"),
        ):
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo
            mock_repo.get_by_email.return_value = None

            mock_magic_link.DEFAULT_EXPIRY_MINUTES = 15

            response = client.post(
                "/api/v1/auth/request-magic-link",
                json={"email": "nonexistent@example.com"},
            )
            # Should return success to prevent user enumeration
            assert response.status_code == status.HTTP_200_OK

    def test_request_magic_link_sends_email(self, client: TestClient) -> None:
        """Test that request sends magic link email."""
        with (
            patch("app.routers.auth.UserRepository") as mock_repo_class,
            patch("app.routers.auth.magic_link_service") as mock_magic_link,
            patch("app.routers.auth.send_magic_link_email") as mock_email,
        ):
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            mock_user = MagicMock()
            mock_user.email = "test@example.com"
            mock_user.first_name = "Test"
            mock_user.is_active = True
            mock_repo.get_by_email.return_value = mock_user

            mock_magic_link.create_code = AsyncMock(return_value="123456")
            mock_magic_link.DEFAULT_EXPIRY_MINUTES = 15
            mock_email.delay = MagicMock()

            client.post(
                "/api/v1/auth/request-magic-link",
                json={"email": "test@example.com"},
            )

            mock_email.delay.assert_called_once_with(
                to_email="test@example.com",
                name="Test",
                code="123456",
                expires_minutes=15,
            )

    def test_request_magic_link_does_not_send_email_for_nonexistent_user(
        self, client: TestClient
    ) -> None:
        """Test that no email is sent for nonexistent user."""
        with (
            patch("app.routers.auth.UserRepository") as mock_repo_class,
            patch("app.routers.auth.magic_link_service") as mock_magic_link,
            patch("app.routers.auth.send_magic_link_email") as mock_email,
        ):
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo
            mock_repo.get_by_email.return_value = None

            mock_magic_link.DEFAULT_EXPIRY_MINUTES = 15
            mock_email.delay = MagicMock()

            client.post(
                "/api/v1/auth/request-magic-link",
                json={"email": "nonexistent@example.com"},
            )

            mock_email.delay.assert_not_called()

    def test_request_magic_link_response_format(self, client: TestClient) -> None:
        """Test that response has correct format."""
        with (
            patch("app.routers.auth.UserRepository") as mock_repo_class,
            patch("app.routers.auth.magic_link_service") as mock_magic_link,
            patch("app.routers.auth.send_magic_link_email"),
        ):
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo
            mock_repo.get_by_email.return_value = None
            mock_magic_link.DEFAULT_EXPIRY_MINUTES = 15

            response = client.post(
                "/api/v1/auth/request-magic-link",
                json={"email": "test@example.com"},
            )

            data = response.json()
            assert "message" in data
            assert "expires_in_minutes" in data
            assert data["expires_in_minutes"] == 15

    def test_request_magic_link_inactive_user_no_email(
        self, client: TestClient
    ) -> None:
        """Test that inactive user does not receive email."""
        with (
            patch("app.routers.auth.UserRepository") as mock_repo_class,
            patch("app.routers.auth.magic_link_service") as mock_magic_link,
            patch("app.routers.auth.send_magic_link_email") as mock_email,
        ):
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            mock_user = MagicMock()
            mock_user.email = "inactive@example.com"
            mock_user.first_name = "Inactive"
            mock_user.is_active = False
            mock_repo.get_by_email.return_value = mock_user

            mock_magic_link.DEFAULT_EXPIRY_MINUTES = 15
            mock_email.delay = MagicMock()

            response = client.post(
                "/api/v1/auth/request-magic-link",
                json={"email": "inactive@example.com"},
            )

            # Should still return success (security)
            assert response.status_code == status.HTTP_200_OK
            # But no email should be sent
            mock_email.delay.assert_not_called()


class TestVerifyMagicLinkEndpoint:
    """Tests for POST /api/v1/auth/verify-magic-link endpoint."""

    def test_verify_magic_link_endpoint_exists(self, client: TestClient) -> None:
        """Test that the verify-magic-link endpoint exists and accepts POST."""
        with (
            patch("app.routers.auth.UserRepository") as mock_repo_class,
            patch("app.routers.auth.magic_link_service") as mock_magic_link,
        ):
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo
            mock_magic_link.verify_code = AsyncMock(return_value=False)

            response = client.post(
                "/api/v1/auth/verify-magic-link",
                json={"email": "test@example.com", "code": "123456"},
            )
            assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_verify_magic_link_valid_code_returns_tokens(
        self, client: TestClient
    ) -> None:
        """Test that valid code returns JWT tokens."""
        with (
            patch("app.routers.auth.UserRepository") as mock_repo_class,
            patch("app.routers.auth.magic_link_service") as mock_magic_link,
            patch("app.routers.auth.token_service") as mock_token_service,
        ):
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            mock_user = MagicMock()
            mock_user.id = "550e8400-e29b-41d4-a716-446655440000"
            mock_user.email = "test@example.com"
            mock_user.email_verified = False
            mock_user.is_active = True
            mock_repo.get_by_email.return_value = mock_user
            mock_repo.mark_email_verified = AsyncMock()

            mock_magic_link.verify_code = AsyncMock(return_value=True)
            mock_token_service.create_access_token.return_value = "mock_access_token"
            mock_token_service.create_refresh_token.return_value = "mock_refresh_token"

            response = client.post(
                "/api/v1/auth/verify-magic-link",
                json={"email": "test@example.com", "code": "123456"},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["access_token"] == "mock_access_token"
            assert data["refresh_token"] == "mock_refresh_token"
            assert data["token_type"] == "bearer"
            assert "expires_in" in data

    def test_verify_magic_link_invalid_code_returns_401(
        self, client: TestClient
    ) -> None:
        """Test that invalid code returns 401."""
        with (
            patch("app.routers.auth.UserRepository") as mock_repo_class,
            patch("app.routers.auth.magic_link_service") as mock_magic_link,
        ):
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo
            mock_magic_link.verify_code = AsyncMock(return_value=False)

            response = client.post(
                "/api/v1/auth/verify-magic-link",
                json={"email": "test@example.com", "code": "999999"},
            )

            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_verify_magic_link_marks_email_verified(self, client: TestClient) -> None:
        """Test that first verification marks email as verified."""
        with (
            patch("app.routers.auth.UserRepository") as mock_repo_class,
            patch("app.routers.auth.magic_link_service") as mock_magic_link,
            patch("app.routers.auth.token_service") as mock_token_service,
        ):
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            mock_user = MagicMock()
            mock_user.id = "550e8400-e29b-41d4-a716-446655440000"
            mock_user.email = "test@example.com"
            mock_user.email_verified = False
            mock_user.is_active = True
            mock_repo.get_by_email.return_value = mock_user
            mock_repo.mark_email_verified = AsyncMock()

            mock_magic_link.verify_code = AsyncMock(return_value=True)
            mock_token_service.create_access_token.return_value = "access"
            mock_token_service.create_refresh_token.return_value = "refresh"

            client.post(
                "/api/v1/auth/verify-magic-link",
                json={"email": "test@example.com", "code": "123456"},
            )

            mock_repo.mark_email_verified.assert_called_once_with(mock_user.id)

    def test_verify_magic_link_skips_email_verified_if_already_verified(
        self, client: TestClient
    ) -> None:
        """Test that already verified email is not re-verified."""
        with (
            patch("app.routers.auth.UserRepository") as mock_repo_class,
            patch("app.routers.auth.magic_link_service") as mock_magic_link,
            patch("app.routers.auth.token_service") as mock_token_service,
        ):
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            mock_user = MagicMock()
            mock_user.id = "550e8400-e29b-41d4-a716-446655440000"
            mock_user.email = "test@example.com"
            mock_user.email_verified = True  # Already verified
            mock_user.is_active = True
            mock_repo.get_by_email.return_value = mock_user
            mock_repo.mark_email_verified = AsyncMock()

            mock_magic_link.verify_code = AsyncMock(return_value=True)
            mock_token_service.create_access_token.return_value = "access"
            mock_token_service.create_refresh_token.return_value = "refresh"

            client.post(
                "/api/v1/auth/verify-magic-link",
                json={"email": "test@example.com", "code": "123456"},
            )

            mock_repo.mark_email_verified.assert_not_called()

    def test_verify_magic_link_nonexistent_user_returns_401(
        self, client: TestClient
    ) -> None:
        """Test that nonexistent user returns 401."""
        with (
            patch("app.routers.auth.UserRepository") as mock_repo_class,
            patch("app.routers.auth.magic_link_service") as mock_magic_link,
        ):
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo
            mock_repo.get_by_email.return_value = None

            mock_magic_link.verify_code = AsyncMock(return_value=True)

            response = client.post(
                "/api/v1/auth/verify-magic-link",
                json={"email": "nonexistent@example.com", "code": "123456"},
            )

            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_verify_magic_link_inactive_user_returns_401(
        self, client: TestClient
    ) -> None:
        """Test that inactive user returns 401."""
        with (
            patch("app.routers.auth.UserRepository") as mock_repo_class,
            patch("app.routers.auth.magic_link_service") as mock_magic_link,
        ):
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            mock_user = MagicMock()
            mock_user.email = "inactive@example.com"
            mock_user.is_active = False
            mock_repo.get_by_email.return_value = mock_user

            mock_magic_link.verify_code = AsyncMock(return_value=True)

            response = client.post(
                "/api/v1/auth/verify-magic-link",
                json={"email": "inactive@example.com", "code": "123456"},
            )

            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_verify_magic_link_invalid_code_format_returns_422(
        self, client: TestClient
    ) -> None:
        """Test that non-6-digit code returns 422."""
        response = client.post(
            "/api/v1/auth/verify-magic-link",
            json={"email": "test@example.com", "code": "abc"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestRefreshEndpoint:
    """Tests for POST /api/v1/auth/refresh endpoint."""

    def test_refresh_endpoint_exists(self, client: TestClient) -> None:
        """Test that the refresh endpoint exists and accepts POST."""
        with patch("app.routers.auth.token_service") as mock_token_service:
            mock_token_service.verify_token.side_effect = ValueError("Invalid token")

            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": "some_token"},
            )
            assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_refresh_valid_token_returns_200(self, client: TestClient) -> None:
        """Test that valid refresh token returns 200 OK."""
        with patch("app.routers.auth.token_service") as mock_token_service:
            mock_payload = MagicMock()
            mock_payload.sub = "550e8400-e29b-41d4-a716-446655440000"
            mock_payload.token_type = "refresh"
            mock_token_service.verify_token.return_value = mock_payload
            mock_token_service.create_access_token.return_value = "new_access_token"

            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": "valid_refresh_token"},
            )
            assert response.status_code == status.HTTP_200_OK

    def test_refresh_valid_token_returns_new_access_token(
        self, client: TestClient
    ) -> None:
        """Test that refresh returns a new access token."""
        with patch("app.routers.auth.token_service") as mock_token_service:
            mock_payload = MagicMock()
            mock_payload.sub = "550e8400-e29b-41d4-a716-446655440000"
            mock_payload.token_type = "refresh"
            mock_token_service.verify_token.return_value = mock_payload
            mock_token_service.create_access_token.return_value = (
                "brand_new_access_token"
            )

            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": "valid_refresh_token"},
            )

            data = response.json()
            assert "access_token" in data
            assert data["access_token"] == "brand_new_access_token"
            assert data["token_type"] == "bearer"
            assert "expires_in" in data
            assert data["expires_in"] == 15 * 60

    def test_refresh_invalid_token_returns_401(self, client: TestClient) -> None:
        """Test that invalid refresh token returns 401."""
        with patch("app.routers.auth.token_service") as mock_token_service:
            mock_token_service.verify_token.side_effect = ValueError("Invalid token")

            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": "invalid_token"},
            )
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Invalid" in response.json()["detail"]

    def test_refresh_expired_token_returns_401(self, client: TestClient) -> None:
        """Test that expired refresh token returns 401."""
        with patch("app.routers.auth.token_service") as mock_token_service:
            mock_token_service.verify_token.side_effect = ValueError(
                "Token has expired"
            )

            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": "expired_token"},
            )
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "expired" in response.json()["detail"].lower()

    def test_refresh_with_access_token_returns_401(self, client: TestClient) -> None:
        """Test that using an access token for refresh returns 401."""
        with patch("app.routers.auth.token_service") as mock_token_service:
            mock_payload = MagicMock()
            mock_payload.sub = "550e8400-e29b-41d4-a716-446655440000"
            mock_payload.token_type = "access"
            mock_token_service.verify_token.return_value = mock_payload

            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": "access_token_not_refresh"},
            )
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "refresh token" in response.json()["detail"].lower()

    def test_refresh_creates_token_with_correct_user_id(
        self, client: TestClient
    ) -> None:
        """Test that refresh creates new access token with correct user ID."""
        with patch("app.routers.auth.token_service") as mock_token_service:
            user_id = "550e8400-e29b-41d4-a716-446655440000"
            mock_payload = MagicMock()
            mock_payload.sub = user_id
            mock_payload.token_type = "refresh"
            mock_token_service.verify_token.return_value = mock_payload
            mock_token_service.create_access_token.return_value = "new_access"

            client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": "valid_refresh_token"},
            )

            mock_token_service.create_access_token.assert_called_once_with(user_id)

    def test_refresh_missing_token_returns_422(self, client: TestClient) -> None:
        """Test that missing refresh token returns 422."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestLogoutEndpoint:
    """Tests for POST /api/v1/auth/logout endpoint."""

    def test_logout_endpoint_exists(self, client: TestClient) -> None:
        """Test that the logout endpoint exists and accepts POST."""
        response = client.post("/api/v1/auth/logout")
        assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_logout_returns_204_on_success(self, client: TestClient) -> None:
        """Test that successful logout returns 204 No Content."""
        from app.core.deps import get_current_user
        from app.main import create_app

        mock_user = MagicMock()
        mock_user.id = "550e8400-e29b-41d4-a716-446655440000"
        mock_user.email = "test@example.com"
        mock_user.is_active = True

        app = create_app()
        app.dependency_overrides[get_current_user] = lambda: mock_user

        with TestClient(app) as test_client:
            response = test_client.post(
                "/api/v1/auth/logout",
                headers={"Authorization": "Bearer valid_token"},
            )
            assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_logout_requires_authentication(self, client: TestClient) -> None:
        """Test that logout requires authentication."""
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_idempotent(self, client: TestClient) -> None:
        """Test that logout is idempotent (can be called multiple times)."""
        from app.core.deps import get_current_user
        from app.main import create_app

        mock_user = MagicMock()
        mock_user.id = "550e8400-e29b-41d4-a716-446655440000"
        mock_user.email = "test@example.com"
        mock_user.is_active = True

        app = create_app()
        app.dependency_overrides[get_current_user] = lambda: mock_user

        with TestClient(app) as test_client:
            response1 = test_client.post(
                "/api/v1/auth/logout",
                headers={"Authorization": "Bearer valid_token"},
            )
            assert response1.status_code == status.HTTP_204_NO_CONTENT

            response2 = test_client.post(
                "/api/v1/auth/logout",
                headers={"Authorization": "Bearer valid_token"},
            )
            assert response2.status_code == status.HTTP_204_NO_CONTENT

    def test_logout_with_invalid_token_returns_401(self, client: TestClient) -> None:
        """Test that logout with invalid token returns 401."""
        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetCurrentUserEndpoint:
    """Tests for GET /api/v1/auth/me endpoint."""

    def test_get_me_endpoint_exists(self, client: TestClient) -> None:
        """Test that the /me endpoint exists and accepts GET."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_get_me_returns_200_on_success(self, client: TestClient) -> None:
        """Test that authenticated request returns 200 OK."""
        from app.core.deps import get_current_user
        from app.main import create_app

        mock_user = MagicMock()
        mock_user.id = "550e8400-e29b-41d4-a716-446655440000"
        mock_user.email = "test@example.com"
        mock_user.first_name = "Test"
        mock_user.last_name = "User"
        mock_user.user_type = UserType.CLIENT
        mock_user.email_verified = False
        mock_user.is_active = True
        mock_user.created_at = "2026-01-29T00:00:00Z"
        mock_user.updated_at = "2026-01-29T00:00:00Z"

        app = create_app()
        app.dependency_overrides[get_current_user] = lambda: mock_user

        with TestClient(app) as test_client:
            response = test_client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer valid_token"},
            )
            assert response.status_code == status.HTTP_200_OK

    def test_get_me_returns_user_data(self, client: TestClient) -> None:
        """Test that /me returns the user's profile data."""
        from app.core.deps import get_current_user
        from app.main import create_app

        mock_user = MagicMock()
        mock_user.id = "550e8400-e29b-41d4-a716-446655440000"
        mock_user.email = "authenticated@example.com"
        mock_user.first_name = "Auth"
        mock_user.last_name = "User"
        mock_user.user_type = UserType.HOST
        mock_user.email_verified = True
        mock_user.is_active = True
        mock_user.created_at = "2026-01-29T00:00:00Z"
        mock_user.updated_at = "2026-01-29T00:00:00Z"

        app = create_app()
        app.dependency_overrides[get_current_user] = lambda: mock_user

        with TestClient(app) as test_client:
            response = test_client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer valid_token"},
            )

            data = response.json()
            assert data["id"] == "550e8400-e29b-41d4-a716-446655440000"
            assert data["email"] == "authenticated@example.com"
            assert data["first_name"] == "Auth"
            assert data["last_name"] == "User"
            assert data["user_type"] == "host"
            assert data["email_verified"] is True
            assert data["is_active"] is True

    def test_get_me_excludes_password_hash(self, client: TestClient) -> None:
        """Test that /me response does not include password_hash."""
        from app.core.deps import get_current_user
        from app.main import create_app

        mock_user = MagicMock()
        mock_user.id = "550e8400-e29b-41d4-a716-446655440000"
        mock_user.email = "test@example.com"
        mock_user.first_name = "Test"
        mock_user.last_name = "User"
        mock_user.user_type = UserType.CLIENT
        mock_user.email_verified = False
        mock_user.is_active = True
        mock_user.password_hash = "argon2$secret_hash"
        mock_user.created_at = "2026-01-29T00:00:00Z"
        mock_user.updated_at = "2026-01-29T00:00:00Z"

        app = create_app()
        app.dependency_overrides[get_current_user] = lambda: mock_user

        with TestClient(app) as test_client:
            response = test_client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer valid_token"},
            )

            data = response.json()
            assert "password_hash" not in data
            assert "password" not in data

    def test_get_me_requires_auth(self, client: TestClient) -> None:
        """Test that /me requires authentication."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_me_with_invalid_token_returns_401(self, client: TestClient) -> None:
        """Test that /me with invalid token returns 401."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_me_returns_full_profile(self, client: TestClient) -> None:
        """Test that /me returns all expected profile fields."""
        from app.core.deps import get_current_user
        from app.main import create_app

        mock_user = MagicMock()
        mock_user.id = "550e8400-e29b-41d4-a716-446655440000"
        mock_user.email = "complete@example.com"
        mock_user.first_name = "Complete"
        mock_user.last_name = "Profile"
        mock_user.user_type = UserType.BOTH
        mock_user.email_verified = True
        mock_user.is_active = True
        mock_user.created_at = "2026-01-29T00:00:00Z"
        mock_user.updated_at = "2026-01-29T12:00:00Z"

        app = create_app()
        app.dependency_overrides[get_current_user] = lambda: mock_user

        with TestClient(app) as test_client:
            response = test_client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer valid_token"},
            )

            data = response.json()
            expected_fields = [
                "id",
                "email",
                "first_name",
                "last_name",
                "user_type",
                "email_verified",
                "is_active",
                "created_at",
                "updated_at",
            ]
            for field in expected_fields:
                assert field in data, f"Missing expected field: {field}"
