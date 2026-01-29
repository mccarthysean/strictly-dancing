"""Tests for push notification triggers.

This module tests that push notifications are sent correctly
when key events occur in the application.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.booking import Booking, BookingStatus
from app.services.notification_triggers import (
    NotificationTriggerService,
    get_notification_trigger_service,
)
from app.services.push_notifications import NotificationResult


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return AsyncMock()


@pytest.fixture
def notification_service(mock_db):
    """Create a NotificationTriggerService instance with mocked push service."""
    service = NotificationTriggerService(mock_db)
    service._push_service = AsyncMock()
    return service


@pytest.fixture
def sample_booking():
    """Create a sample booking for testing."""
    booking = MagicMock(spec=Booking)
    booking.id = uuid4()
    booking.client_id = str(uuid4())
    booking.host_id = str(uuid4())
    booking.status = BookingStatus.PENDING
    booking.scheduled_start = datetime.now(UTC) + timedelta(hours=2)
    booking.scheduled_end = booking.scheduled_start + timedelta(hours=1)
    return booking


class TestOnBookingCreated:
    """Tests for new booking notification to host."""

    @pytest.mark.asyncio
    async def test_sends_notification_to_host(
        self, notification_service, sample_booking
    ):
        """Test that notification is sent to the host when booking is created."""
        notification_service._push_service.send_to_user = AsyncMock(
            return_value=[NotificationResult(token="test", success=True)]
        )

        await notification_service.on_booking_created(
            booking=sample_booking,
            client_name="John Doe",
            dance_style_name="Salsa",
        )

        notification_service._push_service.send_to_user.assert_called_once()
        call_args = notification_service._push_service.send_to_user.call_args
        assert str(call_args[0][0]) == sample_booking.host_id

    @pytest.mark.asyncio
    async def test_notification_contains_correct_title(
        self, notification_service, sample_booking
    ):
        """Test that notification has correct title."""
        notification_service._push_service.send_to_user = AsyncMock(return_value=[])

        await notification_service.on_booking_created(
            booking=sample_booking,
            client_name="John Doe",
        )

        call_args = notification_service._push_service.send_to_user.call_args
        notification = call_args[0][1]
        assert notification.title == "New Booking Request"

    @pytest.mark.asyncio
    async def test_notification_contains_client_name(
        self, notification_service, sample_booking
    ):
        """Test that notification body contains client name."""
        notification_service._push_service.send_to_user = AsyncMock(return_value=[])

        await notification_service.on_booking_created(
            booking=sample_booking,
            client_name="Jane Smith",
        )

        call_args = notification_service._push_service.send_to_user.call_args
        notification = call_args[0][1]
        assert "Jane Smith" in notification.body

    @pytest.mark.asyncio
    async def test_notification_contains_dance_style(
        self, notification_service, sample_booking
    ):
        """Test that notification body contains dance style when provided."""
        notification_service._push_service.send_to_user = AsyncMock(return_value=[])

        await notification_service.on_booking_created(
            booking=sample_booking,
            client_name="John Doe",
            dance_style_name="Bachata",
        )

        call_args = notification_service._push_service.send_to_user.call_args
        notification = call_args[0][1]
        assert "Bachata" in notification.body

    @pytest.mark.asyncio
    async def test_notification_data_contains_booking_id(
        self, notification_service, sample_booking
    ):
        """Test that notification data contains booking ID."""
        notification_service._push_service.send_to_user = AsyncMock(return_value=[])

        await notification_service.on_booking_created(
            booking=sample_booking,
            client_name="John Doe",
        )

        call_args = notification_service._push_service.send_to_user.call_args
        notification = call_args[0][1]
        assert notification.data["booking_id"] == str(sample_booking.id)
        assert notification.data["type"] == "booking_created"


class TestOnBookingConfirmed:
    """Tests for booking confirmed notification to client."""

    @pytest.mark.asyncio
    async def test_sends_notification_to_client(
        self, notification_service, sample_booking
    ):
        """Test that notification is sent to the client when booking is confirmed."""
        notification_service._push_service.send_to_user = AsyncMock(
            return_value=[NotificationResult(token="test", success=True)]
        )

        await notification_service.on_booking_confirmed(
            booking=sample_booking,
            host_name="Maria Garcia",
        )

        notification_service._push_service.send_to_user.assert_called_once()
        call_args = notification_service._push_service.send_to_user.call_args
        assert str(call_args[0][0]) == sample_booking.client_id

    @pytest.mark.asyncio
    async def test_notification_contains_correct_title(
        self, notification_service, sample_booking
    ):
        """Test that notification has correct title."""
        notification_service._push_service.send_to_user = AsyncMock(return_value=[])

        await notification_service.on_booking_confirmed(
            booking=sample_booking,
            host_name="Maria Garcia",
        )

        call_args = notification_service._push_service.send_to_user.call_args
        notification = call_args[0][1]
        assert notification.title == "Booking Confirmed!"

    @pytest.mark.asyncio
    async def test_notification_contains_host_name(
        self, notification_service, sample_booking
    ):
        """Test that notification body contains host name."""
        notification_service._push_service.send_to_user = AsyncMock(return_value=[])

        await notification_service.on_booking_confirmed(
            booking=sample_booking,
            host_name="Carlos Rodriguez",
        )

        call_args = notification_service._push_service.send_to_user.call_args
        notification = call_args[0][1]
        assert "Carlos Rodriguez" in notification.body

    @pytest.mark.asyncio
    async def test_notification_data_contains_booking_id(
        self, notification_service, sample_booking
    ):
        """Test that notification data contains booking ID."""
        notification_service._push_service.send_to_user = AsyncMock(return_value=[])

        await notification_service.on_booking_confirmed(
            booking=sample_booking,
            host_name="Maria Garcia",
        )

        call_args = notification_service._push_service.send_to_user.call_args
        notification = call_args[0][1]
        assert notification.data["booking_id"] == str(sample_booking.id)
        assert notification.data["type"] == "booking_confirmed"


class TestOnNewMessage:
    """Tests for new message notification."""

    @pytest.mark.asyncio
    async def test_sends_notification_to_recipient(self, notification_service):
        """Test that notification is sent to the message recipient."""
        notification_service._push_service.send_to_user = AsyncMock(
            return_value=[NotificationResult(token="test", success=True)]
        )
        recipient_id = uuid4()

        await notification_service.on_new_message(
            conversation_id=uuid4(),
            sender_name="Alice",
            message_preview="Hey, are you available for a session tomorrow?",
            recipient_id=recipient_id,
        )

        notification_service._push_service.send_to_user.assert_called_once()
        call_args = notification_service._push_service.send_to_user.call_args
        assert call_args[0][0] == recipient_id

    @pytest.mark.asyncio
    async def test_notification_contains_sender_name_in_title(
        self, notification_service
    ):
        """Test that notification title contains sender name."""
        notification_service._push_service.send_to_user = AsyncMock(return_value=[])

        await notification_service.on_new_message(
            conversation_id=uuid4(),
            sender_name="Bob",
            message_preview="Hello!",
            recipient_id=uuid4(),
        )

        call_args = notification_service._push_service.send_to_user.call_args
        notification = call_args[0][1]
        assert "Bob" in notification.title
        assert notification.title == "Message from Bob"

    @pytest.mark.asyncio
    async def test_notification_contains_message_preview(self, notification_service):
        """Test that notification body contains message preview."""
        notification_service._push_service.send_to_user = AsyncMock(return_value=[])
        message = "Looking forward to our dance session!"

        await notification_service.on_new_message(
            conversation_id=uuid4(),
            sender_name="Alice",
            message_preview=message,
            recipient_id=uuid4(),
        )

        call_args = notification_service._push_service.send_to_user.call_args
        notification = call_args[0][1]
        assert notification.body == message

    @pytest.mark.asyncio
    async def test_notification_truncates_long_message(self, notification_service):
        """Test that long message previews are truncated."""
        notification_service._push_service.send_to_user = AsyncMock(return_value=[])
        long_message = "x" * 150  # Message longer than 100 characters

        await notification_service.on_new_message(
            conversation_id=uuid4(),
            sender_name="Alice",
            message_preview=long_message,
            recipient_id=uuid4(),
        )

        call_args = notification_service._push_service.send_to_user.call_args
        notification = call_args[0][1]
        assert len(notification.body) == 100
        assert notification.body.endswith("...")

    @pytest.mark.asyncio
    async def test_notification_data_contains_conversation_id(
        self, notification_service
    ):
        """Test that notification data contains conversation ID."""
        notification_service._push_service.send_to_user = AsyncMock(return_value=[])
        conversation_id = uuid4()

        await notification_service.on_new_message(
            conversation_id=conversation_id,
            sender_name="Alice",
            message_preview="Hello!",
            recipient_id=uuid4(),
        )

        call_args = notification_service._push_service.send_to_user.call_args
        notification = call_args[0][1]
        assert notification.data["conversation_id"] == str(conversation_id)
        assert notification.data["type"] == "new_message"
        assert notification.data["screen"] == "chat"


class TestOnSessionStartingSoon:
    """Tests for session starting soon reminder (30 min)."""

    @pytest.mark.asyncio
    async def test_sends_notification_to_user(
        self, notification_service, sample_booking
    ):
        """Test that reminder notification is sent to the specified user."""
        notification_service._push_service.send_to_user = AsyncMock(
            return_value=[NotificationResult(token="test", success=True)]
        )
        user_id = uuid4()

        await notification_service.on_session_starting_soon(
            booking=sample_booking,
            other_party_name="Dance Partner",
            notify_user_id=user_id,
        )

        notification_service._push_service.send_to_user.assert_called_once()
        call_args = notification_service._push_service.send_to_user.call_args
        assert call_args[0][0] == user_id

    @pytest.mark.asyncio
    async def test_notification_contains_correct_title(
        self, notification_service, sample_booking
    ):
        """Test that reminder notification has correct title."""
        notification_service._push_service.send_to_user = AsyncMock(return_value=[])

        await notification_service.on_session_starting_soon(
            booking=sample_booking,
            other_party_name="Dance Partner",
            notify_user_id=uuid4(),
        )

        call_args = notification_service._push_service.send_to_user.call_args
        notification = call_args[0][1]
        assert notification.title == "Session Starting Soon"

    @pytest.mark.asyncio
    async def test_notification_contains_other_party_name(
        self, notification_service, sample_booking
    ):
        """Test that notification body contains the other party's name."""
        notification_service._push_service.send_to_user = AsyncMock(return_value=[])

        await notification_service.on_session_starting_soon(
            booking=sample_booking,
            other_party_name="Sarah Johnson",
            notify_user_id=uuid4(),
        )

        call_args = notification_service._push_service.send_to_user.call_args
        notification = call_args[0][1]
        assert "Sarah Johnson" in notification.body

    @pytest.mark.asyncio
    async def test_notification_contains_time(
        self, notification_service, sample_booking
    ):
        """Test that notification body contains the session time."""
        notification_service._push_service.send_to_user = AsyncMock(return_value=[])

        await notification_service.on_session_starting_soon(
            booking=sample_booking,
            other_party_name="Dance Partner",
            notify_user_id=uuid4(),
        )

        call_args = notification_service._push_service.send_to_user.call_args
        notification = call_args[0][1]
        # Check that it contains time-like pattern (XX:XX AM/PM)
        assert ":" in notification.body
        assert "AM" in notification.body or "PM" in notification.body

    @pytest.mark.asyncio
    async def test_notification_data_contains_booking_id(
        self, notification_service, sample_booking
    ):
        """Test that notification data contains booking ID."""
        notification_service._push_service.send_to_user = AsyncMock(return_value=[])

        await notification_service.on_session_starting_soon(
            booking=sample_booking,
            other_party_name="Dance Partner",
            notify_user_id=uuid4(),
        )

        call_args = notification_service._push_service.send_to_user.call_args
        notification = call_args[0][1]
        assert notification.data["booking_id"] == str(sample_booking.id)
        assert notification.data["type"] == "session_reminder"


