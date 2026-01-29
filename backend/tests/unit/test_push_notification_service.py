"""Unit tests for push notification service."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import httpx
import pytest

from app.models.push_token import DevicePlatform, PushToken
from app.services.push_notifications import (
    NotificationData,
    NotificationPriority,
    NotificationResult,
    PushNotificationService,
)


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.fixture
def push_service(mock_db):
    """Create a push notification service instance."""
    return PushNotificationService(mock_db)


class TestPushTokenValidation:
    """Tests for push token validation."""

    def test_valid_exponent_token(self, push_service):
        """Valid ExponentPushToken should pass validation."""
        token = "ExponentPushToken[abc123xyz789]"
        assert push_service._is_valid_expo_token(token) is True

    def test_valid_expo_token(self, push_service):
        """Valid ExpoPushToken should pass validation."""
        token = "ExpoPushToken[xyz789abc123]"
        assert push_service._is_valid_expo_token(token) is True

    def test_invalid_token_no_brackets(self, push_service):
        """Token without brackets should fail."""
        token = "ExponentPushTokenabc123"
        assert push_service._is_valid_expo_token(token) is False

    def test_invalid_token_wrong_prefix(self, push_service):
        """Token with wrong prefix should fail."""
        token = "InvalidToken[abc123]"
        assert push_service._is_valid_expo_token(token) is False

    def test_invalid_token_empty(self, push_service):
        """Empty token should fail."""
        token = ""
        assert push_service._is_valid_expo_token(token) is False


class TestRegisterToken:
    """Tests for registering push tokens."""

    @pytest.mark.asyncio
    async def test_register_new_token(self, push_service, mock_db):
        """Registering a new token should create a PushToken record."""
        user_id = uuid4()
        token = "ExponentPushToken[newtoken123]"

        # Mock no existing token
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        await push_service.register_token(
            user_id=user_id,
            token=token,
            platform=DevicePlatform.IOS,
            device_id="device-123",
            device_name="iPhone 15",
        )

        # Verify token was added to session
        mock_db.add.assert_called_once()
        added_token = mock_db.add.call_args[0][0]
        assert isinstance(added_token, PushToken)
        assert added_token.token == token
        assert added_token.platform == DevicePlatform.IOS
        assert added_token.device_id == "device-123"
        assert added_token.device_name == "iPhone 15"
        assert added_token.is_active is True

    @pytest.mark.asyncio
    async def test_register_invalid_token_raises_error(self, push_service, mock_db):
        """Registering an invalid token should raise ValueError."""
        user_id = uuid4()
        invalid_token = "not-a-valid-token"

        with pytest.raises(ValueError, match="Invalid Expo push token"):
            await push_service.register_token(
                user_id=user_id,
                token=invalid_token,
                platform=DevicePlatform.ANDROID,
            )

    @pytest.mark.asyncio
    async def test_register_existing_token_same_user_updates(
        self, push_service, mock_db
    ):
        """Re-registering a token for the same user should update it."""
        user_id = uuid4()
        token = "ExponentPushToken[existingtoken]"

        # Mock existing token owned by same user
        existing_token = MagicMock(spec=PushToken)
        existing_token.user_id = str(user_id)
        existing_token.is_active = False

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_token
        mock_db.execute.return_value = mock_result

        result = await push_service.register_token(
            user_id=user_id,
            token=token,
            platform=DevicePlatform.IOS,
        )

        # Should update existing token
        assert existing_token.is_active is True
        assert result == existing_token


class TestUnregisterToken:
    """Tests for unregistering push tokens."""

    @pytest.mark.asyncio
    async def test_unregister_existing_token(self, push_service, mock_db):
        """Unregistering an existing token should deactivate it."""
        token = "ExponentPushToken[tokentoremove]"

        # Mock existing token
        existing_token = MagicMock(spec=PushToken)
        existing_token.is_active = True

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_token
        mock_db.execute.return_value = mock_result

        result = await push_service.unregister_token(token)

        assert result is True
        assert existing_token.is_active is False

    @pytest.mark.asyncio
    async def test_unregister_nonexistent_token(self, push_service, mock_db):
        """Unregistering a non-existent token should return False."""
        token = "ExponentPushToken[doesnotexist]"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await push_service.unregister_token(token)

        assert result is False


class TestGetUserTokens:
    """Tests for getting user tokens."""

    @pytest.mark.asyncio
    async def test_get_user_tokens_returns_list(self, push_service, mock_db):
        """Getting user tokens should return a list."""
        user_id = uuid4()

        # Mock tokens
        token1 = MagicMock(spec=PushToken)
        token2 = MagicMock(spec=PushToken)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [token1, token2]
        mock_db.execute.return_value = mock_result

        result = await push_service.get_user_tokens(user_id)

        assert len(result) == 2
        assert token1 in result
        assert token2 in result

    @pytest.mark.asyncio
    async def test_get_user_tokens_empty_list(self, push_service, mock_db):
        """Getting tokens for user with none should return empty list."""
        user_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await push_service.get_user_tokens(user_id)

        assert result == []


class TestSendNotifications:
    """Tests for sending push notifications."""

    @pytest.mark.asyncio
    async def test_send_notification_success(self, push_service):
        """Sending a notification successfully should return success result."""
        token = "ExponentPushToken[validtoken123]"
        notification = NotificationData(
            title="Test Title",
            body="Test body message",
        )

        # Mock successful API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [{"status": "ok", "id": "msg-12345"}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(push_service, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_get_client.return_value = mock_client

            results = await push_service.send_notifications([token], notification)

        assert len(results) == 1
        assert results[0].success is True
        assert results[0].message_id == "msg-12345"
        assert results[0].error is None

    @pytest.mark.asyncio
    async def test_send_notification_device_not_registered(self, push_service, mock_db):
        """DeviceNotRegistered error should deactivate the token."""
        token = "ExponentPushToken[invalidtoken]"
        notification = NotificationData(
            title="Test",
            body="Test",
        )

        # Mock error response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {
                    "status": "error",
                    "message": "Device not registered",
                    "details": {"error": "DeviceNotRegistered"},
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()

        # Mock token lookup for deactivation
        existing_token = MagicMock(spec=PushToken)
        existing_token.is_active = True
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_token
        mock_db.execute.return_value = mock_result

        with patch.object(push_service, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_get_client.return_value = mock_client

            results = await push_service.send_notifications([token], notification)

        assert len(results) == 1
        assert results[0].success is False
        assert results[0].error == "DeviceNotRegistered"
        # Token should be deactivated
        assert existing_token.is_active is False

    @pytest.mark.asyncio
    async def test_send_notification_http_error(self, push_service):
        """HTTP error should return error results for all tokens."""
        tokens = ["ExponentPushToken[token1]", "ExponentPushToken[token2]"]
        notification = NotificationData(
            title="Test",
            body="Test",
        )

        with patch.object(push_service, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.HTTPError("Connection failed")
            mock_get_client.return_value = mock_client

            results = await push_service.send_notifications(tokens, notification)

        assert len(results) == 2
        assert all(r.success is False for r in results)
        assert all("Connection failed" in r.error for r in results)

    @pytest.mark.asyncio
    async def test_send_notification_empty_tokens(self, push_service):
        """Sending to empty token list should return empty results."""
        notification = NotificationData(
            title="Test",
            body="Test",
        )

        results = await push_service.send_notifications([], notification)

        assert results == []

    @pytest.mark.asyncio
    async def test_send_notification_with_all_options(self, push_service):
        """Notification with all options should include them in request."""
        token = "ExponentPushToken[fulloptionstoken]"
        notification = NotificationData(
            title="Full Test",
            body="Test with all options",
            data={"key": "value", "action": "open_screen"},
            sound="default",
            badge=5,
            priority=NotificationPriority.HIGH,
            channel_id="important",
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": [{"status": "ok", "id": "msg-123"}]}
        mock_response.raise_for_status = MagicMock()

        with patch.object(push_service, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_get_client.return_value = mock_client

            await push_service.send_notifications([token], notification)

            # Verify the message sent to API
            call_args = mock_client.post.call_args
            sent_messages = call_args.kwargs["json"]
            assert len(sent_messages) == 1
            msg = sent_messages[0]
            assert msg["to"] == token
            assert msg["title"] == "Full Test"
            assert msg["body"] == "Test with all options"
            assert msg["data"] == {"key": "value", "action": "open_screen"}
            assert msg["sound"] == "default"
            assert msg["badge"] == 5
            assert msg["priority"] == "high"
            assert msg["channelId"] == "important"


class TestSendToUser:
    """Tests for sending notifications to a user."""

    @pytest.mark.asyncio
    async def test_send_to_user_with_tokens(self, push_service, mock_db):
        """Sending to user with tokens should send to all active tokens."""
        user_id = uuid4()
        notification = NotificationData(
            title="Hello",
            body="Message for you",
        )

        # Mock user tokens
        token1 = MagicMock(spec=PushToken)
        token1.token = "ExponentPushToken[usertoken1]"
        token2 = MagicMock(spec=PushToken)
        token2.token = "ExponentPushToken[usertoken2]"

        mock_tokens_result = MagicMock()
        mock_tokens_result.scalars.return_value.all.return_value = [token1, token2]
        mock_db.execute.return_value = mock_tokens_result

        # Mock successful send
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {"status": "ok", "id": "msg-1"},
                {"status": "ok", "id": "msg-2"},
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(push_service, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_get_client.return_value = mock_client

            results = await push_service.send_to_user(user_id, notification)

        assert len(results) == 2
        assert all(r.success for r in results)

    @pytest.mark.asyncio
    async def test_send_to_user_no_tokens(self, push_service, mock_db):
        """Sending to user with no tokens should return empty list."""
        user_id = uuid4()
        notification = NotificationData(
            title="Hello",
            body="Message",
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        results = await push_service.send_to_user(user_id, notification)

        assert results == []


class TestNotificationData:
    """Tests for NotificationData dataclass."""

    def test_notification_data_defaults(self):
        """NotificationData should have sensible defaults."""
        notification = NotificationData(
            title="Test",
            body="Test body",
        )

        assert notification.title == "Test"
        assert notification.body == "Test body"
        assert notification.data is None
        assert notification.sound == "default"
        assert notification.badge is None
        assert notification.priority == NotificationPriority.DEFAULT
        assert notification.channel_id is None

    def test_notification_data_with_all_fields(self):
        """NotificationData should accept all optional fields."""
        notification = NotificationData(
            title="Full Test",
            body="Body",
            data={"foo": "bar"},
            sound="custom",
            badge=10,
            priority=NotificationPriority.HIGH,
            channel_id="alerts",
        )

        assert notification.title == "Full Test"
        assert notification.data == {"foo": "bar"}
        assert notification.sound == "custom"
        assert notification.badge == 10
        assert notification.priority == NotificationPriority.HIGH
        assert notification.channel_id == "alerts"


class TestNotificationResult:
    """Tests for NotificationResult dataclass."""

    def test_notification_result_success(self):
        """NotificationResult should represent success correctly."""
        result = NotificationResult(
            token="ExponentPushToken[test]",
            success=True,
            message_id="msg-123",
        )

        assert result.token == "ExponentPushToken[test]"
        assert result.success is True
        assert result.message_id == "msg-123"
        assert result.error is None

    def test_notification_result_failure(self):
        """NotificationResult should represent failure correctly."""
        result = NotificationResult(
            token="ExponentPushToken[test]",
            success=False,
            error="DeviceNotRegistered",
        )

        assert result.token == "ExponentPushToken[test]"
        assert result.success is False
        assert result.message_id is None
        assert result.error == "DeviceNotRegistered"
