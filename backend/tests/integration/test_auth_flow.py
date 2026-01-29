"""Integration tests for authentication flow.

Tests the complete authentication lifecycle:
- User registration
- User login
- Token refresh
- Get current user
- Logout

These tests use mocked repositories to simulate database interactions
while testing the full API endpoint behavior.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import create_app
from app.models.user import UserType
from app.services.token import token_service

from .conftest import create_authenticated_client, make_mock_user


class TestAuthenticationFlowE2E:
    """End-to-end tests for complete authentication flow."""

    @pytest.fixture
    def app(self):
        """Create a fresh app for each test."""
        return create_app()

    @pytest.fixture
    def client(self, app) -> TestClient:
        """Create a test client."""
        return TestClient(app)

    def test_complete_registration_login_flow(self, app, client: TestClient) -> None:
        """Test complete flow: register -> login -> get me -> logout."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"

        # Step 1: Register a new user
        with patch("app.routers.auth.UserRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo
            mock_repo.exists_by_email.return_value = False

            mock_user = make_mock_user(
                user_id=user_id,
                email="newuser@example.com",
                first_name="New",
                last_name="User",
            )
            mock_repo.create.return_value = mock_user

            register_response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "newuser@example.com",
                    "password": "SecurePass123",
                    "first_name": "New",
                    "last_name": "User",
                },
            )

            assert register_response.status_code == status.HTTP_201_CREATED
            register_data = register_response.json()
            assert register_data["email"] == "newuser@example.com"
            assert "password_hash" not in register_data

        # Step 2: Login with the registered user
        with (
            patch("app.routers.auth.UserRepository") as mock_repo_class,
            patch("app.routers.auth.password_service") as mock_pw_service,
        ):
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            mock_user = make_mock_user(
                user_id=user_id,
                email="newuser@example.com",
                first_name="New",
                last_name="User",
            )
            mock_repo.get_by_email.return_value = mock_user
            mock_pw_service.verify_password.return_value = True

            login_response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": "newuser@example.com",
                    "password": "SecurePass123",
                },
            )

            assert login_response.status_code == status.HTTP_200_OK
            login_data = login_response.json()
            assert "access_token" in login_data
            assert "refresh_token" in login_data
            assert login_data["token_type"] == "bearer"
            access_token = login_data["access_token"]
            refresh_token = login_data["refresh_token"]

        # Step 3: Access protected endpoint (/me) with access token
        auth_client = create_authenticated_client(app, mock_user)
        me_response = auth_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert me_response.status_code == status.HTTP_200_OK
        me_data = me_response.json()
        assert me_data["email"] == "newuser@example.com"
        assert me_data["first_name"] == "New"
        assert me_data["last_name"] == "User"

        # Step 4: Refresh access token
        # Verify refresh token is valid and get new access token
        refresh_payload = token_service.verify_token(refresh_token)
        assert refresh_payload.sub == user_id
        assert refresh_payload.token_type == "refresh"

        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert refresh_response.status_code == status.HTTP_200_OK
        refresh_data = refresh_response.json()
        assert "access_token" in refresh_data
        new_access_token = refresh_data["access_token"]
        assert new_access_token != access_token  # New token generated

        # Step 5: Logout
        logout_response = auth_client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {new_access_token}"},
        )

        assert logout_response.status_code == status.HTTP_204_NO_CONTENT


