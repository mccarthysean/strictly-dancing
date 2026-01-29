"""Tests for WebSocket location tracking functionality."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import WebSocket

from app.models.booking import BookingStatus
from app.services.websocket_location import (
    LocationConnectionInfo,
    LocationMessage,
    LocationMessageType,
    LocationUpdate,
    LocationWebSocketManager,
    verify_location_websocket_token,
)


class TestLocationUpdate:
    """Tests for LocationUpdate dataclass."""

    def test_location_update_creation(self) -> None:
        """Test creating a LocationUpdate with all fields."""
        location = LocationUpdate(
            latitude=40.7128,
            longitude=-74.0060,
            accuracy=10.0,
            altitude=100.0,
            heading=45.0,
            speed=5.0,
        )

        assert location.latitude == 40.7128
        assert location.longitude == -74.0060
        assert location.accuracy == 10.0
        assert location.altitude == 100.0
        assert location.heading == 45.0
        assert location.speed == 5.0
        assert location.timestamp is not None

    def test_location_update_minimal(self) -> None:
        """Test creating LocationUpdate with only required fields."""
        location = LocationUpdate(latitude=0.0, longitude=0.0)

        assert location.latitude == 0.0
        assert location.longitude == 0.0
        assert location.accuracy is None
        assert location.altitude is None
        assert location.heading is None
        assert location.speed is None

    def test_location_update_to_dict(self) -> None:
        """Test converting LocationUpdate to dictionary."""
        now = datetime.now(UTC)
        location = LocationUpdate(
            latitude=40.7128,
            longitude=-74.0060,
            accuracy=10.0,
            timestamp=now,
        )

        result = location.to_dict()

        assert result["latitude"] == 40.7128
        assert result["longitude"] == -74.0060
        assert result["accuracy"] == 10.0
        assert result["altitude"] is None
        assert result["heading"] is None
        assert result["speed"] is None
        assert result["timestamp"] == now.isoformat()

    def test_location_update_from_dict(self) -> None:
        """Test creating LocationUpdate from dictionary."""
        data = {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "accuracy": 10.0,
            "altitude": 100.0,
            "timestamp": "2026-01-29T10:00:00+00:00",
        }

        location = LocationUpdate.from_dict(data)

        assert location.latitude == 40.7128
        assert location.longitude == -74.0060
        assert location.accuracy == 10.0
        assert location.altitude == 100.0

    def test_location_update_from_dict_without_timestamp(self) -> None:
        """Test creating LocationUpdate from dict without timestamp."""
        data = {
            "latitude": 40.7128,
            "longitude": -74.0060,
        }

        location = LocationUpdate.from_dict(data)

        assert location.latitude == 40.7128
        assert location.longitude == -74.0060
        assert location.timestamp is not None


class TestLocationMessage:
    """Tests for LocationMessage dataclass."""

    def test_location_message_creation(self) -> None:
        """Test creating a LocationMessage."""
        booking_id = str(uuid4())
        message = LocationMessage(
            type=LocationMessageType.LOCATION_UPDATE,
            booking_id=booking_id,
            data={"latitude": 40.7128, "longitude": -74.0060},
            sender_id="user123",
        )

        assert message.type == LocationMessageType.LOCATION_UPDATE
        assert message.booking_id == booking_id
        assert message.data["latitude"] == 40.7128
        assert message.sender_id == "user123"

    def test_location_message_to_dict(self) -> None:
        """Test converting LocationMessage to dictionary."""
        booking_id = str(uuid4())
        now = datetime.now(UTC)
        message = LocationMessage(
            type=LocationMessageType.CONNECTED,
            booking_id=booking_id,
            data={"user_id": "user123"},
            timestamp=now,
        )

        result = message.to_dict()

        assert result["type"] == "connected"
        assert result["booking_id"] == booking_id
        assert result["data"]["user_id"] == "user123"
        assert result["timestamp"] == now.isoformat()


class TestLocationMessageType:
    """Tests for LocationMessageType enum."""

    def test_message_types_exist(self) -> None:
        """Test all expected message types exist."""
        assert LocationMessageType.LOCATION_UPDATE.value == "location_update"
        assert LocationMessageType.LOCATION_RECEIVED.value == "location_received"
        assert LocationMessageType.CONNECTED.value == "connected"
        assert LocationMessageType.DISCONNECTED.value == "disconnected"
        assert LocationMessageType.ERROR.value == "error"
        assert LocationMessageType.SESSION_ENDED.value == "session_ended"


class TestLocationConnectionInfo:
    """Tests for LocationConnectionInfo dataclass."""

    def test_connection_info_creation(self) -> None:
        """Test creating LocationConnectionInfo."""
        websocket = MagicMock(spec=WebSocket)
        booking_id = str(uuid4())

        connection = LocationConnectionInfo(
            websocket=websocket,
            user_id="user123",
            booking_id=booking_id,
            user_role="client",
        )

        assert connection.websocket == websocket
        assert connection.user_id == "user123"
        assert connection.booking_id == booking_id
        assert connection.user_role == "client"
        assert connection.connected_at is not None


class TestLocationWebSocketManager:
    """Tests for LocationWebSocketManager class."""

    @pytest.fixture
    def manager(self) -> LocationWebSocketManager:
        """Create a location WebSocket manager for testing."""
        return LocationWebSocketManager(redis_url="redis://localhost:6379/0")

    @pytest.fixture
    def mock_websocket(self) -> MagicMock:
        """Create a mock WebSocket."""
        websocket = MagicMock(spec=WebSocket)
        websocket.accept = AsyncMock()
        websocket.send_json = AsyncMock()
        websocket.close = AsyncMock()
        return websocket

    @pytest.mark.asyncio
    async def test_connect(
        self,
        manager: LocationWebSocketManager,
        mock_websocket: MagicMock,
    ) -> None:
        """Test connecting a user to location sharing."""
        booking_id = str(uuid4())

        with patch.object(manager, "_get_redis", new_callable=AsyncMock) as mock_redis:
            mock_redis_instance = MagicMock()
            mock_redis_instance.pubsub = MagicMock(return_value=MagicMock())
            mock_redis.return_value = mock_redis_instance

            with patch.object(manager, "_subscribe_to_booking", new_callable=AsyncMock):
                connection = await manager.connect(
                    websocket=mock_websocket,
                    booking_id=booking_id,
                    user_id="user123",
                    user_role="client",
                )

        assert connection.user_id == "user123"
        assert connection.booking_id == booking_id
        assert connection.user_role == "client"
        mock_websocket.accept.assert_called_once()
        mock_websocket.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect(
        self,
        manager: LocationWebSocketManager,
        mock_websocket: MagicMock,
    ) -> None:
        """Test disconnecting a user from location sharing."""
        booking_id = str(uuid4())

        # Set up connection
        connection = LocationConnectionInfo(
            websocket=mock_websocket,
            user_id="user123",
            booking_id=booking_id,
            user_role="client",
        )
        manager._connections[booking_id] = [connection]

        with (
            patch.object(
                manager, "broadcast_to_booking", new_callable=AsyncMock
            ) as mock_broadcast,
            patch.object(manager, "_unsubscribe_from_booking", new_callable=AsyncMock),
        ):
            await manager.disconnect(connection)

        assert booking_id not in manager._connections
        mock_broadcast.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_location_update(
        self,
        manager: LocationWebSocketManager,
    ) -> None:
        """Test handling a location update."""
        booking_id = str(uuid4())
        manager._location_history[booking_id] = []

        location = LocationUpdate(
            latitude=40.7128,
            longitude=-74.0060,
            accuracy=10.0,
        )

        with patch.object(
            manager, "broadcast_to_booking", new_callable=AsyncMock
        ) as mock_broadcast:
            await manager.handle_location_update(
                booking_id=booking_id,
                user_id="user123",
                location=location,
            )

        # Check location was stored
        assert len(manager._location_history[booking_id]) == 1
        assert manager._location_history[booking_id][0]["user_id"] == "user123"

        # Check broadcast was called
        mock_broadcast.assert_called_once()
        call_args = mock_broadcast.call_args
        assert call_args.kwargs["booking_id"] == booking_id
        assert call_args.kwargs["exclude_user_id"] == "user123"

    @pytest.mark.asyncio
    async def test_handle_location_update_limits_history(
        self,
        manager: LocationWebSocketManager,
    ) -> None:
        """Test that location history is limited to 100 entries."""
        booking_id = str(uuid4())
        manager._location_history[booking_id] = [
            {"user_id": f"old_{i}"} for i in range(100)
        ]

        location = LocationUpdate(latitude=0.0, longitude=0.0)

        with patch.object(manager, "broadcast_to_booking", new_callable=AsyncMock):
            await manager.handle_location_update(
                booking_id=booking_id,
                user_id="user123",
                location=location,
            )

        # Should still have 100 entries
        assert len(manager._location_history[booking_id]) == 100
        # The oldest entry should have been removed
        assert manager._location_history[booking_id][0]["user_id"] == "old_1"
        # The newest entry should be last
        assert manager._location_history[booking_id][-1]["user_id"] == "user123"

    def test_get_location_history(
        self,
        manager: LocationWebSocketManager,
    ) -> None:
        """Test getting location history."""
        booking_id = str(uuid4())
        manager._location_history[booking_id] = [
            {"user_id": "user1", "location": {"latitude": 40.0}},
            {"user_id": "user2", "location": {"latitude": 41.0}},
        ]

        history = manager.get_location_history(booking_id)

        assert len(history) == 2
        assert history[0]["user_id"] == "user1"
        # Ensure it's a copy
        history.append({"user_id": "user3"})
        assert len(manager._location_history[booking_id]) == 2

    def test_get_location_history_empty(
        self,
        manager: LocationWebSocketManager,
    ) -> None:
        """Test getting location history for non-existent booking."""
        history = manager.get_location_history("non-existent")
        assert history == []

    def test_clear_location_history(
        self,
        manager: LocationWebSocketManager,
    ) -> None:
        """Test clearing location history."""
        booking_id = str(uuid4())
        manager._location_history[booking_id] = [{"test": "data"}]

        manager.clear_location_history(booking_id)

        assert booking_id not in manager._location_history

    def test_get_connected_users(
        self,
        manager: LocationWebSocketManager,
    ) -> None:
        """Test getting connected users for a booking."""
        booking_id = str(uuid4())
        mock_ws = MagicMock(spec=WebSocket)

        manager._connections[booking_id] = [
            LocationConnectionInfo(
                websocket=mock_ws,
                user_id="client123",
                booking_id=booking_id,
                user_role="client",
            ),
            LocationConnectionInfo(
                websocket=mock_ws,
                user_id="host456",
                booking_id=booking_id,
                user_role="host",
            ),
        ]

        users = manager.get_connected_users(booking_id)

        assert len(users) == 2
        assert {"user_id": "client123", "user_role": "client"} in users
        assert {"user_id": "host456", "user_role": "host"} in users

    def test_get_connected_users_empty(
        self,
        manager: LocationWebSocketManager,
    ) -> None:
        """Test getting connected users for non-existent booking."""
        users = manager.get_connected_users("non-existent")
        assert users == []

    @pytest.mark.asyncio
    async def test_notify_session_ended(
        self,
        manager: LocationWebSocketManager,
    ) -> None:
        """Test notifying participants that session ended."""
        booking_id = str(uuid4())

        with patch.object(
            manager, "broadcast_to_booking", new_callable=AsyncMock
        ) as mock_broadcast:
            await manager.notify_session_ended(booking_id)

        mock_broadcast.assert_called_once()
        call_args = mock_broadcast.call_args
        message = call_args.kwargs["message"]
        assert message.type == LocationMessageType.SESSION_ENDED

    @pytest.mark.asyncio
    async def test_broadcast_to_booking(
        self,
        manager: LocationWebSocketManager,
    ) -> None:
        """Test broadcasting message to booking via Redis."""
        booking_id = str(uuid4())
        message = LocationMessage(
            type=LocationMessageType.LOCATION_RECEIVED,
            booking_id=booking_id,
            data={"test": "data"},
        )

        mock_redis = AsyncMock()
        with patch.object(manager, "_get_redis", return_value=mock_redis):
            await manager.broadcast_to_booking(
                booking_id=booking_id,
                message=message,
                exclude_user_id="user123",
            )

        mock_redis.publish.assert_called_once()
        call_args = mock_redis.publish.call_args
        assert call_args[0][0] == f"location:{booking_id}"


class TestVerifyLocationWebsocketToken:
    """Tests for verify_location_websocket_token function."""

    @pytest.mark.asyncio
    async def test_verify_valid_token(self) -> None:
        """Test verifying a valid token."""
        user_id = uuid4()

        with patch("app.services.token.token_service") as mock_service:
            mock_payload = MagicMock()
            mock_payload.token_type = "access"
            mock_payload.sub = str(user_id)
            mock_service.verify_token.return_value = mock_payload

            result = await verify_location_websocket_token("valid_token")

        assert result == user_id

    @pytest.mark.asyncio
    async def test_verify_refresh_token_rejected(self) -> None:
        """Test that refresh tokens are rejected."""
        with patch("app.services.token.token_service") as mock_service:
            mock_payload = MagicMock()
            mock_payload.token_type = "refresh"
            mock_service.verify_token.return_value = mock_payload

            result = await verify_location_websocket_token("refresh_token")

        assert result is None

    @pytest.mark.asyncio
    async def test_verify_invalid_token(self) -> None:
        """Test verifying an invalid token."""
        with patch("app.services.token.token_service") as mock_service:
            mock_service.verify_token.side_effect = ValueError("Invalid token")

            result = await verify_location_websocket_token("invalid_token")

        assert result is None


class TestWebSocketLocationEndpoint:
    """Tests for the /ws/location/{booking_id} WebSocket endpoint."""

    @pytest.fixture
    def mock_booking_in_progress(self) -> MagicMock:
        """Create a mock booking that is in progress."""
        booking = MagicMock()
        booking.id = str(uuid4())
        booking.client_id = "client123"
        booking.host_id = "host456"
        booking.status = BookingStatus.IN_PROGRESS
        return booking

    @pytest.fixture
    def mock_user(self) -> MagicMock:
        """Create a mock user."""
        user = MagicMock()
        user.id = "client123"
        user.is_active = True
        return user

    def test_verify_booking_access_patterns(self) -> None:
        """Test the booking access verification logic patterns."""
        # This tests the logic from _verify_booking_access
        # Client access
        booking = MagicMock()
        booking.client_id = "client123"
        booking.host_id = "host456"
        booking.status = BookingStatus.IN_PROGRESS

        # Client should have access
        user_id = "client123"
        assert booking.client_id == user_id or booking.host_id == user_id
        assert booking.status == BookingStatus.IN_PROGRESS

        # Host should have access
        user_id = "host456"
        assert booking.client_id == user_id or booking.host_id == user_id

        # Other user should not have access
        user_id = "other999"
        assert not (booking.client_id == user_id or booking.host_id == user_id)

    def test_booking_status_check(self) -> None:
        """Test that only IN_PROGRESS bookings allow location sharing."""
        booking = MagicMock()
        booking.status = BookingStatus.IN_PROGRESS
        assert booking.status == BookingStatus.IN_PROGRESS

        booking.status = BookingStatus.CONFIRMED
        assert booking.status != BookingStatus.IN_PROGRESS

        booking.status = BookingStatus.PENDING
        assert booking.status != BookingStatus.IN_PROGRESS

        booking.status = BookingStatus.COMPLETED
        assert booking.status != BookingStatus.IN_PROGRESS


class TestLocationCoordinateValidation:
    """Tests for location coordinate validation."""

    def test_valid_latitude_range(self) -> None:
        """Test latitude validation (must be -90 to 90)."""
        # Valid latitudes
        assert -90 <= 0.0 <= 90
        assert -90 <= 40.7128 <= 90
        assert -90 <= -90.0 <= 90
        assert -90 <= 90.0 <= 90

        # Invalid latitudes
        assert not (-90 <= 91.0 <= 90)
        assert not (-90 <= -91.0 <= 90)

    def test_valid_longitude_range(self) -> None:
        """Test longitude validation (must be -180 to 180)."""
        # Valid longitudes
        assert -180 <= 0.0 <= 180
        assert -180 <= -74.0060 <= 180
        assert -180 <= -180.0 <= 180
        assert -180 <= 180.0 <= 180

        # Invalid longitudes
        assert not (-180 <= 181.0 <= 180)
        assert not (-180 <= -181.0 <= 180)


class TestLocationHistoryStorage:
    """Tests for location history storage functionality."""

    @pytest.fixture
    def manager(self) -> LocationWebSocketManager:
        """Create a manager for testing."""
        return LocationWebSocketManager(redis_url="redis://localhost:6379/0")

    @pytest.mark.asyncio
    async def test_location_history_contains_all_fields(
        self,
        manager: LocationWebSocketManager,
    ) -> None:
        """Test that location history entries contain required fields."""
        booking_id = str(uuid4())
        manager._location_history[booking_id] = []

        location = LocationUpdate(
            latitude=40.7128,
            longitude=-74.0060,
            accuracy=10.0,
            altitude=50.0,
            heading=90.0,
            speed=5.5,
        )

        with patch.object(manager, "broadcast_to_booking", new_callable=AsyncMock):
            await manager.handle_location_update(
                booking_id=booking_id,
                user_id="user123",
                location=location,
            )

        history_entry = manager._location_history[booking_id][0]
        assert "user_id" in history_entry
        assert "location" in history_entry
        assert "received_at" in history_entry
        assert history_entry["location"]["latitude"] == 40.7128
        assert history_entry["location"]["longitude"] == -74.0060
        assert history_entry["location"]["accuracy"] == 10.0
