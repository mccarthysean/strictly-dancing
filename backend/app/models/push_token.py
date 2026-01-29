"""Push notification token model for storing Expo push tokens.

This module provides the PushToken model for storing push notification
tokens from mobile devices using Expo Push Notifications.
"""

import enum

from sqlalchemy import Boolean, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DevicePlatform(str, enum.Enum):
    """Device platform enumeration."""

    IOS = "ios"
    ANDROID = "android"
    WEB = "web"


class PushToken(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Push notification token for a user's device.

    Stores Expo push tokens for sending push notifications to mobile devices.
    Each user can have multiple devices (tokens).

    Attributes:
        id: UUID primary key
        user_id: Foreign key to users table
        token: The Expo push token (e.g., "ExponentPushToken[...]")
        device_id: Optional unique device identifier
        platform: Device platform (ios, android, web)
        device_name: Optional human-readable device name
        is_active: Whether the token is still valid
        created_at: When the token was registered
        updated_at: When the record was last updated
    """

    __tablename__ = "push_tokens"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    token: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True,
    )

    device_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    platform: Mapped[DevicePlatform] = mapped_column(
        ENUM(
            DevicePlatform,
            name="device_platform_enum",
            create_type=True,
        ),
        nullable=False,
    )

    device_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    # Relationships
    user = relationship(
        "User",
        backref="push_tokens",
        lazy="joined",
    )

    # Indexes for efficient lookups
    __table_args__ = (
        Index(
            "ix_push_tokens_user_platform",
            "user_id",
            "platform",
        ),
        Index(
            "ix_push_tokens_user_active",
            "user_id",
            "is_active",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<PushToken(id={self.id}, "
            f"user_id={self.user_id}, "
            f"platform={self.platform.value if isinstance(self.platform, DevicePlatform) else self.platform})>"
        )
