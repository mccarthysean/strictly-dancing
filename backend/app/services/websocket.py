"""WebSocket chat service for real-time messaging."""

from __future__ import annotations

import asyncio
import contextlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect
from redis.asyncio import Redis

from app.core.config import get_settings


class WebSocketMessageType(str, Enum):
    """Types of WebSocket messages."""

    # Message events
    MESSAGE = "message"
    MESSAGE_SENT = "message_sent"
    MESSAGE_RECEIVED = "message_received"
    MESSAGES_READ = "messages_read"

    # Typing events
    TYPING_START = "typing_start"
    TYPING_STOP = "typing_stop"

    # Connection events
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"

    # User presence
    USER_ONLINE = "user_online"
    USER_OFFLINE = "user_offline"


@dataclass
class WebSocketMessage:
    """WebSocket message structure."""

    type: WebSocketMessageType
    conversation_id: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    sender_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary for JSON serialization."""
        return {
            "type": self.type.value,
            "conversation_id": self.conversation_id,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "sender_id": self.sender_id,
        }


@dataclass
class ConnectionInfo:
    """Information about a WebSocket connection."""

    websocket: WebSocket
    user_id: str
    conversation_id: str
    connected_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class WebSocketManager:
    """Manager for WebSocket connections and Redis Pub/Sub.

    Handles:
    - Connection lifecycle (connect, disconnect)
    - Message broadcasting within conversations
    - Redis Pub/Sub for cross-server communication
    - Typing indicators
    """

    def __init__(self, redis_url: str | None = None) -> None:
        """Initialize WebSocket manager.

        Args:
            redis_url: Redis connection URL. Uses settings if not provided.
        """
        self._redis_url = redis_url or get_settings().redis_url
        self._redis: Redis | None = None
        self._pubsub: Any = None
        self._pubsub_task: asyncio.Task[None] | None = None

        # Local connection tracking: conversation_id -> list of connections
        self._connections: dict[str, list[ConnectionInfo]] = {}

        # User typing states: conversation_id -> set of user_ids
        self._typing_users: dict[str, set[str]] = {}

    async def _get_redis(self) -> Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            self._redis = Redis.from_url(
                self._redis_url,
                decode_responses=True,
            )
        return self._redis

    async def connect(
        self,
        websocket: WebSocket,
        conversation_id: str,
        user_id: str,
    ) -> ConnectionInfo:
        """Register a new WebSocket connection.

        Args:
            websocket: The WebSocket connection.
            conversation_id: The conversation ID.
            user_id: The authenticated user ID.

        Returns:
            ConnectionInfo for the new connection.
        """
        await websocket.accept()

        connection = ConnectionInfo(
            websocket=websocket,
            user_id=user_id,
            conversation_id=conversation_id,
        )

        # Add to local connections
        if conversation_id not in self._connections:
            self._connections[conversation_id] = []
        self._connections[conversation_id].append(connection)

        # Subscribe to Redis channel for this conversation if not already
        await self._subscribe_to_conversation(conversation_id)

        # Send connected confirmation
        await self._send_to_connection(
            connection,
            WebSocketMessage(
                type=WebSocketMessageType.CONNECTED,
                conversation_id=conversation_id,
                data={"user_id": user_id},
            ),
        )

        # Notify others in conversation that user is online
        await self.broadcast_to_conversation(
            conversation_id=conversation_id,
            message=WebSocketMessage(
                type=WebSocketMessageType.USER_ONLINE,
                conversation_id=conversation_id,
                data={"user_id": user_id},
                sender_id=user_id,
            ),
            exclude_user_id=user_id,
        )

        return connection

    async def disconnect(self, connection: ConnectionInfo) -> None:
        """Unregister a WebSocket connection.

        Args:
            connection: The connection to remove.
        """
        conversation_id = connection.conversation_id
        user_id = connection.user_id

        # Remove from local connections
        if conversation_id in self._connections:
            self._connections[conversation_id] = [
                c for c in self._connections[conversation_id] if c != connection
            ]

            # Clean up empty conversation
            if not self._connections[conversation_id]:
                del self._connections[conversation_id]
                await self._unsubscribe_from_conversation(conversation_id)

        # Clear typing state for user
        if conversation_id in self._typing_users:
            self._typing_users[conversation_id].discard(user_id)
            if not self._typing_users[conversation_id]:
                del self._typing_users[conversation_id]

        # Notify others that user is offline
        await self.broadcast_to_conversation(
            conversation_id=conversation_id,
            message=WebSocketMessage(
                type=WebSocketMessageType.USER_OFFLINE,
                conversation_id=conversation_id,
                data={"user_id": user_id},
                sender_id=user_id,
            ),
            exclude_user_id=user_id,
        )

    async def broadcast_to_conversation(
        self,
        conversation_id: str,
        message: WebSocketMessage,
        exclude_user_id: str | None = None,
    ) -> None:
        """Broadcast a message to all users in a conversation.

        Uses Redis Pub/Sub to reach all server instances.

        Args:
            conversation_id: The conversation to broadcast to.
            message: The message to send.
            exclude_user_id: Optional user ID to exclude from broadcast.
        """
        redis = await self._get_redis()

        # Publish to Redis for cross-server broadcasting
        channel = f"chat:{conversation_id}"
        payload = {
            **message.to_dict(),
            "exclude_user_id": exclude_user_id,
        }
        await redis.publish(channel, json.dumps(payload))

    async def _handle_redis_message(
        self,
        conversation_id: str,
        payload: dict[str, Any],
    ) -> None:
        """Handle a message received from Redis Pub/Sub.

        Args:
            conversation_id: The conversation ID.
            payload: The message payload from Redis.
        """
        exclude_user_id = payload.pop("exclude_user_id", None)

        message = WebSocketMessage(
            type=WebSocketMessageType(payload["type"]),
            conversation_id=payload["conversation_id"],
            data=payload.get("data", {}),
            timestamp=datetime.fromisoformat(payload["timestamp"]),
            sender_id=payload.get("sender_id"),
        )

        # Send to all local connections for this conversation
        await self._send_to_conversation_local(
            conversation_id,
            message,
            exclude_user_id=exclude_user_id,
        )

    async def _send_to_conversation_local(
        self,
        conversation_id: str,
        message: WebSocketMessage,
        exclude_user_id: str | None = None,
    ) -> None:
        """Send message to local connections only.

        Args:
            conversation_id: The conversation ID.
            message: The message to send.
            exclude_user_id: Optional user ID to exclude.
        """
        if conversation_id not in self._connections:
            return

        for connection in self._connections[conversation_id]:
            if exclude_user_id and connection.user_id == exclude_user_id:
                continue

            await self._send_to_connection(connection, message)

    async def _send_to_connection(
        self,
        connection: ConnectionInfo,
        message: WebSocketMessage,
    ) -> None:
        """Send a message to a specific connection.

        Args:
            connection: The connection to send to.
            message: The message to send.
        """
        try:
            await connection.websocket.send_json(message.to_dict())
        except WebSocketDisconnect:
            # Connection was closed, clean up
            await self.disconnect(connection)
        except Exception:
            # Log error but don't fail - connection might be stale
            pass

    async def _subscribe_to_conversation(self, conversation_id: str) -> None:
        """Subscribe to Redis Pub/Sub channel for a conversation.

        Args:
            conversation_id: The conversation ID to subscribe to.
        """
        redis = await self._get_redis()
        if self._pubsub is None:
            self._pubsub = redis.pubsub()

        channel = f"chat:{conversation_id}"
        await self._pubsub.subscribe(channel)

        # Start pubsub listener if not already running
        if self._pubsub_task is None or self._pubsub_task.done():
            self._pubsub_task = asyncio.create_task(self._pubsub_listener())

    async def _unsubscribe_from_conversation(self, conversation_id: str) -> None:
        """Unsubscribe from Redis Pub/Sub channel.

        Args:
            conversation_id: The conversation ID to unsubscribe from.
        """
        if self._pubsub is not None:
            channel = f"chat:{conversation_id}"
            await self._pubsub.unsubscribe(channel)

    async def _pubsub_listener(self) -> None:
        """Listen for Redis Pub/Sub messages and handle them."""
        if self._pubsub is None:
            return

        try:
            async for message in self._pubsub.listen():
                if message["type"] == "message":
                    channel = message["channel"]
                    if isinstance(channel, bytes):
                        channel = channel.decode("utf-8")

                    # Extract conversation_id from channel name
                    if channel.startswith("chat:"):
                        conversation_id = channel[5:]
                        data = message["data"]
                        if isinstance(data, bytes):
                            data = data.decode("utf-8")
                        payload = json.loads(data)
                        await self._handle_redis_message(conversation_id, payload)
        except asyncio.CancelledError:
            pass
        except Exception:
            # Log error but continue listening
            pass

    async def handle_typing_start(
        self,
        conversation_id: str,
        user_id: str,
    ) -> None:
        """Handle user starting to type.

        Args:
            conversation_id: The conversation ID.
            user_id: The typing user ID.
        """
        if conversation_id not in self._typing_users:
            self._typing_users[conversation_id] = set()

        self._typing_users[conversation_id].add(user_id)

        await self.broadcast_to_conversation(
            conversation_id=conversation_id,
            message=WebSocketMessage(
                type=WebSocketMessageType.TYPING_START,
                conversation_id=conversation_id,
                data={"user_id": user_id},
                sender_id=user_id,
            ),
            exclude_user_id=user_id,
        )

    async def handle_typing_stop(
        self,
        conversation_id: str,
        user_id: str,
    ) -> None:
        """Handle user stopping typing.

        Args:
            conversation_id: The conversation ID.
            user_id: The user who stopped typing.
        """
        if conversation_id in self._typing_users:
            self._typing_users[conversation_id].discard(user_id)

        await self.broadcast_to_conversation(
            conversation_id=conversation_id,
            message=WebSocketMessage(
                type=WebSocketMessageType.TYPING_STOP,
                conversation_id=conversation_id,
                data={"user_id": user_id},
                sender_id=user_id,
            ),
            exclude_user_id=user_id,
        )

    def get_typing_users(self, conversation_id: str) -> set[str]:
        """Get the set of users currently typing in a conversation.

        Args:
            conversation_id: The conversation ID.

        Returns:
            Set of user IDs currently typing.
        """
        return self._typing_users.get(conversation_id, set()).copy()

    def get_online_users(self, conversation_id: str) -> set[str]:
        """Get the set of online users in a conversation.

        Args:
            conversation_id: The conversation ID.

        Returns:
            Set of user IDs currently online in the conversation.
        """
        if conversation_id not in self._connections:
            return set()
        return {c.user_id for c in self._connections[conversation_id]}

    async def send_new_message_notification(
        self,
        conversation_id: str,
        message_data: dict[str, Any],
        sender_id: str,
    ) -> None:
        """Send a new message notification to conversation participants.

        Args:
            conversation_id: The conversation ID.
            message_data: The message data to include.
            sender_id: The sender's user ID.
        """
        await self.broadcast_to_conversation(
            conversation_id=conversation_id,
            message=WebSocketMessage(
                type=WebSocketMessageType.MESSAGE_RECEIVED,
                conversation_id=conversation_id,
                data=message_data,
                sender_id=sender_id,
            ),
            exclude_user_id=sender_id,
        )

    async def send_messages_read_notification(
        self,
        conversation_id: str,
        user_id: str,
        read_count: int,
    ) -> None:
        """Notify conversation that messages were read.

        Args:
            conversation_id: The conversation ID.
            user_id: The user who read messages.
            read_count: Number of messages marked as read.
        """
        await self.broadcast_to_conversation(
            conversation_id=conversation_id,
            message=WebSocketMessage(
                type=WebSocketMessageType.MESSAGES_READ,
                conversation_id=conversation_id,
                data={
                    "user_id": user_id,
                    "read_count": read_count,
                },
                sender_id=user_id,
            ),
            exclude_user_id=user_id,
        )

    async def close(self) -> None:
        """Clean up resources when shutting down."""
        # Cancel pubsub listener
        if self._pubsub_task is not None:
            self._pubsub_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._pubsub_task

        # Close pubsub connection
        if self._pubsub is not None:
            await self._pubsub.close()

        # Close Redis connection
        if self._redis is not None:
            await self._redis.close()


def _create_websocket_manager() -> WebSocketManager:
    """Create WebSocket manager from application settings."""
    return WebSocketManager()


# Singleton instance
websocket_manager = _create_websocket_manager()


async def verify_websocket_token(token: str) -> UUID | None:
    """Verify a JWT token for WebSocket authentication.

    WebSocket connections pass the token as a query parameter since
    they can't use Authorization headers in the same way as HTTP.

    Args:
        token: The JWT access token.

    Returns:
        The user ID if valid, None otherwise.
    """
    from app.services.token import token_service

    try:
        payload = token_service.verify_token(token)
        if payload.token_type != "access":
            return None
        return UUID(payload.sub)
    except (ValueError, TypeError):
        return None
