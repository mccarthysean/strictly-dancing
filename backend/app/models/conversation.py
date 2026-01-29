"""Conversation and Message database models for real-time messaging."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class MessageType(str, enum.Enum):
    """Message type enumeration."""

    TEXT = "text"
    SYSTEM = "system"
    BOOKING_REQUEST = "booking_request"
    BOOKING_CONFIRMED = "booking_confirmed"
    BOOKING_CANCELLED = "booking_cancelled"


class Conversation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Conversation model for direct messaging between two users.

    Represents a chat thread between two participants.
    The participant_1_id is always the smaller UUID to ensure
    uniqueness of the participant pair.

    Attributes:
        id: UUID primary key
        participant_1_id: FK to first user (smaller UUID for uniqueness)
        participant_2_id: FK to second user (larger UUID for uniqueness)
        last_message_at: When the last message was sent
        last_message_preview: Preview text of last message
        participant_1_unread_count: Number of unread messages for participant 1
        participant_2_unread_count: Number of unread messages for participant 2
        created_at: When the conversation was created
        updated_at: When the conversation was last updated
    """

    __tablename__ = "conversations"

    participant_1_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    participant_2_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_message_preview: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    participant_1_unread_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )
    participant_2_unread_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )

    # Relationships
    participant_1: Mapped["User"] = relationship(
        "User",
        foreign_keys=[participant_1_id],
        lazy="selectin",
    )
    participant_2: Mapped["User"] = relationship(
        "User",
        foreign_keys=[participant_2_id],
        lazy="selectin",
    )
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        lazy="selectin",
        order_by="Message.created_at",
    )

    __table_args__ = (
        # Ensure unique participant pair (regardless of order)
        UniqueConstraint(
            "participant_1_id",
            "participant_2_id",
            name="uq_conversations_participants",
        ),
        # Ensure participant_1_id < participant_2_id for consistent ordering
        CheckConstraint(
            "participant_1_id < participant_2_id",
            name="ck_conversations_participant_order",
        ),
        # Index for finding conversations by participant
        Index(
            "ix_conversations_participant_1",
            "participant_1_id",
        ),
        Index(
            "ix_conversations_participant_2",
            "participant_2_id",
        ),
        # Index for sorting by last message
        Index(
            "ix_conversations_last_message_at",
            "last_message_at",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Conversation(id={self.id}, "
            f"p1={self.participant_1_id}, p2={self.participant_2_id})>"
        )

    def get_other_participant_id(self, user_id: str) -> str | None:
        """Get the ID of the other participant in the conversation."""
        if self.participant_1_id == user_id:
            return self.participant_2_id
        elif self.participant_2_id == user_id:
            return self.participant_1_id
        return None

    def is_participant(self, user_id: str) -> bool:
        """Check if a user is a participant in this conversation."""
        return user_id in (self.participant_1_id, self.participant_2_id)


class Message(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Message model for individual messages in a conversation.

    Attributes:
        id: UUID primary key
        conversation_id: FK to conversation
        sender_id: FK to user who sent the message
        content: Message content (text)
        message_type: Type of message (text, system, booking events)
        read_at: When the message was read by recipient
        metadata: Optional JSON metadata for system messages
        created_at: When the message was sent
        updated_at: When the message was last updated
    """

    __tablename__ = "messages"

    conversation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    sender_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    message_type: Mapped[MessageType] = mapped_column(
        ENUM(MessageType, name="message_type_enum", create_type=True),
        default=MessageType.TEXT,
        nullable=False,
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation",
        back_populates="messages",
        lazy="selectin",
    )
    sender: Mapped["User"] = relationship(
        "User",
        foreign_keys=[sender_id],
        lazy="selectin",
    )

    __table_args__ = (
        # Index for loading messages in a conversation
        Index(
            "ix_messages_conversation_created",
            "conversation_id",
            "created_at",
        ),
        # Index for unread messages
        Index(
            "ix_messages_conversation_read_at",
            "conversation_id",
            "read_at",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Message(id={self.id}, "
            f"conversation={self.conversation_id}, "
            f"type={self.message_type})>"
        )

    def is_read(self) -> bool:
        """Check if the message has been read."""
        return self.read_at is not None
