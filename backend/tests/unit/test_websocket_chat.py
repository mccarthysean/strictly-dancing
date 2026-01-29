"""Tests for WebSocket chat functionality."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import WebSocket

from app.services.websocket import (
    ConnectionInfo,
    WebSocketManager,
    WebSocketMessage,
    WebSocketMessageType,
    verify_websocket_token,
)


class TestWebSocketMessageType:
    """Tests for WebSocketMessageType enum."""

    def test_message_type_values(self) -> None:
        """Test message type string values."""
        assert WebSocketMessageType.MESSAGE.value == "message"
        assert WebSocketMessageType.MESSAGE_SENT.value == "message_sent"
        assert WebSocketMessageType.MESSAGE_RECEIVED.value == "message_received"
        assert WebSocketMessageType.MESSAGES_READ.value == "messages_read"
        assert WebSocketMessageType.TYPING_START.value == "typing_start"
        assert WebSocketMessageType.TYPING_STOP.value == "typing_stop"
        assert WebSocketMessageType.CONNECTED.value == "connected"
        assert WebSocketMessageType.DISCONNECTED.value == "disconnected"
        assert WebSocketMessageType.ERROR.value == "error"
        assert WebSocketMessageType.USER_ONLINE.value == "user_online"
        assert WebSocketMessageType.USER_OFFLINE.value == "user_offline"


class TestWebSocketMessage:
    """Tests for WebSocketMessage dataclass."""

    def test_message_creation(self) -> None:
        """Test creating a WebSocket message."""
        conversation_id = str(uuid4())
        message = WebSocketMessage(
            type=WebSocketMessageType.MESSAGE,
            conversation_id=conversation_id,
            data={"content": "Hello"},
            sender_id="user123",
        )

        assert message.type == WebSocketMessageType.MESSAGE
        assert message.conversation_id == conversation_id
        assert message.data == {"content": "Hello"}
        assert message.sender_id == "user123"
        assert message.timestamp is not None

    def test_message_to_dict(self) -> None:
        """Test converting message to dictionary."""
        conversation_id = str(uuid4())
        now = datetime.now(UTC)
        message = WebSocketMessage(
            type=WebSocketMessageType.TYPING_START,
            conversation_id=conversation_id,
            data={"user_id": "user123"},
            timestamp=now,
            sender_id="user123",
        )

        result = message.to_dict()

        assert result["type"] == "typing_start"
        assert result["conversation_id"] == conversation_id
        assert result["data"] == {"user_id": "user123"}
        assert result["timestamp"] == now.isoformat()
        assert result["sender_id"] == "user123"

    def test_message_default_data(self) -> None:
        """Test message with default empty data."""
        message = WebSocketMessage(
            type=WebSocketMessageType.CONNECTED,
            conversation_id="conv123",
        )

        assert message.data == {}


class TestConnectionInfo:
    """Tests for ConnectionInfo dataclass."""

    def test_connection_info_creation(self) -> None:
        """Test creating connection info."""
        websocket = MagicMock(spec=WebSocket)
        connection = ConnectionInfo(
            websocket=websocket,
            user_id="user123",
            conversation_id="conv456",
        )

        assert connection.websocket == websocket
        assert connection.user_id == "user123"
        assert connection.conversation_id == "conv456"
        assert connection.connected_at is not None


class TestWebSocketManager:
    """Tests for WebSocketManager class."""

    @pytest.fixture
    def mock_redis(self) -> MagicMock:
        """Create a mock Redis client."""
        mock = MagicMock()
        mock.publish = AsyncMock(return_value=1)
        mock.close = AsyncMock()
        return mock

    @pytest.fixture
    def mock_pubsub(self) -> MagicMock:
        """Create a mock Redis pubsub."""
        mock = MagicMock()
        mock.subscribe = AsyncMock()
        mock.unsubscribe = AsyncMock()
        mock.close = AsyncMock()
        return mock

    @pytest.fixture
    def manager(self) -> WebSocketManager:
        """Create a WebSocket manager for testing."""
        return WebSocketManager(redis_url="redis://localhost:6379/0")

    @pytest.mark.asyncio
    async def test_connect_adds_connection(
        self,
        manager: WebSocketManager,
        mock_redis: MagicMock,
        mock_pubsub: MagicMock,
    ) -> None:
        """Test that connecting adds a connection to the manager."""
        mock_websocket = AsyncMock(spec=WebSocket)
        conversation_id = "conv123"
        user_id = "user456"

        # Patch Redis
        with patch.object(manager, "_get_redis", return_value=mock_redis):
            mock_redis.pubsub = MagicMock(return_value=mock_pubsub)

            connection = await manager.connect(
                websocket=mock_websocket,
                conversation_id=conversation_id,
                user_id=user_id,
            )

        assert connection.user_id == user_id
        assert connection.conversation_id == conversation_id
        assert conversation_id in manager._connections
        assert connection in manager._connections[conversation_id]
        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_removes_connection(
        self,
        manager: WebSocketManager,
        mock_redis: MagicMock,
        mock_pubsub: MagicMock,
    ) -> None:
        """Test that disconnecting removes the connection."""
        mock_websocket = AsyncMock(spec=WebSocket)
        conversation_id = "conv123"
        user_id = "user456"

        with patch.object(manager, "_get_redis", return_value=mock_redis):
            mock_redis.pubsub = MagicMock(return_value=mock_pubsub)

            # Connect first
            connection = await manager.connect(
                websocket=mock_websocket,
                conversation_id=conversation_id,
                user_id=user_id,
            )

            # Then disconnect
            await manager.disconnect(connection)

        # Connection should be removed
        assert conversation_id not in manager._connections

    @pytest.mark.asyncio
    async def test_multiple_connections_same_conversation(
        self,
        manager: WebSocketManager,
        mock_redis: MagicMock,
        mock_pubsub: MagicMock,
    ) -> None:
        """Test multiple users in the same conversation."""
        mock_ws1 = AsyncMock(spec=WebSocket)
        mock_ws2 = AsyncMock(spec=WebSocket)
        conversation_id = "conv123"

        with patch.object(manager, "_get_redis", return_value=mock_redis):
            mock_redis.pubsub = MagicMock(return_value=mock_pubsub)

            conn1 = await manager.connect(mock_ws1, conversation_id, "user1")
            conn2 = await manager.connect(mock_ws2, conversation_id, "user2")

        assert len(manager._connections[conversation_id]) == 2
        assert conn1 in manager._connections[conversation_id]
        assert conn2 in manager._connections[conversation_id]

    @pytest.mark.asyncio
    async def test_handle_typing_start(
        self,
        manager: WebSocketManager,
        mock_redis: MagicMock,
    ) -> None:
        """Test handling typing start indicator."""
        conversation_id = "conv123"
        user_id = "user456"

        with patch.object(manager, "_get_redis", return_value=mock_redis):
            await manager.handle_typing_start(conversation_id, user_id)

        assert conversation_id in manager._typing_users
        assert user_id in manager._typing_users[conversation_id]
        mock_redis.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_typing_stop(
        self,
        manager: WebSocketManager,
        mock_redis: MagicMock,
    ) -> None:
        """Test handling typing stop indicator."""
        conversation_id = "conv123"
        user_id = "user456"

        # First start typing
        with patch.object(manager, "_get_redis", return_value=mock_redis):
            await manager.handle_typing_start(conversation_id, user_id)
            await manager.handle_typing_stop(conversation_id, user_id)

        assert user_id not in manager._typing_users.get(conversation_id, set())

    def test_get_typing_users_empty(self, manager: WebSocketManager) -> None:
        """Test getting typing users when none are typing."""
        result = manager.get_typing_users("conv123")
        assert result == set()

    def test_get_typing_users(self, manager: WebSocketManager) -> None:
        """Test getting typing users."""
        manager._typing_users["conv123"] = {"user1", "user2"}

        result = manager.get_typing_users("conv123")

        assert result == {"user1", "user2"}
        # Should return a copy
        assert result is not manager._typing_users["conv123"]

    def test_get_online_users_empty(self, manager: WebSocketManager) -> None:
        """Test getting online users when none connected."""
        result = manager.get_online_users("conv123")
        assert result == set()

    @pytest.mark.asyncio
    async def test_get_online_users(
        self,
        manager: WebSocketManager,
        mock_redis: MagicMock,
        mock_pubsub: MagicMock,
    ) -> None:
        """Test getting online users in a conversation."""
        mock_ws1 = AsyncMock(spec=WebSocket)
        mock_ws2 = AsyncMock(spec=WebSocket)
        conversation_id = "conv123"

        with patch.object(manager, "_get_redis", return_value=mock_redis):
            mock_redis.pubsub = MagicMock(return_value=mock_pubsub)

            await manager.connect(mock_ws1, conversation_id, "user1")
            await manager.connect(mock_ws2, conversation_id, "user2")

        result = manager.get_online_users(conversation_id)
        assert result == {"user1", "user2"}

    @pytest.mark.asyncio
    async def test_broadcast_to_conversation_publishes_to_redis(
        self,
        manager: WebSocketManager,
        mock_redis: MagicMock,
    ) -> None:
        """Test that broadcasting publishes to Redis."""
        conversation_id = "conv123"
        message = WebSocketMessage(
            type=WebSocketMessageType.MESSAGE_RECEIVED,
            conversation_id=conversation_id,
            data={"content": "Hello"},
        )

        with patch.object(manager, "_get_redis", return_value=mock_redis):
            await manager.broadcast_to_conversation(
                conversation_id=conversation_id,
                message=message,
            )

        mock_redis.publish.assert_called_once()
        call_args = mock_redis.publish.call_args
        assert call_args[0][0] == f"chat:{conversation_id}"

    @pytest.mark.asyncio
    async def test_send_new_message_notification(
        self,
        manager: WebSocketManager,
        mock_redis: MagicMock,
    ) -> None:
        """Test sending new message notification."""
        conversation_id = "conv123"
        sender_id = "user456"
        message_data = {
            "id": str(uuid4()),
            "content": "Hello!",
            "sender_id": sender_id,
        }

        with patch.object(manager, "_get_redis", return_value=mock_redis):
            await manager.send_new_message_notification(
                conversation_id=conversation_id,
                message_data=message_data,
                sender_id=sender_id,
            )

        mock_redis.publish.assert_called_once()
        call_args = mock_redis.publish.call_args
        payload = json.loads(call_args[0][1])
        assert payload["type"] == WebSocketMessageType.MESSAGE_RECEIVED.value
        assert payload["data"] == message_data
        assert payload["exclude_user_id"] == sender_id

    @pytest.mark.asyncio
    async def test_send_messages_read_notification(
        self,
        manager: WebSocketManager,
        mock_redis: MagicMock,
    ) -> None:
        """Test sending messages read notification."""
        conversation_id = "conv123"
        user_id = "user456"
        read_count = 5

        with patch.object(manager, "_get_redis", return_value=mock_redis):
            await manager.send_messages_read_notification(
                conversation_id=conversation_id,
                user_id=user_id,
                read_count=read_count,
            )

        mock_redis.publish.assert_called_once()
        call_args = mock_redis.publish.call_args
        payload = json.loads(call_args[0][1])
        assert payload["type"] == WebSocketMessageType.MESSAGES_READ.value
        assert payload["data"]["user_id"] == user_id
        assert payload["data"]["read_count"] == read_count

    @pytest.mark.asyncio
    async def test_close_cleans_up_resources(
        self,
        manager: WebSocketManager,
        mock_redis: MagicMock,
        mock_pubsub: MagicMock,
    ) -> None:
        """Test that close cleans up all resources."""
        manager._redis = mock_redis
        manager._pubsub = mock_pubsub
        manager._pubsub_task = None

        await manager.close()

        mock_pubsub.close.assert_called_once()
        mock_redis.close.assert_called_once()


class TestVerifyWebsocketToken:
    """Tests for verify_websocket_token function."""

    @pytest.mark.asyncio
    async def test_verify_valid_token(self) -> None:
        """Test verifying a valid access token."""
        user_id = uuid4()
        mock_payload = MagicMock()
        mock_payload.token_type = "access"
        mock_payload.sub = str(user_id)

        mock_token_service = MagicMock()
        mock_token_service.verify_token.return_value = mock_payload

        with patch(
            "app.services.token.token_service",
            mock_token_service,
        ):
            result = await verify_websocket_token("valid_token")

        assert result == user_id

    @pytest.mark.asyncio
    async def test_verify_refresh_token_rejected(self) -> None:
        """Test that refresh tokens are rejected."""
        mock_payload = MagicMock()
        mock_payload.token_type = "refresh"
        mock_payload.sub = str(uuid4())

        mock_token_service = MagicMock()
        mock_token_service.verify_token.return_value = mock_payload

        with patch(
            "app.services.token.token_service",
            mock_token_service,
        ):
            result = await verify_websocket_token("refresh_token")

        assert result is None

    @pytest.mark.asyncio
    async def test_verify_invalid_token(self) -> None:
        """Test verifying an invalid token."""
        mock_token_service = MagicMock()
        mock_token_service.verify_token.side_effect = ValueError("Invalid token")

        with patch(
            "app.services.token.token_service",
            mock_token_service,
        ):
            result = await verify_websocket_token("invalid_token")

        assert result is None

    @pytest.mark.asyncio
    async def test_verify_expired_token(self) -> None:
        """Test verifying an expired token."""
        mock_token_service = MagicMock()
        mock_token_service.verify_token.side_effect = ValueError("Token has expired")

        with patch(
            "app.services.token.token_service",
            mock_token_service,
        ):
            result = await verify_websocket_token("expired_token")

        assert result is None


class TestWebSocketMessageHandling:
    """Tests for WebSocket message handling logic."""

    @pytest.mark.asyncio
    async def test_handle_redis_message(self) -> None:
        """Test handling a message from Redis Pub/Sub."""
        manager = WebSocketManager(redis_url="redis://localhost:6379/0")
        conversation_id = "conv123"

        mock_ws = AsyncMock(spec=WebSocket)
        connection = ConnectionInfo(
            websocket=mock_ws,
            user_id="user1",
            conversation_id=conversation_id,
        )
        manager._connections[conversation_id] = [connection]

        payload = {
            "type": "message_received",
            "conversation_id": conversation_id,
            "data": {"content": "Hello"},
            "timestamp": datetime.now(UTC).isoformat(),
            "sender_id": "user2",
            "exclude_user_id": "user2",
        }

        await manager._handle_redis_message(conversation_id, payload)

        # User1 should receive the message (not excluded)
        mock_ws.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_redis_message_excludes_sender(self) -> None:
        """Test that Redis message excludes specified user."""
        manager = WebSocketManager(redis_url="redis://localhost:6379/0")
        conversation_id = "conv123"

        mock_ws = AsyncMock(spec=WebSocket)
        connection = ConnectionInfo(
            websocket=mock_ws,
            user_id="user2",  # Same as exclude_user_id
            conversation_id=conversation_id,
        )
        manager._connections[conversation_id] = [connection]

        payload = {
            "type": "message_received",
            "conversation_id": conversation_id,
            "data": {"content": "Hello"},
            "timestamp": datetime.now(UTC).isoformat(),
            "sender_id": "user2",
            "exclude_user_id": "user2",
        }

        await manager._handle_redis_message(conversation_id, payload)

        # User2 should NOT receive the message (excluded)
        mock_ws.send_json.assert_not_called()


class TestWebSocketEndpointBehavior:
    """Tests for WebSocket endpoint behavior."""

    def test_message_type_from_string(self) -> None:
        """Test creating message type from string."""
        assert WebSocketMessageType("message") == WebSocketMessageType.MESSAGE
        assert WebSocketMessageType("typing_start") == WebSocketMessageType.TYPING_START

    def test_message_serialization_roundtrip(self) -> None:
        """Test message can be serialized and deserialized."""
        original = WebSocketMessage(
            type=WebSocketMessageType.MESSAGE_RECEIVED,
            conversation_id="conv123",
            data={"id": "msg1", "content": "Hello"},
            sender_id="user456",
        )

        as_dict = original.to_dict()
        json_str = json.dumps(as_dict)
        parsed = json.loads(json_str)

        assert parsed["type"] == "message_received"
        assert parsed["conversation_id"] == "conv123"
        assert parsed["data"]["content"] == "Hello"
        assert parsed["sender_id"] == "user456"

    def test_connection_info_immutable_fields(self) -> None:
        """Test connection info fields are set correctly."""
        mock_ws = MagicMock(spec=WebSocket)
        now = datetime.now(UTC)

        conn = ConnectionInfo(
            websocket=mock_ws,
            user_id="user123",
            conversation_id="conv456",
            connected_at=now,
        )

        assert conn.user_id == "user123"
        assert conn.conversation_id == "conv456"
        assert conn.connected_at == now


class TestWebSocketManagerConnectionTracking:
    """Tests for WebSocket manager connection tracking."""

    def test_connections_initially_empty(self) -> None:
        """Test that connections start empty."""
        manager = WebSocketManager(redis_url="redis://localhost:6379/0")
        assert manager._connections == {}

    def test_typing_users_initially_empty(self) -> None:
        """Test that typing users start empty."""
        manager = WebSocketManager(redis_url="redis://localhost:6379/0")
        assert manager._typing_users == {}

    @pytest.mark.asyncio
    async def test_disconnect_clears_typing_state(self) -> None:
        """Test that disconnecting clears typing state."""
        manager = WebSocketManager(redis_url="redis://localhost:6379/0")
        conversation_id = "conv123"
        user_id = "user456"

        # Set up connection manually
        mock_ws = AsyncMock(spec=WebSocket)
        connection = ConnectionInfo(
            websocket=mock_ws,
            user_id=user_id,
            conversation_id=conversation_id,
        )
        manager._connections[conversation_id] = [connection]
        manager._typing_users[conversation_id] = {user_id}

        # Mock Redis for broadcast
        mock_redis = AsyncMock()
        mock_redis.publish = AsyncMock()

        with (
            patch.object(manager, "_get_redis", return_value=mock_redis),
            patch.object(manager, "_unsubscribe_from_conversation", return_value=None),
        ):
            await manager.disconnect(connection)

        # Typing state should be cleared
        assert user_id not in manager._typing_users.get(conversation_id, set())

    @pytest.mark.asyncio
    async def test_multiple_conversations_isolated(self) -> None:
        """Test that different conversations are isolated."""
        manager = WebSocketManager(redis_url="redis://localhost:6379/0")

        # Set up connections for two conversations
        mock_ws1 = AsyncMock(spec=WebSocket)
        mock_ws2 = AsyncMock(spec=WebSocket)

        conn1 = ConnectionInfo(
            websocket=mock_ws1,
            user_id="user1",
            conversation_id="conv1",
        )
        conn2 = ConnectionInfo(
            websocket=mock_ws2,
            user_id="user2",
            conversation_id="conv2",
        )

        manager._connections["conv1"] = [conn1]
        manager._connections["conv2"] = [conn2]

        # Get online users for each conversation
        assert manager.get_online_users("conv1") == {"user1"}
        assert manager.get_online_users("conv2") == {"user2"}
