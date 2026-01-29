"""Background workers module."""

from app.workers.celery import celery_app
from app.workers.tasks import (
    send_booking_notification_email,
    send_email_task,
    send_magic_link_email,
    send_message_notification_email,
    send_review_request_email,
    send_session_reminders_task,
    send_templated_email_task,
    send_welcome_email,
)

__all__ = [
    "celery_app",
    "send_email_task",
    "send_templated_email_task",
    "send_booking_notification_email",
    "send_message_notification_email",
    "send_magic_link_email",
    "send_welcome_email",
    "send_review_request_email",
    "send_session_reminders_task",
]