class TestSendSessionReminders:
    """Tests for batch session reminder sending."""

    @pytest.mark.asyncio
    async def test_sends_reminders_to_both_parties(
        self, notification_service, sample_booking
    ):
        """Test that reminders are sent to both client and host."""
        notification_service._push_service.send_to_user = AsyncMock(return_value=[])

        count = await notification_service.send_session_reminders(
            [
                (sample_booking, "Client Name", "Host Name"),
            ]
        )

        # Should send to both client and host
        assert notification_service._push_service.send_to_user.call_count == 2
        assert count == 2

    @pytest.mark.asyncio
    async def test_returns_correct_count(self, notification_service, sample_booking):
        """Test that returns the number of notifications sent."""
        notification_service._push_service.send_to_user = AsyncMock(return_value=[])

        # Create two bookings
        booking2 = MagicMock(spec=Booking)
        booking2.id = uuid4()
        booking2.client_id = str(uuid4())
        booking2.host_id = str(uuid4())
        booking2.scheduled_start = datetime.now(UTC) + timedelta(minutes=30)

        count = await notification_service.send_session_reminders(
            [
                (sample_booking, "Client1", "Host1"),
                (booking2, "Client2", "Host2"),
            ]
        )

        # 2 bookings * 2 parties each = 4 notifications
        assert count == 4

    @pytest.mark.asyncio
    async def test_continues_on_failure(self, notification_service, sample_booking):
        """Test that continues sending even if one fails."""
        call_count = 0

        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Push failed")
            return []

        notification_service._push_service.send_to_user = AsyncMock(
            side_effect=side_effect
        )

        count = await notification_service.send_session_reminders(
            [
                (sample_booking, "Client Name", "Host Name"),
            ]
        )

        # First fails, second succeeds
        assert count == 1
        assert notification_service._push_service.send_to_user.call_count == 2


