"""Background workers module."""

from app.workers.celery import celery_app
from app.workers.tasks import send_email_task

__all__ = ["celery_app", "send_email_task"]
