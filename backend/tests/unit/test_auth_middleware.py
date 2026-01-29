"""Unit tests for authentication middleware (deps.py)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.core.deps import CurrentUser, get_current_user
from app.models.user import User, UserType


@pytest.fixture
def mock_user() -> MagicMock:
    """Create a mock user object."""
    user = MagicMock(spec=User)
    user.id = "550e8400-e29b-41d4-a716-446655440000"
    user.email = "test@example.com"
    user.first_name = "Test"
    user.last_name = "User"
    user.user_type = UserType.CLIENT
    user.email_verified = False
    user.is_active = True
    user.created_at = "2026-01-29T00:00:00Z"
    user.updated_at = "2026-01-29T00:00:00Z"
    return user


@pytest.fixture
def app_with_protected_route():
    """Create a test app with a protected route."""
    app = FastAPI()

    @app.get("/protected")
    async def protected_route(current_user: CurrentUser) -> dict:
        return {
            "user_id": str(current_user.id),
            "email": current_user.email,
        }

    return app


@pytest.fixture
def client(app_with_protected_route):
    """Create a test client for the app."""
    return TestClient(app_with_protected_route)


class TestGetCurrentUserDependency:
    """Tests for the get_current_user dependency."""

    def test_deps_file_exists(self) -> None:
        """Test that deps.py module exists and can be imported."""
        from app.core import deps

        assert hasattr(deps, "get_current_user")
        assert hasattr(deps, "CurrentUser")
        assert hasattr(deps, "security")

    def test_get_current_user_is_async(self) -> None:
        """Test that get_current_user is an async function."""
        import inspect

        assert inspect.iscoroutinefunction(get_current_user)

    def test_auth_middleware_missing_token_returns_401(
        self, client: TestClient
    ) -> None:
        """Test that missing Authorization header returns 401."""
        response = client.get("/protected")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Not authenticated"
        assert response.headers["WWW-Authenticate"] == "Bearer"

    def test_auth_middleware_valid_token_returns_user(
        self, client: TestClient, mock_user: MagicMock
    ) -> None:
        """Test that valid token returns the authenticated user."""
        with (
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_repo_class,
        ):
            mock_payload = MagicMock()
            mock_payload.sub = "550e8400-e29b-41d4-a716-446655440000"
            mock_payload.token_type = "access"
            mock_token_service.verify_token.return_value = mock_payload

            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo
            mock_repo.get_by_id.return_value = mock_user

            response = client.get(
                "/protected",
                headers={"Authorization": "Bearer valid_access_token"},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["user_id"] == "550e8400-e29b-41d4-a716-446655440000"
            assert data["email"] == "test@example.com"

    def test_auth_middleware_extracts_bearer_token(
        self, client: TestClient, mock_user: MagicMock
    ) -> None:
        """Test that middleware correctly extracts Bearer token from header."""
        with (
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_repo_class,
        ):
            mock_payload = MagicMock()
            mock_payload.sub = "550e8400-e29b-41d4-a716-446655440000"
            mock_payload.token_type = "access"
            mock_token_service.verify_token.return_value = mock_payload

            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo
            mock_repo.get_by_id.return_value = mock_user

            client.get(
                "/protected",
                headers={"Authorization": "Bearer my_specific_token_123"},
            )

            # Verify token_service received the correct token
            mock_token_service.verify_token.assert_called_once_with(
                "my_specific_token_123"
            )

    def test_auth_middleware_invalid_token_returns_401(
        self, client: TestClient
    ) -> None:
        """Test that invalid token returns 401."""
        with patch("app.core.deps.token_service") as mock_token_service:
            mock_token_service.verify_token.side_effect = ValueError("Invalid token")

            response = client.get(
                "/protected",
                headers={"Authorization": "Bearer invalid_token"},
            )

            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert response.json()["detail"] == "Invalid token"
            assert response.headers["WWW-Authenticate"] == "Bearer"

    def test_auth_middleware_expired_token_returns_401(
        self, client: TestClient
    ) -> None:
        """Test that expired token returns 401 with specific message."""
        with patch("app.core.deps.token_service") as mock_token_service:
            mock_token_service.verify_token.side_effect = ValueError(
                "Token has expired"
            )

            response = client.get(
                "/protected",
                headers={"Authorization": "Bearer expired_token"},
            )

            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert response.json()["detail"] == "Token has expired"
            assert response.headers["WWW-Authenticate"] == "Bearer"

    def test_auth_middleware_refresh_token_returns_401(
        self, client: TestClient
    ) -> None:
        """Test that using refresh token instead of access token returns 401."""
        with patch("app.core.deps.token_service") as mock_token_service:
            mock_payload = MagicMock()
            mock_payload.sub = "550e8400-e29b-41d4-a716-446655440000"
            mock_payload.token_type = "refresh"  # Wrong token type
            mock_token_service.verify_token.return_value = mock_payload

            response = client.get(
                "/protected",
                headers={"Authorization": "Bearer refresh_token_not_access"},
            )

            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "access token" in response.json()["detail"].lower()
            assert response.headers["WWW-Authenticate"] == "Bearer"

    def test_auth_middleware_user_not_found_returns_401(
        self, client: TestClient
    ) -> None:
        """Test that returns 401 when user is not found in database."""
        with (
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_repo_class,
        ):
            mock_payload = MagicMock()
            mock_payload.sub = "550e8400-e29b-41d4-a716-446655440000"
            mock_payload.token_type = "access"
            mock_token_service.verify_token.return_value = mock_payload

            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo
            mock_repo.get_by_id.return_value = None  # User not found

            response = client.get(
                "/protected",
                headers={"Authorization": "Bearer valid_token"},
            )

            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert response.json()["detail"] == "User not found"

    def test_auth_middleware_inactive_user_returns_401(
        self, client: TestClient, mock_user: MagicMock
    ) -> None:
        """Test that returns 401 when user account is deactivated."""
        with (
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_repo_class,
        ):
            mock_payload = MagicMock()
            mock_payload.sub = "550e8400-e29b-41d4-a716-446655440000"
            mock_payload.token_type = "access"
            mock_token_service.verify_token.return_value = mock_payload

            mock_user.is_active = False  # Deactivated user
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo
            mock_repo.get_by_id.return_value = mock_user

            response = client.get(
                "/protected",
                headers={"Authorization": "Bearer valid_token"},
            )

            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "deactivated" in response.json()["detail"].lower()

    def test_auth_middleware_loads_user_from_database(
        self, client: TestClient, mock_user: MagicMock
    ) -> None:
        """Test that middleware loads user from database using token's user ID."""
        with (
            patch("app.core.deps.token_service") as mock_token_service,
            patch("app.core.deps.UserRepository") as mock_repo_class,
        ):
            user_id = "550e8400-e29b-41d4-a716-446655440000"
            mock_payload = MagicMock()
            mock_payload.sub = user_id
            mock_payload.token_type = "access"
            mock_token_service.verify_token.return_value = mock_payload

            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo
            mock_repo.get_by_id.return_value = mock_user

            client.get(
                "/protected",
                headers={"Authorization": "Bearer valid_token"},
            )

            # Verify the user was loaded from database with correct UUID
            from uuid import UUID

            mock_repo.get_by_id.assert_called_once()
            call_args = mock_repo.get_by_id.call_args
            assert call_args[0][0] == UUID(user_id)

    def test_auth_middleware_invalid_user_id_format_returns_401(
        self, client: TestClient
    ) -> None:
        """Test that invalid user ID format in token returns 401."""
        with patch("app.core.deps.token_service") as mock_token_service:
            mock_payload = MagicMock()
            mock_payload.sub = "not-a-valid-uuid"
            mock_payload.token_type = "access"
            mock_token_service.verify_token.return_value = mock_payload

            response = client.get(
                "/protected",
                headers={"Authorization": "Bearer token_with_bad_user_id"},
            )

            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Invalid token payload" in response.json()["detail"]


class TestCurrentUserTypeAlias:
    """Tests for the CurrentUser type alias."""

    def test_current_user_type_alias_exists(self) -> None:
        """Test that CurrentUser type alias is defined."""
        from app.core.deps import CurrentUser

        # CurrentUser should be an annotated type
        assert CurrentUser is not None

    def test_current_user_uses_get_current_user_dependency(self) -> None:
        """Test that CurrentUser uses get_current_user as its dependency."""
        from typing import get_args

        from app.core.deps import CurrentUser, get_current_user

        # Get the type arguments from the Annotated type
        args = get_args(CurrentUser)
        # First arg should be User, second should be Depends(get_current_user)
        assert len(args) == 2
        # The dependency should reference get_current_user
        depends_obj = args[1]
        assert depends_obj.dependency == get_current_user
