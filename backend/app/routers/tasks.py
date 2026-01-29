"""Tasks router for background job endpoints.

This module provides endpoints that can be called by cron jobs or
background task schedulers to perform periodic operations.
"""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.models.booking import BookingStatus
from app.repositories.booking import BookingRepository
from app.repositories.user import UserRepository
from app.services.notification_triggers import get_notification_trigger_service

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])

# Type alias for database session dependency
DbSession = Annotated[AsyncSession, Depends(get_db)]


class SessionRemindersResponse(BaseModel):
    """Response model for session reminders task."""

    bookings_checked: int
    notifications_sent: int
    message: str


async def verify_task_secret(
    x_task_secret: str | None = Header(None),
) -> None:
    """Verify the task secret header for protected task endpoints.

    This is a simple security measure to prevent unauthorized access
    to task endpoints from the public internet.
    """
    settings = get_settings()

    # If no task secret is configured, allow the request (for development)
    if not settings.task_secret_key:
        return

    if x_task_secret != settings.task_secret_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing task secret",
        )


@router.post(
    "/send-session-reminders",
    response_model=SessionRemindersResponse,
    status_code=status.HTTP_200_OK,
    summary="Send session starting soon reminders",
    description="Send push notifications for sessions starting within 30 minutes. Should be called every 5 minutes by a cron job.",
    dependencies=[Depends(verify_task_secret)],
)
async def send_session_reminders(
    db: DbSession,
) -> SessionRemindersResponse:
    """Send session reminders for bookings starting soon.

    This endpoint finds all confirmed bookings that:
    - Start within the next 25-35 minutes
    - Have not been reminded yet

    It sends push notifications to both the client and host for each booking.

    This endpoint should be called every 5-10 minutes by a cron job or
    external task scheduler.

    Returns:
        SessionRemindersResponse with counts of bookings checked and notifications sent.
    """
    booking_repo = BookingRepository(db)
    user_repo = UserRepository(db)
    notification_service = get_notification_trigger_service(db)

    now = datetime.now(UTC)

    # Look for bookings starting between 25 and 35 minutes from now
    # This gives a 10-minute window to catch bookings even if the cron
    # job runs slightly late or early
    window_start = now + timedelta(minutes=25)
    window_end = now + timedelta(minutes=35)

    # Get confirmed bookings in the window
    bookings = await booking_repo.get_bookings_in_time_window(
        start_time=window_start,
        end_time=window_end,
        status=BookingStatus.CONFIRMED,
        load_relationships=True,
    )

    # Build the list of bookings with names for notifications
    bookings_to_remind = []
    for booking in bookings:
        # Get user names
        client = await user_repo.get_by_id(booking.client_id)
        host = await user_repo.get_by_id(booking.host_id)

        if client and host:
            client_name = f"{client.first_name} {client.last_name}"
            host_name = f"{host.first_name} {host.last_name}"
            bookings_to_remind.append((booking, client_name, host_name))

    # Send reminders
    notifications_sent = await notification_service.send_session_reminders(
        bookings_to_remind
    )

    return SessionRemindersResponse(
        bookings_checked=len(bookings),
        notifications_sent=notifications_sent,
        message=f"Sent {notifications_sent} reminders for {len(bookings)} bookings",
    )
