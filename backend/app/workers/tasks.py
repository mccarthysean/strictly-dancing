"""Celery background tasks for asynchronous processing."""

import asyncio

import structlog

from app.services.email import EmailMessage, EmailTemplate, email_service
from app.workers.celery import celery_app

logger = structlog.get_logger()


def _run_async(coro):
    """Run an async coroutine in a sync context."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


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

        # Create email message
        message = EmailMessage(
            to_email=to_email,
            subject=subject,
            plain_text=body,
            html_content=html_body,
        )

        # Send via email service
        message_id = _run_async(email_service.send(message))

        logger.info(
            "email_sent_success",
            to=to_email,
            subject=subject,
            message_id=message_id,
        )

        return {
            "status": "sent",
            "to": to_email,
            "subject": subject,
            "message_id": message_id,
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


@celery_app.task(bind=True, max_retries=3)
def send_templated_email_task(
    self,
    template: str,
    to_email: str,
    context: dict,
) -> dict:
    """
    Send a templated email asynchronously.

    Args:
        self: Celery task instance (bound)
        template: Email template name (from EmailTemplate enum)
        to_email: Recipient email address
        context: Template context variables

    Returns:
        dict with status and message_id

    Raises:
        Exception: On email sending failure (will retry)
    """
    try:
        email_template = EmailTemplate(template)

        logger.info(
            "sending_templated_email",
            template=template,
            to=to_email,
            task_id=self.request.id,
        )

        # Send via email service
        message_id = _run_async(
            email_service.send_template(
                template=email_template,
                to_email=to_email,
                context=context,
            )
        )

        logger.info(
            "templated_email_sent_success",
            template=template,
            to=to_email,
            message_id=message_id,
        )

        return {
            "status": "sent",
            "to": to_email,
            "template": template,
            "message_id": message_id,
        }

    except Exception as exc:
        logger.error(
            "templated_email_send_failed",
            template=template,
            to=to_email,
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
    host_name: str = "",
    client_name: str = "",
    date: str = "",
    time: str = "",
    duration: str = "",
    dance_style: str = "",
    location: str = "",
    reason: str = "",
    cancelled_by: str = "",
    is_host: bool = False,
) -> dict:
    """
    Send booking-related notification email using templates.

    Args:
        self: Celery task instance
        booking_id: UUID of the booking
        notification_type: Type of notification (created, confirmed, cancelled, etc.)
        recipient_email: Recipient email address
        recipient_name: Recipient name for personalization
        host_name: Name of the host
        client_name: Name of the client
        date: Booking date
        time: Booking time
        duration: Session duration
        dance_style: Dance style for the session
        location: Meeting location
        reason: Reason for cancellation (if applicable)
        cancelled_by: Who cancelled the booking (if applicable)
        is_host: Whether recipient is the host

    Returns:
        dict with status
    """
    logger.info(
        "sending_booking_notification",
        booking_id=booking_id,
        notification_type=notification_type,
        recipient=recipient_email,
    )

    # Map notification types to templates
    template_map = {
        "created": EmailTemplate.BOOKING_CREATED,
        "confirmed": EmailTemplate.BOOKING_CONFIRMED,
        "cancelled": EmailTemplate.BOOKING_CANCELLED,
        "completed": EmailTemplate.BOOKING_COMPLETED,
        "reminder": EmailTemplate.SESSION_REMINDER,
    }

    template = template_map.get(notification_type)
    if template is None:
        logger.warning(
            "unknown_notification_type",
            notification_type=notification_type,
            booking_id=booking_id,
        )
        return {"status": "skipped", "reason": "unknown_notification_type"}

    # Build context for template
    context = {
        "recipient_name": recipient_name,
        "host_name": host_name,
        "client_name": client_name,
        "date": date,
        "time": time,
        "duration": duration,
        "dance_style": dance_style,
        "location": location,
        "reason": reason,
        "cancelled_by": cancelled_by,
        "is_host": is_host,
        "partner_name": client_name if is_host else host_name,
    }

    # Delegate to templated email task
    send_templated_email_task.delay(
        template=template.value,
        to_email=recipient_email,
        context=context,
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
    Send new message notification email using template.

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

    context = {
        "recipient_name": recipient_name,
        "sender_name": sender_name,
        "message_preview": message_preview,
    }

    send_templated_email_task.delay(
        template=EmailTemplate.NEW_MESSAGE.value,
        to_email=recipient_email,
        context=context,
    )

    return {"status": "queued", "conversation_id": conversation_id}


@celery_app.task(bind=True)
def send_magic_link_email(
    self,
    to_email: str,
    name: str,
    code: str,
    expires_minutes: int = 15,
) -> dict:
    """
    Send magic link login code email.

    Args:
        self: Celery task instance
        to_email: Recipient email address
        name: Recipient name for personalization
        code: 6-digit login code
        expires_minutes: Minutes until code expires

    Returns:
        dict with status
    """
    logger.info(
        "sending_magic_link",
        to=to_email,
    )

    context = {
        "name": name,
        "code": code,
        "expires_minutes": expires_minutes,
    }

    send_templated_email_task.delay(
        template=EmailTemplate.MAGIC_LINK.value,
        to_email=to_email,
        context=context,
    )

    return {"status": "queued", "to": to_email}


@celery_app.task(bind=True)
def send_welcome_email(
    self,
    to_email: str,
    name: str,
) -> dict:
    """
    Send welcome email to new users.

    Args:
        self: Celery task instance
        to_email: Recipient email address
        name: User's name

    Returns:
        dict with status
    """
    logger.info(
        "sending_welcome_email",
        to=to_email,
    )

    context = {
        "name": name,
    }

    send_templated_email_task.delay(
        template=EmailTemplate.WELCOME.value,
        to_email=to_email,
        context=context,
    )

    return {"status": "queued", "to": to_email}


@celery_app.task(bind=True)
def send_review_request_email(
    self,
    to_email: str,
    recipient_name: str,
    host_name: str,
    date: str,
) -> dict:
    """
    Send review request email after completed session.

    Args:
        self: Celery task instance
        to_email: Recipient email address
        recipient_name: Client's name
        host_name: Host's name
        date: Date of the session

    Returns:
        dict with status
    """
    logger.info(
        "sending_review_request",
        to=to_email,
    )

    context = {
        "recipient_name": recipient_name,
        "host_name": host_name,
        "date": date,
    }

    send_templated_email_task.delay(
        template=EmailTemplate.REVIEW_REQUEST.value,
        to_email=to_email,
        context=context,
    )

    return {"status": "queued", "to": to_email}


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
