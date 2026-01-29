"""Notification trigger service for sending push notifications on key events.

This module integrates push notifications with booking and messaging events,
automatically notifying users when important events occur.
"""

import logging
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.services.push_notifications import (
    NotificationData,
    NotificationPriority,
    PushNotificationService,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class NotificationTriggerService:
    """Service for triggering push notifications on key application events.

    This service encapsulates the logic for sending appropriate notifications
    when users perform actions like creating bookings, sending messages, etc.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._push_service = PushNotificationService(db)

    # --- Booking Notifications ---

    async def on_booking_created(
        self,
        booking: Booking,
        client_name: str,
        dance_style_name: str | None = None,
    ) -> None:
        """Send notification to host when a new booking is created.

        Args:
            booking: The newly created booking.
            client_name: The client's display name.
            dance_style_name: Optional dance style name for the booking.
        """
        host_id = UUID(booking.host_id)

        # Format the scheduled time
        scheduled_time = booking.scheduled_start.strftime("%b %d at %I:%M %p")

        # Build notification body
        body = f"{client_name} wants to book a session on {scheduled_time}"
        if dance_style_name:
            body = f"{client_name} wants to book a {dance_style_name} session on {scheduled_time}"

        notification = NotificationData(
            title="New Booking Request",
            body=body,
            data={
                "type": "booking_created",
                "booking_id": str(booking.id),
                "screen": "booking_detail",
            },
            priority=NotificationPriority.HIGH,
        )

        results = await self._push_service.send_to_user(host_id, notification)
        logger.info(
            "Sent new booking notification to host %s: %d devices",
            host_id,
            len(results),
        )

    async def on_booking_confirmed(
        self,
        booking: Booking,
        host_name: str,
    ) -> None:
        """Send notification to client when their booking is confirmed.

        Args:
            booking: The confirmed booking.
            host_name: The host's display name.
        """
        client_id = UUID(booking.client_id)

        # Format the scheduled time
        scheduled_time = booking.scheduled_start.strftime("%b %d at %I:%M %p")

        notification = NotificationData(
            title="Booking Confirmed!",
            body=f"{host_name} confirmed your session for {scheduled_time}",
            data={
                "type": "booking_confirmed",
                "booking_id": str(booking.id),
                "screen": "booking_detail",
            },
            priority=NotificationPriority.HIGH,
        )

        results = await self._push_service.send_to_user(client_id, notification)
        logger.info(
            "Sent booking confirmed notification to client %s: %d devices",
            client_id,
            len(results),
        )

    async def on_booking_cancelled(
        self,
        booking: Booking,
        cancelled_by_name: str,
        notify_user_id: UUID,
    ) -> None:
        """Send notification when a booking is cancelled.

        Args:
            booking: The cancelled booking.
            cancelled_by_name: Name of the person who cancelled.
            notify_user_id: The user to notify (the other party).
        """
        scheduled_time = booking.scheduled_start.strftime("%b %d at %I:%M %p")

        notification = NotificationData(
            title="Booking Cancelled",
            body=f"{cancelled_by_name} cancelled the session scheduled for {scheduled_time}",
            data={
                "type": "booking_cancelled",
                "booking_id": str(booking.id),
                "screen": "bookings",
            },
            priority=NotificationPriority.DEFAULT,
        )

        results = await self._push_service.send_to_user(notify_user_id, notification)
        logger.info(
            "Sent booking cancelled notification to user %s: %d devices",
            notify_user_id,
            len(results),
        )

    async def on_session_starting_soon(
        self,
        booking: Booking,
        other_party_name: str,
        notify_user_id: UUID,
    ) -> None:
        """Send reminder notification 30 minutes before session starts.

        Args:
            booking: The upcoming booking.
            other_party_name: Name of the other party (client or host).
            notify_user_id: The user to notify.
        """
        scheduled_time = booking.scheduled_start.strftime("%I:%M %p")

        notification = NotificationData(
            title="Session Starting Soon",
            body=f"Your session with {other_party_name} starts at {scheduled_time}",
            data={
                "type": "session_reminder",
                "booking_id": str(booking.id),
                "screen": "booking_detail",
            },
            priority=NotificationPriority.HIGH,
        )

        results = await self._push_service.send_to_user(notify_user_id, notification)
        logger.info(
            "Sent session reminder to user %s: %d devices",
            notify_user_id,
            len(results),
        )

    async def send_session_reminders(
        self,
        bookings: list[tuple[Booking, str, str]],
    ) -> int:
        """Send session starting soon reminders for multiple bookings.

        This method is designed to be called by a background job that queries
        for bookings starting in 30 minutes.

        Args:
            bookings: List of tuples (booking, client_name, host_name).

        Returns:
            Number of notifications sent successfully.
        """
        sent_count = 0

        for booking, client_name, host_name in bookings:
            # Notify both client and host
            try:
                await self.on_session_starting_soon(
                    booking=booking,
                    other_party_name=host_name,
                    notify_user_id=UUID(booking.client_id),
                )
                sent_count += 1
            except Exception:
                logger.exception(
                    "Failed to send reminder to client %s", booking.client_id
                )

            try:
                await self.on_session_starting_soon(
                    booking=booking,
                    other_party_name=client_name,
                    notify_user_id=UUID(booking.host_id),
                )
                sent_count += 1
            except Exception:
                logger.exception("Failed to send reminder to host %s", booking.host_id)

        return sent_count

    # --- Messaging Notifications ---

    async def on_new_message(
        self,
        conversation_id: UUID,
        sender_name: str,
        message_preview: str,
        recipient_id: UUID,
    ) -> None:
        """Send notification when a new message is received.

        Args:
            conversation_id: The conversation where the message was sent.
            sender_name: The sender's display name.
            message_preview: Preview of the message content.
            recipient_id: The user to notify.
        """
        # Truncate preview if too long
        if len(message_preview) > 100:
            message_preview = message_preview[:97] + "..."

        notification = NotificationData(
            title=f"Message from {sender_name}",
            body=message_preview,
            data={
                "type": "new_message",
                "conversation_id": str(conversation_id),
                "screen": "chat",
            },
            priority=NotificationPriority.DEFAULT,
        )

        results = await self._push_service.send_to_user(recipient_id, notification)
        logger.info(
            "Sent new message notification to user %s: %d devices",
            recipient_id,
            len(results),
        )


def get_notification_trigger_service(db: AsyncSession) -> NotificationTriggerService:
    """Create a NotificationTriggerService instance.

    Args:
        db: The database session.

    Returns:
        NotificationTriggerService instance.
    """
    return NotificationTriggerService(db)