class TestOnBookingCancelled:
    """Tests for booking cancelled notification."""

    @pytest.mark.asyncio
    async def test_sends_notification_to_specified_user(
        self, notification_service, sample_booking
    ):
        """Test that notification is sent to the specified user."""
        notification_service._push_service.send_to_user = AsyncMock(
            return_value=[NotificationResult(token="test", success=True)]
        )
        notify_user_id = uuid4()

        await notification_service.on_booking_cancelled(
            booking=sample_booking,
            cancelled_by_name="John Doe",
            notify_user_id=notify_user_id,
        )

        notification_service._push_service.send_to_user.assert_called_once()
        call_args = notification_service._push_service.send_to_user.call_args
        assert call_args[0][0] == notify_user_id

    @pytest.mark.asyncio
    async def test_notification_contains_correct_title(
        self, notification_service, sample_booking
    ):
        """Test that notification has correct title."""
        notification_service._push_service.send_to_user = AsyncMock(return_value=[])

        await notification_service.on_booking_cancelled(
            booking=sample_booking,
            cancelled_by_name="John Doe",
            notify_user_id=uuid4(),
        )

        call_args = notification_service._push_service.send_to_user.call_args
        notification = call_args[0][1]
        assert notification.title == "Booking Cancelled"

    @pytest.mark.asyncio
    async def test_notification_contains_canceller_name(
        self, notification_service, sample_booking
    ):
        """Test that notification body contains who cancelled."""
        notification_service._push_service.send_to_user = AsyncMock(return_value=[])

        await notification_service.on_booking_cancelled(
            booking=sample_booking,
            cancelled_by_name="Jane Smith",
            notify_user_id=uuid4(),
        )

        call_args = notification_service._push_service.send_to_user.call_args
        notification = call_args[0][1]
        assert "Jane Smith" in notification.body


class TestGetNotificationTriggerService:
    """Tests for the factory function."""

    def test_creates_service_instance(self, mock_db):
        """Test that factory function creates a service instance."""
        service = get_notification_trigger_service(mock_db)

        assert isinstance(service, NotificationTriggerService)
        assert service.db == mock_db
