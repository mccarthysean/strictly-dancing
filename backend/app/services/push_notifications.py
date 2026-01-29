"""Push notification service for sending notifications via Expo Push API.

This module provides functionality for sending push notifications to mobile
devices using the Expo Push Notification service.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.push_token import DevicePlatform, PushToken

logger = logging.getLogger(__name__)


class NotificationPriority(str, Enum):
    """Push notification priority levels."""

    DEFAULT = "default"
    NORMAL = "normal"
    HIGH = "high"


class NotificationSound(str, Enum):
    """Push notification sound options."""

    DEFAULT = "default"
    NONE = None


@dataclass
class NotificationData:
    """Data for a push notification."""

    title: str
    body: str
    data: dict[str, Any] | None = None
    sound: str | None = "default"
    badge: int | None = None
    priority: NotificationPriority = NotificationPriority.DEFAULT
    channel_id: str | None = None  # Android notification channel


@dataclass
class NotificationResult:
    """Result of sending a notification."""

    token: str
    success: bool
    message_id: str | None = None
    error: str | None = None


class PushNotificationService:
    """Service for managing push tokens and sending notifications.

    Uses the Expo Push API to send notifications to mobile devices.
    https://docs.expo.dev/push-notifications/sending-notifications/
    """

    EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"

    def __init__(self, db: AsyncSession):
        self.db = db
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    # --- Token Management ---

    async def register_token(
        self,
        user_id: UUID,
        token: str,
        platform: DevicePlatform,
        device_id: str | None = None,
        device_name: str | None = None,
    ) -> PushToken:
        """Register or update a push token for a user.

        If the token already exists, updates its metadata.
        If the device_id exists for the user, replaces the old token.

        Args:
            user_id: The user's UUID
            token: The Expo push token
            platform: Device platform (ios, android, web)
            device_id: Optional unique device identifier
            device_name: Optional human-readable device name

        Returns:
            The registered or updated PushToken
        """
        # Validate token format
        if not self._is_valid_expo_token(token):
            msg = f"Invalid Expo push token format: {token}"
            raise ValueError(msg)

        # Check if token already exists
        existing = await self._get_token_by_value(token)
        if existing:
            # Update token if owned by same user
            if str(existing.user_id) == str(user_id):
                existing.is_active = True
                existing.device_id = device_id
                existing.device_name = device_name
                existing.platform = platform
                await self.db.flush()
                return existing
            # Token owned by different user - deactivate old and create new
            existing.is_active = False
            await self.db.flush()

        # If device_id provided, deactivate any existing token for that device
        if device_id:
            await self._deactivate_device_tokens(user_id, device_id)

        # Create new token
        push_token = PushToken(
            user_id=str(user_id),
            token=token,
            platform=platform,
            device_id=device_id,
            device_name=device_name,
            is_active=True,
        )
        self.db.add(push_token)
        await self.db.flush()
        await self.db.refresh(push_token)

        logger.info(
            "Registered push token for user %s on %s",
            user_id,
            platform.value,
        )

        return push_token

    async def unregister_token(self, token: str) -> bool:
        """Unregister (deactivate) a push token.

        Args:
            token: The Expo push token to unregister

        Returns:
            True if token was found and deactivated, False otherwise
        """
        existing = await self._get_token_by_value(token)
        if existing:
            existing.is_active = False
            await self.db.flush()
            logger.info("Unregistered push token %s", token[:20] + "...")
            return True
        return False

    async def get_user_tokens(
        self, user_id: UUID, active_only: bool = True
    ) -> list[PushToken]:
        """Get all push tokens for a user.

        Args:
            user_id: The user's UUID
            active_only: Whether to return only active tokens

        Returns:
            List of PushToken objects
        """
        query = select(PushToken).where(PushToken.user_id == str(user_id))
        if active_only:
            query = query.where(PushToken.is_active.is_(True))

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def _get_token_by_value(self, token: str) -> PushToken | None:
        """Get a push token by its value."""
        query = select(PushToken).where(PushToken.token == token)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _deactivate_device_tokens(self, user_id: UUID, device_id: str) -> None:
        """Deactivate all tokens for a specific device."""
        query = select(PushToken).where(
            and_(
                PushToken.user_id == str(user_id),
                PushToken.device_id == device_id,
                PushToken.is_active.is_(True),
            )
        )
        result = await self.db.execute(query)
        for token in result.scalars():
            token.is_active = False
        await self.db.flush()

    def _is_valid_expo_token(self, token: str) -> bool:
        """Validate Expo push token format.

        Expo tokens should be in format: ExponentPushToken[...] or ExpoPushToken[...]
        """
        return (
            token.startswith("ExponentPushToken[") or token.startswith("ExpoPushToken[")
        ) and token.endswith("]")

    # --- Sending Notifications ---

    async def send_notification(
        self,
        token: str,
        notification: NotificationData,
    ) -> NotificationResult:
        """Send a push notification to a single device.

        Args:
            token: The Expo push token
            notification: The notification data to send

        Returns:
            NotificationResult with success status and any errors
        """
        results = await self.send_notifications([token], notification)
        return (
            results[0]
            if results
            else NotificationResult(
                token=token,
                success=False,
                error="No result returned",
            )
        )

    async def send_notifications(
        self,
        tokens: list[str],
        notification: NotificationData,
    ) -> list[NotificationResult]:
        """Send a push notification to multiple devices.

        Uses the Expo Push API batch endpoint for efficiency.

        Args:
            tokens: List of Expo push tokens
            notification: The notification data to send

        Returns:
            List of NotificationResult objects
        """
        if not tokens:
            return []

        # Build messages for Expo API
        messages = []
        for token in tokens:
            message: dict[str, Any] = {
                "to": token,
                "title": notification.title,
                "body": notification.body,
            }

            if notification.sound is not None:
                message["sound"] = notification.sound
            if notification.badge is not None:
                message["badge"] = notification.badge
            if notification.data:
                message["data"] = notification.data
            if notification.priority != NotificationPriority.DEFAULT:
                message["priority"] = notification.priority.value
            if notification.channel_id:
                message["channelId"] = notification.channel_id

            messages.append(message)

        # Send to Expo Push API
        try:
            client = await self._get_client()
            response = await client.post(
                self.EXPO_PUSH_URL,
                json=messages,
                headers={
                    "Accept": "application/json",
                    "Accept-Encoding": "gzip, deflate",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            data = response.json()

        except httpx.HTTPError as e:
            logger.exception("Failed to send push notifications")
            return [
                NotificationResult(
                    token=token,
                    success=False,
                    error=str(e),
                )
                for token in tokens
            ]

        # Parse results
        results = []
        response_data = data.get("data", [])

        for i, token in enumerate(tokens):
            if i < len(response_data):
                ticket = response_data[i]
                if ticket.get("status") == "ok":
                    results.append(
                        NotificationResult(
                            token=token,
                            success=True,
                            message_id=ticket.get("id"),
                        )
                    )
                else:
                    error_message = ticket.get("message", "Unknown error")
                    error_details = ticket.get("details", {})
                    error = error_details.get("error", error_message)

                    results.append(
                        NotificationResult(
                            token=token,
                            success=False,
                            error=error,
                        )
                    )

                    # Deactivate invalid tokens
                    if error in ("DeviceNotRegistered", "InvalidCredentials"):
                        await self.unregister_token(token)
            else:
                results.append(
                    NotificationResult(
                        token=token,
                        success=False,
                        error="No response for token",
                    )
                )

        logger.info(
            "Sent %d notifications, %d successful",
            len(tokens),
            sum(1 for r in results if r.success),
        )

        return results

    async def send_to_user(
        self,
        user_id: UUID,
        notification: NotificationData,
    ) -> list[NotificationResult]:
        """Send a notification to all active devices of a user.

        Args:
            user_id: The user's UUID
            notification: The notification data to send

        Returns:
            List of NotificationResult objects for each device
        """
        tokens = await self.get_user_tokens(user_id, active_only=True)
        if not tokens:
            logger.debug("No active push tokens for user %s", user_id)
            return []

        token_values = [t.token for t in tokens]
        return await self.send_notifications(token_values, notification)

    async def send_to_users(
        self,
        user_ids: list[UUID],
        notification: NotificationData,
    ) -> dict[str, list[NotificationResult]]:
        """Send a notification to multiple users.

        Args:
            user_ids: List of user UUIDs
            notification: The notification data to send

        Returns:
            Dict mapping user_id to list of NotificationResults
        """
        results: dict[str, list[NotificationResult]] = {}

        # Collect all tokens
        all_tokens: list[tuple[str, str]] = []  # (user_id, token)
        for user_id in user_ids:
            tokens = await self.get_user_tokens(user_id, active_only=True)
            for token in tokens:
                all_tokens.append((str(user_id), token.token))

        if not all_tokens:
            return {str(uid): [] for uid in user_ids}

        # Send all notifications in one batch
        token_values = [t[1] for t in all_tokens]
        notification_results = await self.send_notifications(token_values, notification)

        # Map results back to users
        for i, (user_id_str, _) in enumerate(all_tokens):
            if user_id_str not in results:
                results[user_id_str] = []
            if i < len(notification_results):
                results[user_id_str].append(notification_results[i])

        return results


# Convenience function to create service instance
def get_push_notification_service(db: AsyncSession) -> PushNotificationService:
    """Create a PushNotificationService instance.

    Args:
        db: The database session

    Returns:
        PushNotificationService instance
    """
    return PushNotificationService(db)
