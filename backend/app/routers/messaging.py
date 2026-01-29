"""Messaging router for conversation and message management operations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUser
from app.models.conversation import MessageType
from app.repositories.messaging import MessagingRepository
from app.repositories.user import UserRepository
from app.schemas.messaging import (
    ConversationListResponse,
    ConversationSummaryResponse,
    ConversationWithMessagesResponse,
    ConversationWithParticipantsResponse,
    CreateMessageRequest,
    MessageListResponse,
    MessageUserSummary,
    MessageWithSenderResponse,
    StartConversationRequest,
    UnreadCountResponse,
)
from app.services.notification_triggers import get_notification_trigger_service

router = APIRouter(prefix="/api/v1/conversations", tags=["messaging"])

# Type alias for database session dependency
DbSession = Annotated[AsyncSession, Depends(get_db)]


def _build_user_summary(user) -> MessageUserSummary:
    """Build a MessageUserSummary from a User model."""
    return MessageUserSummary(
        id=str(user.id),
        first_name=user.first_name,
        last_name=user.last_name,
    )


def _build_message_response(message, sender=None) -> MessageWithSenderResponse:
    """Build a MessageWithSenderResponse from a Message model."""
    sender_summary = None
    if sender is not None:
        sender_summary = _build_user_summary(sender)
    elif message.sender is not None:
        sender_summary = _build_user_summary(message.sender)

    return MessageWithSenderResponse(
        id=str(message.id),
        conversation_id=str(message.conversation_id),
        sender_id=str(message.sender_id),
        content=message.content,
        message_type=message.message_type,
        read_at=message.read_at,
        created_at=message.created_at,
        updated_at=message.updated_at,
        sender=sender_summary,
    )


def _build_conversation_summary(
    conversation,
    current_user_id: str,
    other_participant,
) -> ConversationSummaryResponse:
    """Build a ConversationSummaryResponse from a Conversation model."""
    # Determine unread count for current user
    if conversation.participant_1_id == current_user_id:
        unread_count = conversation.participant_1_unread_count
    else:
        unread_count = conversation.participant_2_unread_count

    return ConversationSummaryResponse(
        id=str(conversation.id),
        other_participant=_build_user_summary(other_participant),
        last_message_at=conversation.last_message_at,
        last_message_preview=conversation.last_message_preview,
        unread_count=unread_count,
        created_at=conversation.created_at,
    )


def _build_conversation_with_participants(
    conversation,
    participant_1,
    participant_2,
) -> ConversationWithParticipantsResponse:
    """Build a ConversationWithParticipantsResponse from a Conversation model."""
    return ConversationWithParticipantsResponse(
        id=str(conversation.id),
        participant_1_id=str(conversation.participant_1_id),
        participant_2_id=str(conversation.participant_2_id),
        last_message_at=conversation.last_message_at,
        last_message_preview=conversation.last_message_preview,
        participant_1_unread_count=conversation.participant_1_unread_count,
        participant_2_unread_count=conversation.participant_2_unread_count,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        participant_1=_build_user_summary(participant_1) if participant_1 else None,
        participant_2=_build_user_summary(participant_2) if participant_2 else None,
    )


# --- Conversation Endpoints ---


@router.get(
    "",
    response_model=ConversationListResponse,
    status_code=status.HTTP_200_OK,
    summary="List conversations for current user",
    description="Get all conversations for the authenticated user, sorted by last message time.",
)
async def list_conversations(
    db: DbSession,
    current_user: CurrentUser,
    cursor: Annotated[
        str | None,
        Query(description="Cursor for pagination (conversation ID)"),
    ] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=50, description="Maximum conversations to return (1-50)"),
    ] = 20,
) -> ConversationListResponse:
    """Get conversations for the authenticated user.

    Returns all conversations where the user is a participant,
    ordered by the most recent message time.

    Args:
        db: The database session (injected).
        current_user: The authenticated user (injected).
        cursor: Optional conversation ID for pagination.
        limit: Maximum number of conversations to return.

    Returns:
        ConversationListResponse with conversations and pagination info.
    """
    messaging_repo = MessagingRepository(db)
    user_repo = UserRepository(db)

    # Parse cursor if provided
    cursor_uuid = None
    if cursor:
        try:
            cursor_uuid = UUID(cursor)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid cursor format",
            ) from e

    # Fetch conversations with one extra to check for more pages
    conversations = await messaging_repo.get_conversations_for_user(
        user_id=current_user.id,
        cursor=cursor_uuid,
        limit=limit + 1,
    )

    # Determine if there are more results
    has_more = len(conversations) > limit
    if has_more:
        conversations = conversations[:limit]

    # Build response items with other participant info
    items = []
    user_id_str = str(current_user.id)

    for conv in conversations:
        # Get the other participant's ID
        other_id = conv.get_other_participant_id(user_id_str)
        if other_id:
            other_user = await user_repo.get_by_id(UUID(other_id))
            if other_user:
                items.append(_build_conversation_summary(conv, user_id_str, other_user))

    # Set next cursor
    next_cursor = str(conversations[-1].id) if conversations and has_more else None

    return ConversationListResponse(
        items=items,
        next_cursor=next_cursor,
        has_more=has_more,
        limit=limit,
    )


@router.post(
    "",
    response_model=ConversationWithParticipantsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start or get a conversation",
    description="Start a new conversation with another user, or return existing one.",
)
async def start_conversation(
    db: DbSession,
    current_user: CurrentUser,
    request: StartConversationRequest,
) -> ConversationWithParticipantsResponse:
    """Start or get a conversation with another user.

    If a conversation already exists between the two users, it is returned.
    If the request includes an initial_message, it is sent as the first message.

    Args:
        db: The database session (injected).
        current_user: The authenticated user (injected).
        request: The conversation request with participant_id and optional initial_message.

    Returns:
        ConversationWithParticipantsResponse with the conversation and participant details.

    Raises:
        HTTPException: 400 if trying to start conversation with self.
        HTTPException: 404 if the participant user is not found.
    """
    messaging_repo = MessagingRepository(db)
    user_repo = UserRepository(db)

    # Parse and validate participant_id
    try:
        participant_id = UUID(request.participant_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid participant_id format",
        ) from e

    # Cannot start conversation with self
    if participant_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot start a conversation with yourself",
        )

    # Verify participant exists
    participant = await user_repo.get_by_id(participant_id)
    if participant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Get or create the conversation
    conversation, created = await messaging_repo.get_or_create_conversation(
        user_1_id=current_user.id,
        user_2_id=participant_id,
    )

    # Send initial message if provided
    if request.initial_message:
        await messaging_repo.create_message(
            conversation_id=UUID(str(conversation.id)),
            sender_id=current_user.id,
            content=request.initial_message,
            message_type=MessageType.TEXT,
        )

    # Get participant details
    participant_1 = await user_repo.get_by_id(UUID(conversation.participant_1_id))
    participant_2 = await user_repo.get_by_id(UUID(conversation.participant_2_id))

    return _build_conversation_with_participants(
        conversation, participant_1, participant_2
    )


@router.get(
    "/unread",
    response_model=UnreadCountResponse,
    status_code=status.HTTP_200_OK,
    summary="Get total unread message count",
    description="Get the total number of unread messages across all conversations.",
)
async def get_unread_count(
    db: DbSession,
    current_user: CurrentUser,
) -> UnreadCountResponse:
    """Get total unread message count for the authenticated user.

    Args:
        db: The database session (injected).
        current_user: The authenticated user (injected).

    Returns:
        UnreadCountResponse with total_unread count.
    """
    messaging_repo = MessagingRepository(db)

    total_unread = await messaging_repo.get_unread_count(current_user.id)

    return UnreadCountResponse(total_unread=total_unread)


@router.get(
    "/{conversation_id}",
    response_model=ConversationWithMessagesResponse,
    status_code=status.HTTP_200_OK,
    summary="Get conversation with messages",
    description="Get a conversation and its messages.",
)
async def get_conversation(
    conversation_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
    message_limit: Annotated[
        int,
        Query(ge=1, le=100, description="Maximum messages to include (1-100)"),
    ] = 50,
) -> ConversationWithMessagesResponse:
    """Get a conversation with its messages.

    Returns the conversation details along with the most recent messages.
    Use the messages endpoint with cursor for loading more messages.

    Args:
        conversation_id: The conversation's unique identifier.
        db: The database session (injected).
        current_user: The authenticated user (injected).
        message_limit: Maximum number of messages to include.

    Returns:
        ConversationWithMessagesResponse with conversation and messages.

    Raises:
        HTTPException: 403 if user is not a participant.
        HTTPException: 404 if conversation not found.
    """
    messaging_repo = MessagingRepository(db)
    user_repo = UserRepository(db)

    # Get the conversation
    conversation = await messaging_repo.get_conversation_by_id(conversation_id)
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    # Verify user is a participant
    user_id_str = str(current_user.id)
    if not conversation.is_participant(user_id_str):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant in this conversation",
        )

    # Get messages
    messages = await messaging_repo.get_messages(
        conversation_id=conversation_id,
        limit=message_limit,
        load_sender=True,
    )

    # Get participant details
    participant_1 = await user_repo.get_by_id(UUID(conversation.participant_1_id))
    participant_2 = await user_repo.get_by_id(UUID(conversation.participant_2_id))

    # Build message responses (reverse to show oldest first)
    message_responses = [_build_message_response(msg) for msg in reversed(messages)]

    return ConversationWithMessagesResponse(
        id=str(conversation.id),
        participant_1_id=str(conversation.participant_1_id),
        participant_2_id=str(conversation.participant_2_id),
        last_message_at=conversation.last_message_at,
        last_message_preview=conversation.last_message_preview,
        participant_1_unread_count=conversation.participant_1_unread_count,
        participant_2_unread_count=conversation.participant_2_unread_count,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        participant_1=_build_user_summary(participant_1) if participant_1 else None,
        participant_2=_build_user_summary(participant_2) if participant_2 else None,
        messages=message_responses,
    )


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageWithSenderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send a message",
    description="Send a new message in a conversation.",
)
async def send_message(
    conversation_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
    request: CreateMessageRequest,
) -> MessageWithSenderResponse:
    """Send a message in a conversation.

    Creates a new message in the specified conversation.
    The sender must be a participant in the conversation.

    Args:
        conversation_id: The conversation's unique identifier.
        db: The database session (injected).
        current_user: The authenticated user (injected).
        request: The message request with content and type.

    Returns:
        MessageWithSenderResponse with the created message.

    Raises:
        HTTPException: 403 if user is not a participant.
        HTTPException: 404 if conversation not found.
    """
    messaging_repo = MessagingRepository(db)

    # Get the conversation to verify it exists and user is participant
    conversation = await messaging_repo.get_conversation_by_id(conversation_id)
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    # Verify user is a participant
    user_id_str = str(current_user.id)
    if not conversation.is_participant(user_id_str):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant in this conversation",
        )

    # Create the message
    try:
        message = await messaging_repo.create_message(
            conversation_id=conversation_id,
            sender_id=current_user.id,
            content=request.content,
            message_type=request.message_type,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    # Send push notification to the recipient
    try:
        other_participant_id = conversation.get_other_participant_id(user_id_str)
        if other_participant_id:
            notification_service = get_notification_trigger_service(db)
            sender_name = f"{current_user.first_name} {current_user.last_name}"
            await notification_service.on_new_message(
                conversation_id=conversation_id,
                sender_name=sender_name,
                message_preview=request.content,
                recipient_id=UUID(other_participant_id),
            )
    except Exception:
        # Don't fail the message if notification fails
        pass

    return _build_message_response(message, sender=current_user)


@router.post(
    "/{conversation_id}/read",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Mark conversation as read",
    description="Mark all messages in a conversation as read.",
)
async def mark_conversation_read(
    conversation_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    """Mark all messages in a conversation as read.

    Marks all unread messages from the other participant as read
    and resets the unread count for the current user.

    Args:
        conversation_id: The conversation's unique identifier.
        db: The database session (injected).
        current_user: The authenticated user (injected).

    Returns:
        204 No Content on success.

    Raises:
        HTTPException: 403 if user is not a participant.
        HTTPException: 404 if conversation not found.
    """
    messaging_repo = MessagingRepository(db)

    # Get the conversation to verify it exists and user is participant
    conversation = await messaging_repo.get_conversation_by_id(conversation_id)
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    # Verify user is a participant
    user_id_str = str(current_user.id)
    if not conversation.is_participant(user_id_str):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant in this conversation",
        )

    # Mark messages as read
    await messaging_repo.mark_as_read(
        conversation_id=conversation_id,
        user_id=current_user.id,
    )


# --- Messages Endpoint (for loading more) ---


@router.get(
    "/{conversation_id}/messages",
    response_model=MessageListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get messages in a conversation",
    description="Get messages with cursor-based pagination for infinite scroll.",
)
async def get_messages(
    conversation_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
    cursor: Annotated[
        str | None,
        Query(description="Cursor for pagination (message ID)"),
    ] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=100, description="Maximum messages to return (1-100)"),
    ] = 50,
) -> MessageListResponse:
    """Get messages in a conversation with cursor-based pagination.

    Returns messages in reverse chronological order (newest first)
    for efficient infinite scroll loading. Use the cursor parameter
    to load older messages.

    Args:
        conversation_id: The conversation's unique identifier.
        db: The database session (injected).
        current_user: The authenticated user (injected).
        cursor: Optional message ID for pagination.
        limit: Maximum number of messages to return.

    Returns:
        MessageListResponse with messages and pagination info.

    Raises:
        HTTPException: 403 if user is not a participant.
        HTTPException: 404 if conversation not found.
    """
    messaging_repo = MessagingRepository(db)

    # Get the conversation to verify it exists and user is participant
    conversation = await messaging_repo.get_conversation_by_id(conversation_id)
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    # Verify user is a participant
    user_id_str = str(current_user.id)
    if not conversation.is_participant(user_id_str):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant in this conversation",
        )

    # Parse cursor if provided
    cursor_uuid = None
    if cursor:
        try:
            cursor_uuid = UUID(cursor)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid cursor format",
            ) from e

    # Fetch messages with one extra to check for more pages
    messages = await messaging_repo.get_messages(
        conversation_id=conversation_id,
        cursor=cursor_uuid,
        limit=limit + 1,
        load_sender=True,
    )

    # Determine if there are more results
    has_more = len(messages) > limit
    if has_more:
        messages = messages[:limit]

    # Build response items
    items = [_build_message_response(msg) for msg in messages]

    # Set next cursor
    next_cursor = str(messages[-1].id) if messages and has_more else None

    return MessageListResponse(
        items=items,
        next_cursor=next_cursor,
        has_more=has_more,
        limit=limit,
    )