class TestRegistrationEndpointIntegration:
    """Integration tests for user registration endpoint."""

    @pytest.fixture
    def app(self):
        """Create a fresh app for each test."""
        return create_app()

    @pytest.fixture
    def client(self, app) -> TestClient:
        """Create a test client."""
        return TestClient(app)

    def test_register_with_valid_data_creates_user(self, client: TestClient) -> None:
        """Test that valid registration data creates a user successfully."""
        with patch("app.routers.auth.UserRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo
            mock_repo.exists_by_email.return_value = False

            mock_user = make_mock_user(
                email="valid@example.com",
                first_name="Valid",
                last_name="User",
            )
            mock_repo.create.return_value = mock_user

            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "valid@example.com",
                    "password": "ValidPass123",
                    "first_name": "Valid",
                    "last_name": "User",
                },
            )

            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["email"] == "valid@example.com"
            assert data["first_name"] == "Valid"
            assert data["last_name"] == "User"
            assert data["user_type"] == "client"
            assert data["is_active"] is True

    def test_register_with_host_user_type(self, client: TestClient) -> None:
        """Test registration with host user type."""
        with patch("app.routers.auth.UserRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo
            mock_repo.exists_by_email.return_value = False

            mock_user = make_mock_user(
                email="host@example.com",
                first_name="Host",
                last_name="User",
                user_type=UserType.HOST,
            )
            mock_repo.create.return_value = mock_user

            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "host@example.com",
                    "password": "HostPass123",
                    "first_name": "Host",
                    "last_name": "User",
                    "user_type": "host",
                },
            )

            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["user_type"] == "host"

    def test_register_duplicate_email_rejected(self, client: TestClient) -> None:
        """Test that duplicate email registration is rejected."""
        with patch("app.routers.auth.UserRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo
            mock_repo.exists_by_email.return_value = True

            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "existing@example.com",
                    "password": "ExistingPass123",
                    "first_name": "Existing",
                    "last_name": "User",
                },
            )

            assert response.status_code == status.HTTP_409_CONFLICT
            assert "already registered" in response.json()["detail"].lower()

    def test_register_invalid_email_rejected(self, client: TestClient) -> None:
        """Test that invalid email format is rejected."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "ValidPass123",
                "first_name": "Test",
                "last_name": "User",
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_weak_password_rejected(self, client: TestClient) -> None:
        """Test that weak passwords are rejected."""
        # Missing uppercase
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "weakpass123",
                "first_name": "Test",
                "last_name": "User",
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_short_password_rejected(self, client: TestClient) -> None:
        """Test that short passwords are rejected."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "Short1",
                "first_name": "Test",
                "last_name": "User",
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_password_without_number_rejected(
        self, client: TestClient
    ) -> None:
        """Test that passwords without numbers are rejected."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "NoNumberPass",
                "first_name": "Test",
                "last_name": "User",
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_missing_fields_rejected(self, client: TestClient) -> None:
        """Test that missing required fields are rejected."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestLoginEndpointIntegration:
    """Integration tests for user login endpoint."""

    @pytest.fixture
    def app(self):
        """Create a fresh app for each test."""
        return create_app()

    @pytest.fixture
    def client(self, app) -> TestClient:
        """Create a test client."""
        return TestClient(app)

    def test_login_with_valid_credentials_returns_tokens(
        self, client: TestClient
    ) -> None:
        """Test that valid login returns access and refresh tokens."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"

        with (
            patch("app.routers.auth.UserRepository") as mock_repo_class,
            patch("app.routers.auth.password_service") as mock_pw_service,
        ):
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            mock_user = make_mock_user(user_id=user_id, email="login@example.com")
            mock_repo.get_by_email.return_value = mock_user
            mock_pw_service.verify_password.return_value = True

            response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": "login@example.com",
                    "password": "ValidPass123",
                },
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["token_type"] == "bearer"
            assert data["expires_in"] == 15 * 60

            # Verify tokens are valid
            access_payload = token_service.verify_token(data["access_token"])
            assert access_payload.sub == user_id
            assert access_payload.token_type == "access"

            refresh_payload = token_service.verify_token(data["refresh_token"])
            assert refresh_payload.sub == user_id
            assert refresh_payload.token_type == "refresh"

    def test_login_with_invalid_email_returns_401(self, client: TestClient) -> None:
        """Test that non-existent email returns 401."""
        with patch("app.routers.auth.UserRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo
            mock_repo.get_by_email.return_value = None

            response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": "nonexistent@example.com",
                    "password": "AnyPass123",
                },
            )

            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Invalid email or password" in response.json()["detail"]

    def test_login_with_wrong_password_returns_401(self, client: TestClient) -> None:
        """Test that wrong password returns 401."""
        with (
            patch("app.routers.auth.UserRepository") as mock_repo_class,
            patch("app.routers.auth.password_service") as mock_pw_service,
        ):
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            mock_user = make_mock_user(email="user@example.com")
            mock_repo.get_by_email.return_value = mock_user
            mock_pw_service.verify_password.return_value = False

            response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": "user@example.com",
                    "password": "WrongPass123",
                },
            )

            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Invalid email or password" in response.json()["detail"]

    def test_login_inactive_user_returns_401(self, client: TestClient) -> None:
        """Test that inactive user cannot login."""
        with patch("app.routers.auth.UserRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            mock_user = make_mock_user(email="inactive@example.com", is_active=False)
            mock_repo.get_by_email.return_value = mock_user

            response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": "inactive@example.com",
                    "password": "AnyPass123",
                },
            )

            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_error_messages_dont_leak_user_existence(
        self, client: TestClient
    ) -> None:
        """Test that error messages don't reveal whether email exists."""
        # Test with non-existent user
        with patch("app.routers.auth.UserRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo
            mock_repo.get_by_email.return_value = None

            response_no_user = client.post(
                "/api/v1/auth/login",
                json={
                    "email": "nobody@example.com",
                    "password": "AnyPass123",
                },
            )

        # Test with existing user, wrong password
        with (
            patch("app.routers.auth.UserRepository") as mock_repo_class,
            patch("app.routers.auth.password_service") as mock_pw_service,
        ):
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            mock_user = make_mock_user(email="exists@example.com")
            mock_repo.get_by_email.return_value = mock_user
            mock_pw_service.verify_password.return_value = False

            response_wrong_pw = client.post(
                "/api/v1/auth/login",
                json={
                    "email": "exists@example.com",
                    "password": "WrongPass123",
                },
            )

        # Both should return same error to prevent user enumeration
        assert response_no_user.status_code == response_wrong_pw.status_code
        assert response_no_user.json()["detail"] == response_wrong_pw.json()["detail"]


class TestRefreshEndpointIntegration:
    """Integration tests for token refresh endpoint."""

    @pytest.fixture
    def app(self):
        """Create a fresh app for each test."""
        return create_app()

    @pytest.fixture
    def client(self, app) -> TestClient:
        """Create a test client."""
        return TestClient(app)

    def test_refresh_with_valid_token_returns_new_access_token(
        self, client: TestClient
    ) -> None:
        """Test that valid refresh token returns new access token."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        refresh_token = token_service.create_refresh_token(user_id)

        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 15 * 60

        # Verify new access token is valid and has correct user_id
        new_access_payload = token_service.verify_token(data["access_token"])
        assert new_access_payload.sub == user_id
        assert new_access_payload.token_type == "access"

    def test_refresh_with_access_token_returns_401(self, client: TestClient) -> None:
        """Test that using access token for refresh returns 401."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        access_token = token_service.create_access_token(user_id)

        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "refresh token" in response.json()["detail"].lower()

    def test_refresh_with_invalid_token_returns_401(self, client: TestClient) -> None:
        """Test that invalid refresh token returns 401."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_with_missing_token_returns_422(self, client: TestClient) -> None:
        """Test that missing refresh token returns 422."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestGetCurrentUserEndpointIntegration:
    """Integration tests for get current user endpoint."""

    @pytest.fixture
    def app(self):
        """Create a fresh app for each test."""
        return create_app()

    @pytest.fixture
    def client(self, app) -> TestClient:
        """Create a test client."""
        return TestClient(app)

    def test_get_me_with_valid_token_returns_user_data(
        self, app, client: TestClient
    ) -> None:
        """Test that valid authentication returns user profile."""
        mock_user = make_mock_user(
            user_id="550e8400-e29b-41d4-a716-446655440000",
            email="me@example.com",
            first_name="Me",
            last_name="User",
            user_type=UserType.HOST,
            email_verified=True,
        )

        auth_client = create_authenticated_client(app, mock_user)

        response = auth_client.get("/api/v1/auth/me")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "me@example.com"
        assert data["first_name"] == "Me"
        assert data["last_name"] == "User"
        assert data["user_type"] == "host"
        assert data["email_verified"] is True
        assert "password_hash" not in data
        assert "password" not in data

    def test_get_me_without_token_returns_401(self, client: TestClient) -> None:
        """Test that missing authentication returns 401."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_me_with_invalid_token_returns_401(self, client: TestClient) -> None:
        """Test that invalid token returns 401."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestLogoutEndpointIntegration:
    """Integration tests for logout endpoint."""

    @pytest.fixture
    def app(self):
        """Create a fresh app for each test."""
        return create_app()

    @pytest.fixture
    def client(self, app) -> TestClient:
        """Create a test client."""
        return TestClient(app)

    def test_logout_with_valid_token_returns_204(self, app) -> None:
        """Test that valid logout returns 204 No Content."""
        mock_user = make_mock_user()
        auth_client = create_authenticated_client(app, mock_user)

        response = auth_client.post("/api/v1/auth/logout")

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.content == b""

    def test_logout_without_token_returns_401(self, client: TestClient) -> None:
        """Test that logout without authentication returns 401."""
        response = client.post("/api/v1/auth/logout")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_is_idempotent(self, app) -> None:
        """Test that logout can be called multiple times safely."""
        mock_user = make_mock_user()
        auth_client = create_authenticated_client(app, mock_user)

        # First logout
        response1 = auth_client.post("/api/v1/auth/logout")
        assert response1.status_code == status.HTTP_204_NO_CONTENT

        # Second logout (should also succeed)
        response2 = auth_client.post("/api/v1/auth/logout")
        assert response2.status_code == status.HTTP_204_NO_CONTENT
