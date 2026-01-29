"""Celery application configuration for background task processing."""

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

# Create Celery app with Redis as broker and backend
celery_app = Celery(
    "strictly_dancing",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task execution settings
    task_acks_late=True,  # Acknowledge task after completion
    task_reject_on_worker_lost=True,  # Reject task if worker dies
    worker_prefetch_multiplier=1,  # Only fetch one task at a time
    # Result settings
    result_expires=3600,  # Results expire after 1 hour
    # Retry settings
    task_default_retry_delay=60,  # 1 minute default retry delay
    task_max_retries=3,
    # Worker settings
    worker_send_task_events=True,
    task_send_sent_event=True,
    # Beat scheduler settings (for periodic tasks)
    beat_scheduler="celery.beat:PersistentScheduler",
)

# Optional: Define periodic tasks (Celery Beat)
celery_app.conf.beat_schedule = {
    # Send session reminders every 5 minutes
    "send-session-reminders": {
        "task": "app.workers.tasks.send_session_reminders_task",
        "schedule": 300.0,  # Every 5 minutes
    },
}
