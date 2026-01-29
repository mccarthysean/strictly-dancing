"""Unit tests for authentication router endpoints."""

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
    """Tests for POST /api/v1/auth/register endpoint."""

    def test_registration_endpoint_exists(self, client: TestClient) -> None:
        """Test that the registration endpoint exists and accepts POST."""
        with patch("app.routers.auth.UserRepository") as mock_repo_class:
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
            mock_repo.create.return_value = mock_user

            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "test@example.com",
                    "password": "SecurePass123",
                    "first_name": "Test",
                    "last_name": "User",
                },
            )
            # Should not be 404 (endpoint exists)
            assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_registration_returns_201_on_success(self, client: TestClient) -> None:
        """Test that successful registration returns 201 Created."""
        with patch("app.routers.auth.UserRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo
            mock_repo.exists_by_email.return_value = False

            # Create a mock user that will be returned
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
            mock_repo.create.return_value = mock_user

            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "test@example.com",
                    "password": "SecurePass123",
                    "first_name": "Test",
                    "last_name": "User",
                },
            )
            assert response.status_code == status.HTTP_201_CREATED

    def test_registration_returns_user_response(self, client: TestClient) -> None:
        """Test that registration returns UserResponse with correct data."""
        with patch("app.routers.auth.UserRepository") as mock_repo_class:
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
            mock_repo.create.return_value = mock_user

            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "test@example.com",
                    "password": "SecurePass123",
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
                    "password": "SecurePass123",
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
            # Simulates that lowercase version exists
            mock_repo.exists_by_email.return_value = True

            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "EXISTING@EXAMPLE.COM",  # Uppercase
                    "password": "SecurePass123",
                    "first_name": "Test",
                    "last_name": "User",
                },
            )
            assert response.status_code == status.HTTP_409_CONFLICT

    def test_registration_hashes_password(self, client: TestClient) -> None:
        """Test that registration hashes password before storing."""
        with (
            patch("app.routers.auth.UserRepository") as mock_repo_class,
            patch("app.routers.auth.password_service") as mock_password_service,
        ):
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo
            mock_repo.exists_by_email.return_value = False

            mock_password_service.hash_password.return_value = "argon2$hashed"

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
            mock_repo.create.return_value = mock_user

            client.post(
                "/api/v1/auth/register",
                json={
                    "email": "test@example.com",
                    "password": "SecurePass123",
                    "first_name": "Test",
                    "last_name": "User",
                },
            )

            # Verify password was hashed
            mock_password_service.hash_password.assert_called_once_with("SecurePass123")
            # Verify hashed password was passed to create
            mock_repo.create.assert_called_once()
            call_args = mock_repo.create.call_args
            assert call_args[1]["password_hash"] == "argon2$hashed"

    def test_registration_creates_user_in_database(self, client: TestClient) -> None:
        """Test that registration creates user in database via repository."""
        with (
            patch("app.routers.auth.UserRepository") as mock_repo_class,
            patch("app.routers.auth.password_service") as mock_password_service,
        ):
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo
            mock_repo.exists_by_email.return_value = False

            mock_password_service.hash_password.return_value = "argon2$hashed"

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
            mock_repo.create.return_value = mock_user

            client.post(
                "/api/v1/auth/register",
                json={
                    "email": "newuser@example.com",
                    "password": "SecurePass123",
                    "first_name": "New",
                    "last_name": "User",
                    "user_type": "client",
                },
            )

            mock_repo.create.assert_called_once()

    def test_registration_invalid_email_returns_422(self, client: TestClient) -> None:
        """Test that invalid email format returns 422."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "SecurePass123",
                "first_name": "Test",
                "last_name": "User",
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_registration_weak_password_returns_422(self, client: TestClient) -> None:
        """Test that weak password returns 422."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "weak",  # Too short, no uppercase/number
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
                # Missing password, first_name, last_name
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
