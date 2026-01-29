"""Sentry SDK integration for error tracking and performance monitoring."""

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from app.core.config import get_settings


def init_sentry() -> None:
    """Initialize Sentry SDK with configured settings.

    Call this function once at application startup.
    Sentry will be disabled if SENTRY_DSN is not set.
    """
    settings = get_settings()

    if not settings.sentry_dsn:
        return

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment,
        # Performance monitoring
        traces_sample_rate=settings.sentry_traces_sample_rate,
        profiles_sample_rate=settings.sentry_profiles_sample_rate,
        # Integrations
        integrations=[
            # FastAPI/Starlette integration for HTTP request tracing
            StarletteIntegration(transaction_style="endpoint"),
            FastApiIntegration(transaction_style="endpoint"),
            # SQLAlchemy integration for database query tracing
            SqlalchemyIntegration(),
            # Logging integration to capture log messages as breadcrumbs
            LoggingIntegration(
                level=None,  # Capture all levels as breadcrumbs
                event_level=None,  # Don't send log messages as events
            ),
            # Redis integration for cache operation tracing
            RedisIntegration(),
            # Celery integration for background task tracing
            CeleryIntegration(),
        ],
        # Include request data in error reports
        send_default_pii=False,  # Don't send personally identifiable information
        # Attach stacktrace to log messages
        attach_stacktrace=True,
        # Enable auto session tracking
        auto_session_tracking=True,
        # Set release version
        release=f"strictly-dancing-backend@{settings.app_version}",
    )


def capture_exception(exception: Exception) -> str | None:
    """Capture an exception and send it to Sentry.

    Args:
        exception: The exception to capture.

    Returns:
        The Sentry event ID if captured, None otherwise.
    """
    return sentry_sdk.capture_exception(exception)


def capture_message(message: str, level: str = "info") -> str | None:
    """Capture a message and send it to Sentry.

    Args:
        message: The message to capture.
        level: The severity level (debug, info, warning, error, fatal).

    Returns:
        The Sentry event ID if captured, None otherwise.
    """
    return sentry_sdk.capture_message(message, level=level)


def set_user(user_id: str, email: str | None = None) -> None:
    """Set the current user for Sentry error tracking.

    Args:
        user_id: The user's unique identifier.
        email: The user's email address (optional).
    """
    sentry_sdk.set_user({"id": user_id, "email": email})


def set_tag(key: str, value: str) -> None:
    """Set a tag on the current scope.

    Args:
        key: The tag key.
        value: The tag value.
    """
    sentry_sdk.set_tag(key, value)


def set_context(name: str, data: dict) -> None:
    """Set context data on the current scope.

    Args:
        name: The context name.
        data: The context data dictionary.
    """
    sentry_sdk.set_context(name, data)
