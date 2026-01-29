"""Unit tests for push notification router."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient

from app.core.deps import get_current_user
from app.main import app
from app.models.push_token import DevicePlatform, PushToken


@pytest.fixture
def mock_user():
    """Create a mock authenticated user."""
    user = MagicMock()
    user.id = str(uuid4())
    user.email = "test@example.com"
    user.first_name = "Test"
    user.last_name = "User"
    user.is_active = True
    return user


@pytest.fixture
def auth_headers():
    """Create mock authentication headers."""
    return {"Authorization": "Bearer mock-test-token"}


@pytest.fixture
async def client():
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def authenticated_client(mock_user):
    """Create an async test client with authentication."""
    app.dependency_overrides[get_current_user] = lambda: mock_user
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


class TestRegisterPushTokenEndpoint:
    """Tests for POST /api/v1/push/register endpoint."""

    @pytest.mark.asyncio
    async def test_register_endpoint_exists(self, authenticated_client):
        """The register endpoint should exist and be reachable."""
        with patch("app.routers.push.PushNotificationService") as mock_service_class:
            mock_service = MagicMock()
            mock_token = MagicMock(spec=PushToken)
            mock_token.id = str(uuid4())
            mock_token.token = "ExponentPushToken[test123]"
            mock_token.platform = DevicePlatform.IOS
            mock_token.device_id = "device-123"
            mock_token.device_name = "iPhone"
            mock_token.is_active = True

            mock_service.register_token = AsyncMock(return_value=mock_token)
            mock_service_class.return_value = mock_service

            response = await authenticated_client.post(
                "/api/v1/push/register",
                json={
                    "token": "ExponentPushToken[test123]",
                    "platform": "ios",
                    "device_id": "device-123",
                    "device_name": "iPhone",
                },
            )

        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.asyncio
    async def test_register_returns_token_response(self, authenticated_client):
        """Successful registration should return token details."""
        token_id = str(uuid4())

        with patch("app.routers.push.PushNotificationService") as mock_service_class:
            mock_service = MagicMock()
            mock_token = MagicMock(spec=PushToken)
            mock_token.id = token_id
            mock_token.token = "ExponentPushToken[newtoken456]"
            mock_token.platform = DevicePlatform.ANDROID
            mock_token.device_id = "android-device"
            mock_token.device_name = "Pixel 8"
            mock_token.is_active = True

            mock_service.register_token = AsyncMock(return_value=mock_token)
            mock_service_class.return_value = mock_service

            response = await authenticated_client.post(
                "/api/v1/push/register",
                json={
                    "token": "ExponentPushToken[newtoken456]",
                    "platform": "android",
                    "device_id": "android-device",
                    "device_name": "Pixel 8",
                },
            )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["id"] == token_id
        assert data["token"] == "ExponentPushToken[newtoken456]"
        assert data["platform"] == "android"
        assert data["device_id"] == "android-device"
        assert data["device_name"] == "Pixel 8"
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_register_invalid_token_format(self, authenticated_client):
        """Invalid token format should return 422."""
        response = await authenticated_client.post(
            "/api/v1/push/register",
            json={
                "token": "invalid-token-format",
                "platform": "ios",
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_register_requires_authentication(self, client):
        """Register endpoint should require authentication."""
        response = await client.post(
            "/api/v1/push/register",
            json={
                "token": "ExponentPushToken[test]",
                "platform": "ios",
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_register_service_error(self, authenticated_client):
        """Service error should return 400."""
        with patch("app.routers.push.PushNotificationService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.register_token = AsyncMock(
                side_effect=ValueError("Invalid token")
            )
            mock_service_class.return_value = mock_service

            response = await authenticated_client.post(
                "/api/v1/push/register",
                json={
                    "token": "ExponentPushToken[badtoken]",
                    "platform": "ios",
                },
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestUnregisterPushTokenEndpoint:
    """Tests for POST /api/v1/push/unregister endpoint."""

    @pytest.mark.asyncio
    async def test_unregister_endpoint_exists(self, authenticated_client):
        """The unregister endpoint should exist."""
        with patch("app.routers.push.PushNotificationService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.unregister_token = AsyncMock(return_value=True)
            mock_service_class.return_value = mock_service

            response = await authenticated_client.post(
                "/api/v1/push/unregister",
                json={"token": "ExponentPushToken[tokentoremove]"},
            )

        assert response.status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.asyncio
    async def test_unregister_requires_authentication(self, client):
        """Unregister endpoint should require authentication."""
        response = await client.post(
            "/api/v1/push/unregister",
            json={"token": "ExponentPushToken[test]"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetPushTokensEndpoint:
    """Tests for GET /api/v1/push/tokens endpoint."""

    @pytest.mark.asyncio
    async def test_get_tokens_endpoint_exists(self, authenticated_client):
        """The get tokens endpoint should exist."""
        with patch("app.routers.push.PushNotificationService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_user_tokens = AsyncMock(return_value=[])
            mock_service_class.return_value = mock_service

            response = await authenticated_client.get("/api/v1/push/tokens")

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_get_tokens_returns_list(self, authenticated_client):
        """Should return list of user's tokens."""
        token_id = str(uuid4())

        with patch("app.routers.push.PushNotificationService") as mock_service_class:
            mock_service = MagicMock()
            mock_token = MagicMock(spec=PushToken)
            mock_token.id = token_id
            mock_token.token = "ExponentPushToken[usertoken]"
            mock_token.platform = DevicePlatform.IOS
            mock_token.device_id = "device-1"
            mock_token.device_name = "iPhone"
            mock_token.is_active = True

            mock_service.get_user_tokens = AsyncMock(return_value=[mock_token])
            mock_service_class.return_value = mock_service

            response = await authenticated_client.get("/api/v1/push/tokens")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["count"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == token_id

    @pytest.mark.asyncio
    async def test_get_tokens_requires_authentication(self, client):
        """Get tokens endpoint should require authentication."""
        response = await client.get("/api/v1/push/tokens")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestDeletePushTokenEndpoint:
    """Tests for DELETE /api/v1/push/tokens/{token_id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_token_endpoint_exists(self, mock_user):
        """The delete token endpoint should exist."""
        token_id = str(uuid4())

        from app.core.database import get_db

        mock_db = AsyncMock()
        mock_token = MagicMock(spec=PushToken)
        mock_token.id = token_id
        mock_token.user_id = mock_user.id
        mock_token.is_active = True

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_token
        mock_db.execute.return_value = mock_result
        mock_db.flush = AsyncMock()

        async def mock_db_dep():
            yield mock_db

        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = mock_db_dep

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.delete(f"/api/v1/push/tokens/{token_id}")

        app.dependency_overrides.clear()

        # Token found and deactivated
        assert response.status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.asyncio
    async def test_delete_token_requires_authentication(self, client):
        """Delete token endpoint should require authentication."""
        token_id = str(uuid4())

        response = await client.delete(f"/api/v1/push/tokens/{token_id}")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
