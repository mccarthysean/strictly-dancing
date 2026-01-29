"""Messaging repository for conversation and message data access operations."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import and_, case, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation, Message, MessageType


class MessagingRepository:
    """Repository for Conversation and Message CRUD operations.

    Implements the repository pattern for messaging data access,
    providing an abstraction layer over SQLAlchemy operations.

    All methods use async patterns for non-blocking database access.

    Attributes:
        session: The async database session for executing queries.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session.

        Args:
            session: An async SQLAlchemy session.
        """
        self._session = session

    async def get_or_create_conversation(
        self,
        user_1_id: UUID,
        user_2_id: UUID,
    ) -> tuple[Conversation, bool]:
        """Get an existing conversation or create a new one between two users.

        Ensures participant ordering (participant_1_id < participant_2_id)
        for consistent lookup.

        Args:
            user_1_id: First user's UUID.
            user_2_id: Second user's UUID.

        Returns:
            A tuple of (Conversation, created) where created is True if
            a new conversation was created, False if existing.

        Raises:
            ValueError: If user_1_id and user_2_id are the same.
        """
        if user_1_id == user_2_id:
            raise ValueError("Cannot create conversation with self")

        # Ensure consistent ordering (smaller UUID first)
        p1_id = str(min(user_1_id, user_2_id, key=lambda x: str(x)))
        p2_id = str(max(user_1_id, user_2_id, key=lambda x: str(x)))

        # Try to find existing conversation
        stmt = select(Conversation).where(
            and_(
                Conversation.participant_1_id == p1_id,
                Conversation.participant_2_id == p2_id,
            )
        )
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            return existing, False

        # Create new conversation
        conversation = Conversation(
            participant_1_id=p1_id,
            participant_2_id=p2_id,
            participant_1_unread_count=0,
            participant_2_unread_count=0,
        )
        self._session.add(conversation)
        await self._session.flush()
        return conversation, True

    async def get_conversation_by_id(
        self,
        conversation_id: UUID,
        load_messages: bool = False,
    ) -> Conversation | None:
        """Get a conversation by ID.

        Args:
            conversation_id: The conversation's UUID.
            load_messages: Whether to eagerly load messages.

        Returns:
            The Conversation if found, None otherwise.
        """
        stmt = select(Conversation).where(Conversation.id == str(conversation_id))

        if load_messages:
            stmt = stmt.options(selectinload(Conversation.messages))

        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_conversations_for_user(
        self,
        user_id: UUID,
        cursor: UUID | None = None,
        limit: int = 20,
    ) -> list[Conversation]:
        """Get conversations for a user, ordered by last message time.

        Uses cursor-based pagination for efficient scrolling.

        Args:
            user_id: The user's UUID.
            cursor: Optional conversation ID to paginate from.
            limit: Maximum number of conversations to return.

        Returns:
            List of conversations, ordered by last_message_at descending.
        """
        user_id_str = str(user_id)

        # Base query: find all conversations where user is a participant
        stmt = (
            select(Conversation)
            .where(
                or_(
                    Conversation.participant_1_id == user_id_str,
                    Conversation.participant_2_id == user_id_str,
                )
            )
            .order_by(
                Conversation.last_message_at.desc().nulls_last(),
                Conversation.created_at.desc(),
            )
        )

        # Apply cursor pagination
        if cursor:
            # Get the cursor conversation's last_message_at and created_at
            cursor_stmt = select(
                Conversation.last_message_at, Conversation.created_at
            ).where(Conversation.id == str(cursor))
            cursor_result = await self._session.execute(cursor_stmt)
            cursor_row = cursor_result.one_or_none()

            if cursor_row:
                cursor_last_message_at, cursor_created_at = cursor_row
                # Use composite cursor: last_message_at, created_at
                stmt = stmt.where(
                    or_(
                        Conversation.last_message_at < cursor_last_message_at,
                        and_(
                            Conversation.last_message_at == cursor_last_message_at,
                            Conversation.created_at < cursor_created_at,
                        ),
                        and_(
                            Conversation.last_message_at.is_(None),
                            cursor_last_message_at.is_not(None),
                        ),
                        and_(
                            Conversation.last_message_at.is_(None),
                            cursor_last_message_at.is_(None),
                            Conversation.created_at < cursor_created_at,
                        ),
                    )
                )

        stmt = stmt.limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_messages(
        self,
        conversation_id: UUID,
        cursor: UUID | None = None,
        limit: int = 50,
        load_sender: bool = True,
    ) -> list[Message]:
        """Get messages in a conversation with cursor-based pagination.

        Returns messages in reverse chronological order (newest first)
        for efficient infinite scroll loading.

        Args:
            conversation_id: The conversation's UUID.
            cursor: Optional message ID to paginate from (load older messages).
            limit: Maximum number of messages to return.
            load_sender: Whether to eagerly load sender relationship.

        Returns:
            List of messages, ordered by created_at descending.
        """
        stmt = (
            select(Message)
            .where(Message.conversation_id == str(conversation_id))
            .order_by(Message.created_at.desc())
        )

        if load_sender:
            stmt = stmt.options(selectinload(Message.sender))

        # Apply cursor pagination
        if cursor:
            cursor_stmt = select(Message.created_at).where(Message.id == str(cursor))
            cursor_result = await self._session.execute(cursor_stmt)
            cursor_created_at = cursor_result.scalar_one_or_none()

            if cursor_created_at:
                stmt = stmt.where(Message.created_at < cursor_created_at)

        stmt = stmt.limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create_message(
        self,
        conversation_id: UUID,
        sender_id: UUID,
        content: str,
        message_type: MessageType = MessageType.TEXT,
    ) -> Message:
        """Create a new message in a conversation.

        Also updates the conversation's last_message_at, last_message_preview,
        and increments the unread count for the recipient.

        Args:
            conversation_id: The conversation's UUID.
            sender_id: The sender's UUID.
            content: The message content.
            message_type: The type of message.

        Returns:
            The newly created Message.

        Raises:
            ValueError: If conversation not found or sender not a participant.
        """
        # Get the conversation to validate and update
        conversation = await self.get_conversation_by_id(conversation_id)
        if not conversation:
            raise ValueError("Conversation not found")

        sender_id_str = str(sender_id)
        if not conversation.is_participant(sender_id_str):
            raise ValueError("Sender is not a participant in this conversation")

        # Create the message
        message = Message(
            conversation_id=str(conversation_id),
            sender_id=sender_id_str,
            content=content,
            message_type=message_type,
        )
        self._session.add(message)

        # Update conversation metadata
        now = datetime.now(UTC)
        conversation.last_message_at = now
        conversation.last_message_preview = (
            content[:255] if len(content) > 255 else content
        )

        # Increment unread count for the recipient
        if conversation.participant_1_id == sender_id_str:
            conversation.participant_2_unread_count += 1
        else:
            conversation.participant_1_unread_count += 1

        await self._session.flush()
        return message

    async def mark_as_read(
        self,
        conversation_id: UUID,
        user_id: UUID,
    ) -> int:
        """Mark all messages as read for a user in a conversation.

        Only marks messages sent by the other participant as read.
        Also resets the unread count for the user.

        Args:
            conversation_id: The conversation's UUID.
            user_id: The user marking messages as read.

        Returns:
            The number of messages marked as read.
        """
        conversation_id_str = str(conversation_id)
        user_id_str = str(user_id)
        now = datetime.now(UTC)

        # Mark all unread messages from other participants as read
        stmt = (
            update(Message)
            .where(
                and_(
                    Message.conversation_id == conversation_id_str,
                    Message.sender_id != user_id_str,
                    Message.read_at.is_(None),
                )
            )
            .values(read_at=now)
        )
        result = await self._session.execute(stmt)
        messages_marked = result.rowcount

        # Reset unread count for this user
        conversation = await self.get_conversation_by_id(conversation_id)
        if conversation:
            if conversation.participant_1_id == user_id_str:
                conversation.participant_1_unread_count = 0
            elif conversation.participant_2_id == user_id_str:
                conversation.participant_2_unread_count = 0

        await self._session.flush()
        return messages_marked

    async def get_unread_count(self, user_id: UUID) -> int:
        """Get total unread message count across all conversations for a user.

        Args:
            user_id: The user's UUID.

        Returns:
            Total number of unread messages.
        """
        user_id_str = str(user_id)

        # Sum up unread counts from all conversations where user is a participant
        stmt = select(
            func.coalesce(
                func.sum(
                    case(
                        (
                            Conversation.participant_1_id == user_id_str,
                            Conversation.participant_1_unread_count,
                        ),
                        (
                            Conversation.participant_2_id == user_id_str,
                            Conversation.participant_2_unread_count,
                        ),
                        else_=0,
                    )
                ),
                0,
            )
        ).where(
            or_(
                Conversation.participant_1_id == user_id_str,
                Conversation.participant_2_id == user_id_str,
            )
        )

        result = await self._session.execute(stmt)
        return int(result.scalar() or 0)

    async def get_unread_count_for_conversation(
        self,
        conversation_id: UUID,
        user_id: UUID,
    ) -> int:
        """Get unread message count for a specific conversation.

        Args:
            conversation_id: The conversation's UUID.
            user_id: The user's UUID.

        Returns:
            Number of unread messages in this conversation.
        """
        conversation = await self.get_conversation_by_id(conversation_id)
        if not conversation:
            return 0

        user_id_str = str(user_id)
        if conversation.participant_1_id == user_id_str:
            return conversation.participant_1_unread_count
        elif conversation.participant_2_id == user_id_str:
            return conversation.participant_2_unread_count
        return 0

    async def get_conversation_between_users(
        self,
        user_1_id: UUID,
        user_2_id: UUID,
    ) -> Conversation | None:
        """Get an existing conversation between two users if it exists.

        Args:
            user_1_id: First user's UUID.
            user_2_id: Second user's UUID.

        Returns:
            The Conversation if found, None otherwise.
        """
        # Ensure consistent ordering
        p1_id = str(min(user_1_id, user_2_id, key=lambda x: str(x)))
        p2_id = str(max(user_1_id, user_2_id, key=lambda x: str(x)))

        stmt = select(Conversation).where(
            and_(
                Conversation.participant_1_id == p1_id,
                Conversation.participant_2_id == p2_id,
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_message(self, message_id: UUID, user_id: UUID) -> bool:
        """Delete a message (only sender can delete).

        Args:
            message_id: The message's UUID.
            user_id: The user attempting to delete.

        Returns:
            True if deleted, False if message not found or user not sender.
        """
        stmt = select(Message).where(Message.id == str(message_id))
        result = await self._session.execute(stmt)
        message = result.scalar_one_or_none()

        if not message or message.sender_id != str(user_id):
            return False

        await self._session.delete(message)
        await self._session.flush()
        return True
