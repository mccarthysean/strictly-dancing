"""WebSocket location service for real-time location tracking during sessions."""

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


class LocationMessageType(str, Enum):
    """Types of location WebSocket messages."""

    # Location events
    LOCATION_UPDATE = "location_update"
    LOCATION_RECEIVED = "location_received"

    # Connection events
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"

    # Session events
    SESSION_ENDED = "session_ended"


@dataclass
class LocationUpdate:
    """Location update data structure."""

    latitude: float
    longitude: float
    accuracy: float | None = None
    altitude: float | None = None
    heading: float | None = None
    speed: float | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "accuracy": self.accuracy,
            "altitude": self.altitude,
            "heading": self.heading,
            "speed": self.speed,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LocationUpdate:
        """Create LocationUpdate from dictionary."""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.now(UTC)

        return cls(
            latitude=float(data["latitude"]),
            longitude=float(data["longitude"]),
            accuracy=data.get("accuracy"),
            altitude=data.get("altitude"),
            heading=data.get("heading"),
            speed=data.get("speed"),
            timestamp=timestamp,
        )


@dataclass
class LocationMessage:
    """WebSocket location message structure."""

    type: LocationMessageType
    booking_id: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    sender_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary for JSON serialization."""
        return {
            "type": self.type.value,
            "booking_id": self.booking_id,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "sender_id": self.sender_id,
        }


@dataclass
class LocationConnectionInfo:
    """Information about a location WebSocket connection."""

    websocket: WebSocket
    user_id: str
    booking_id: str
    user_role: str  # 'client' or 'host'
    connected_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class LocationWebSocketManager:
    """Manager for location sharing WebSocket connections.

    Handles:
    - Connection lifecycle for active session location tracking
    - Location update broadcasting between participants
    - Redis Pub/Sub for cross-server communication
    - Location history storage via callback
    """

    def __init__(self, redis_url: str | None = None) -> None:
        """Initialize location WebSocket manager.

        Args:
            redis_url: Redis connection URL. Uses settings if not provided.
        """
        self._redis_url = redis_url or get_settings().redis_url
        self._redis: Redis | None = None
        self._pubsub: Any = None
        self._pubsub_task: asyncio.Task[None] | None = None

        # Local connection tracking: booking_id -> list of connections
        self._connections: dict[str, list[LocationConnectionInfo]] = {}

        # Location history for each booking: booking_id -> list of location updates
        self._location_history: dict[str, list[dict[str, Any]]] = {}

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
        booking_id: str,
        user_id: str,
        user_role: str,
    ) -> LocationConnectionInfo:
        """Register a new location WebSocket connection.

        Args:
            websocket: The WebSocket connection.
            booking_id: The booking ID for the active session.
            user_id: The authenticated user ID.
            user_role: The user's role ('client' or 'host').

        Returns:
            LocationConnectionInfo for the new connection.
        """
        await websocket.accept()

        connection = LocationConnectionInfo(
            websocket=websocket,
            user_id=user_id,
            booking_id=booking_id,
            user_role=user_role,
        )

        # Add to local connections
        if booking_id not in self._connections:
            self._connections[booking_id] = []
        self._connections[booking_id].append(connection)

        # Initialize location history for this booking if not exists
        if booking_id not in self._location_history:
            self._location_history[booking_id] = []

        # Subscribe to Redis channel for this booking if not already
        await self._subscribe_to_booking(booking_id)

        # Send connected confirmation
        await self._send_to_connection(
            connection,
            LocationMessage(
                type=LocationMessageType.CONNECTED,
                booking_id=booking_id,
                data={
                    "user_id": user_id,
                    "user_role": user_role,
                },
            ),
        )

        return connection

    async def disconnect(self, connection: LocationConnectionInfo) -> None:
        """Unregister a location WebSocket connection.

        Args:
            connection: The connection to remove.
        """
        booking_id = connection.booking_id
        user_id = connection.user_id

        # Remove from local connections
        if booking_id in self._connections:
            self._connections[booking_id] = [
                c for c in self._connections[booking_id] if c != connection
            ]

            # Clean up empty booking
            if not self._connections[booking_id]:
                del self._connections[booking_id]
                await self._unsubscribe_from_booking(booking_id)

        # Notify others that user disconnected
        await self.broadcast_to_booking(
            booking_id=booking_id,
            message=LocationMessage(
                type=LocationMessageType.DISCONNECTED,
                booking_id=booking_id,
                data={"user_id": user_id},
                sender_id=user_id,
            ),
            exclude_user_id=user_id,
        )

    async def handle_location_update(
        self,
        booking_id: str,
        user_id: str,
        location: LocationUpdate,
    ) -> None:
        """Handle a location update from a user.

        Stores the location in history and broadcasts to other participant.

        Args:
            booking_id: The booking ID.
            user_id: The user sending the location update.
            location: The location update data.
        """
        # Store in location history
        history_entry = {
            "user_id": user_id,
            "location": location.to_dict(),
            "received_at": datetime.now(UTC).isoformat(),
        }

        if booking_id in self._location_history:
            self._location_history[booking_id].append(history_entry)
            # Keep only last 100 entries per booking to prevent memory issues
            if len(self._location_history[booking_id]) > 100:
                self._location_history[booking_id] = self._location_history[booking_id][
                    -100:
                ]

        # Broadcast to other participants
        await self.broadcast_to_booking(
            booking_id=booking_id,
            message=LocationMessage(
                type=LocationMessageType.LOCATION_RECEIVED,
                booking_id=booking_id,
                data={
                    "user_id": user_id,
                    "location": location.to_dict(),
                },
                sender_id=user_id,
            ),
            exclude_user_id=user_id,
        )

    async def broadcast_to_booking(
        self,
        booking_id: str,
        message: LocationMessage,
        exclude_user_id: str | None = None,
    ) -> None:
        """Broadcast a message to all users connected to a booking.

        Uses Redis Pub/Sub for cross-server communication.

        Args:
            booking_id: The booking to broadcast to.
            message: The message to send.
            exclude_user_id: Optional user ID to exclude from broadcast.
        """
        redis = await self._get_redis()

        # Publish to Redis for cross-server broadcasting
        channel = f"location:{booking_id}"
        payload = {
            **message.to_dict(),
            "exclude_user_id": exclude_user_id,
        }
        await redis.publish(channel, json.dumps(payload))

    async def _handle_redis_message(
        self,
        booking_id: str,
        payload: dict[str, Any],
    ) -> None:
        """Handle a message received from Redis Pub/Sub.

        Args:
            booking_id: The booking ID.
            payload: The message payload from Redis.
        """
        exclude_user_id = payload.pop("exclude_user_id", None)

        message = LocationMessage(
            type=LocationMessageType(payload["type"]),
            booking_id=payload["booking_id"],
            data=payload.get("data", {}),
            timestamp=datetime.fromisoformat(payload["timestamp"]),
            sender_id=payload.get("sender_id"),
        )

        # Send to all local connections for this booking
        await self._send_to_booking_local(
            booking_id,
            message,
            exclude_user_id=exclude_user_id,
        )

    async def _send_to_booking_local(
        self,
        booking_id: str,
        message: LocationMessage,
        exclude_user_id: str | None = None,
    ) -> None:
        """Send message to local connections only.

        Args:
            booking_id: The booking ID.
            message: The message to send.
            exclude_user_id: Optional user ID to exclude.
        """
        if booking_id not in self._connections:
            return

        for connection in self._connections[booking_id]:
            if exclude_user_id and connection.user_id == exclude_user_id:
                continue

            await self._send_to_connection(connection, message)

    async def _send_to_connection(
        self,
        connection: LocationConnectionInfo,
        message: LocationMessage,
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

    async def _subscribe_to_booking(self, booking_id: str) -> None:
        """Subscribe to Redis Pub/Sub channel for a booking.

        Args:
            booking_id: The booking ID to subscribe to.
        """
        redis = await self._get_redis()
        if self._pubsub is None:
            self._pubsub = redis.pubsub()

        channel = f"location:{booking_id}"
        await self._pubsub.subscribe(channel)

        # Start pubsub listener if not already running
        if self._pubsub_task is None or self._pubsub_task.done():
            self._pubsub_task = asyncio.create_task(self._pubsub_listener())

    async def _unsubscribe_from_booking(self, booking_id: str) -> None:
        """Unsubscribe from Redis Pub/Sub channel.

        Args:
            booking_id: The booking ID to unsubscribe from.
        """
        if self._pubsub is not None:
            channel = f"location:{booking_id}"
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

                    # Extract booking_id from channel name
                    if channel.startswith("location:"):
                        booking_id = channel[9:]
                        data = message["data"]
                        if isinstance(data, bytes):
                            data = data.decode("utf-8")
                        payload = json.loads(data)
                        await self._handle_redis_message(booking_id, payload)
        except asyncio.CancelledError:
            pass
        except Exception:
            # Log error but continue listening
            pass

    def get_location_history(self, booking_id: str) -> list[dict[str, Any]]:
        """Get location history for a booking.

        Args:
            booking_id: The booking ID.

        Returns:
            List of location history entries.
        """
        return self._location_history.get(booking_id, []).copy()

    def clear_location_history(self, booking_id: str) -> None:
        """Clear location history for a booking.

        Args:
            booking_id: The booking ID.
        """
        if booking_id in self._location_history:
            del self._location_history[booking_id]

    def get_connected_users(self, booking_id: str) -> list[dict[str, str]]:
        """Get list of users connected to a booking's location sharing.

        Args:
            booking_id: The booking ID.

        Returns:
            List of user info dicts with user_id and user_role.
        """
        if booking_id not in self._connections:
            return []
        return [
            {"user_id": c.user_id, "user_role": c.user_role}
            for c in self._connections[booking_id]
        ]

    async def notify_session_ended(self, booking_id: str) -> None:
        """Notify all connections that the session has ended.

        Args:
            booking_id: The booking ID.
        """
        await self.broadcast_to_booking(
            booking_id=booking_id,
            message=LocationMessage(
                type=LocationMessageType.SESSION_ENDED,
                booking_id=booking_id,
                data={"message": "Session has ended"},
            ),
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


def _create_location_websocket_manager() -> LocationWebSocketManager:
    """Create location WebSocket manager from application settings."""
    return LocationWebSocketManager()


# Singleton instance
location_websocket_manager = _create_location_websocket_manager()


async def verify_location_websocket_token(token: str) -> UUID | None:
    """Verify a JWT token for location WebSocket authentication.

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
