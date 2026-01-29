"""Celery background tasks for asynchronous processing."""

import structlog

from app.workers.celery import celery_app

logger = structlog.get_logger()


@celery_app.task(bind=True, max_retries=3)
def send_email_task(
    self,
    to_email: str,
    subject: str,
    body: str,
    html_body: str | None = None,
) -> dict:
    """
    Send an email asynchronously.

    Args:
        self: Celery task instance (bound)
        to_email: Recipient email address
        subject: Email subject line
        body: Plain text body
        html_body: Optional HTML body

    Returns:
        dict with status and message_id

    Raises:
        Exception: On email sending failure (will retry)
    """
    try:
        logger.info(
            "sending_email",
            to=to_email,
            subject=subject,
            task_id=self.request.id,
        )

        # TODO: Implement actual email sending via SMTP or service like SendGrid/SES
        # For now, just log the email
        logger.info(
            "email_sent_success",
            to=to_email,
            subject=subject,
            body_length=len(body),
            has_html=html_body is not None,
        )

        return {
            "status": "sent",
            "to": to_email,
            "subject": subject,
            "message_id": f"msg_{self.request.id}",
        }

    except Exception as exc:
        logger.error(
            "email_send_failed",
            to=to_email,
            subject=subject,
            error=str(exc),
            retry_count=self.request.retries,
        )
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2**self.request.retries)) from exc


@celery_app.task(bind=True)
def send_booking_notification_email(
    self,
    booking_id: str,
    notification_type: str,
    recipient_email: str,
    recipient_name: str,
) -> dict:
    """
    Send booking-related notification email.

    Args:
        self: Celery task instance
        booking_id: UUID of the booking
        notification_type: Type of notification (created, confirmed, cancelled, etc.)
        recipient_email: Recipient email address
        recipient_name: Recipient name for personalization

    Returns:
        dict with status
    """
    logger.info(
        "sending_booking_notification",
        booking_id=booking_id,
        notification_type=notification_type,
        recipient=recipient_email,
    )

    subject_map = {
        "created": "New Booking Request",
        "confirmed": "Booking Confirmed",
        "cancelled": "Booking Cancelled",
        "completed": "Session Completed - Leave a Review",
        "reminder": "Upcoming Session Reminder",
    }

    subject = subject_map.get(notification_type, "Booking Update")
    body = f"Hi {recipient_name},\n\nThis is a notification about your booking.\n\nType: {notification_type}\nBooking ID: {booking_id}\n\n- Strictly Dancing Team"

    # Delegate to main email task
    send_email_task.delay(
        to_email=recipient_email,
        subject=f"[Strictly Dancing] {subject}",
        body=body,
    )

    return {"status": "queued", "booking_id": booking_id, "type": notification_type}


@celery_app.task(bind=True)
def send_message_notification_email(
    self,
    conversation_id: str,
    sender_name: str,
    recipient_email: str,
    recipient_name: str,
    message_preview: str,
) -> dict:
    """
    Send new message notification email.

    Args:
        self: Celery task instance
        conversation_id: UUID of the conversation
        sender_name: Name of the message sender
        recipient_email: Recipient email address
        recipient_name: Recipient name
        message_preview: Preview of the message content

    Returns:
        dict with status
    """
    logger.info(
        "sending_message_notification",
        conversation_id=conversation_id,
        sender=sender_name,
        recipient=recipient_email,
    )

    subject = f"New message from {sender_name}"
    body = f'Hi {recipient_name},\n\nYou have a new message from {sender_name}:\n\n"{message_preview[:100]}{"..." if len(message_preview) > 100 else ""}"\n\nLog in to reply.\n\n- Strictly Dancing Team'

    send_email_task.delay(
        to_email=recipient_email,
        subject=f"[Strictly Dancing] {subject}",
        body=body,
    )

    return {"status": "queued", "conversation_id": conversation_id}


@celery_app.task(bind=True)
def send_session_reminders_task(self) -> dict:
    """
    Periodic task to send session reminders for upcoming bookings.

    This task should be scheduled via Celery Beat to run every 5-10 minutes.
    It finds all confirmed bookings starting within the next 30 minutes and
    sends reminder notifications to both parties.

    Returns:
        dict with count of reminders sent
    """
    logger.info("running_session_reminders_task", task_id=self.request.id)

    # TODO: Query database for upcoming sessions within 30 minutes
    # and send reminders via push notifications and email
    # This is a placeholder implementation

    reminders_sent = 0

    logger.info(
        "session_reminders_complete",
        reminders_sent=reminders_sent,
        task_id=self.request.id,
    )

    return {"status": "completed", "reminders_sent": reminders_sent}
