"""WebSocket endpoints for real-time chat functionality."""

from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.repositories.messaging import MessagingRepository
from app.repositories.user import UserRepository
from app.services.websocket import (
    WebSocketManager,
    WebSocketMessage,
    WebSocketMessageType,
    verify_websocket_token,
    websocket_manager,
)

router = APIRouter(tags=["websocket"])


async def _get_user_from_token(
    token: str,
    session: AsyncSession,
) -> User | None:
    """Get user from JWT token.

    Args:
        token: The JWT access token.
        session: Database session.

    Returns:
        User if valid and active, None otherwise.
    """
    user_id = await verify_websocket_token(token)
    if user_id is None:
        return None

    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)

    if user is None or not user.is_active:
        return None

    return user


async def _verify_conversation_access(
    conversation_id: UUID,
    user_id: UUID,
    session: AsyncSession,
) -> bool:
    """Verify user has access to the conversation.

    Args:
        conversation_id: The conversation ID.
        user_id: The user ID.
        session: Database session.

    Returns:
        True if user is a participant, False otherwise.
    """
    messaging_repo = MessagingRepository(session)
    conversation = await messaging_repo.get_conversation_by_id(conversation_id)

    if conversation is None:
        return False

    return conversation.is_participant(str(user_id))


@router.websocket("/ws/chat/{conversation_id}")
async def websocket_chat(
    websocket: WebSocket,
    conversation_id: UUID,
    token: str = Query(..., description="JWT access token"),
) -> None:
    """WebSocket endpoint for real-time chat.

    Connects the user to a conversation for real-time message updates,
    typing indicators, and presence notifications.

    Authentication is done via JWT token passed as query parameter.

    Message Types (client -> server):
    - message: Send a new message
      {"type": "message", "content": "Hello!"}

    - typing_start: Indicate user started typing
      {"type": "typing_start"}

    - typing_stop: Indicate user stopped typing
      {"type": "typing_stop"}

    Message Types (server -> client):
    - connected: Connection established
      {"type": "connected", "user_id": "..."}

    - message_received: New message from other participant
      {"type": "message_received", "data": {...}}

    - typing_start/typing_stop: Typing indicator from other participant
      {"type": "typing_start", "data": {"user_id": "..."}}

    - user_online/user_offline: Presence updates
      {"type": "user_online", "data": {"user_id": "..."}}

    - messages_read: Other user read messages
      {"type": "messages_read", "data": {"user_id": "...", "read_count": 5}}

    - error: Error message
      {"type": "error", "data": {"message": "..."}}

    Args:
        websocket: The WebSocket connection.
        conversation_id: The conversation UUID.
        token: JWT access token for authentication.
    """
    async with AsyncSessionLocal() as session:
        # Authenticate user
        user = await _get_user_from_token(token, session)
        if user is None:
            await websocket.accept()
            await websocket.send_json(
                {
                    "type": WebSocketMessageType.ERROR.value,
                    "data": {"message": "Authentication failed"},
                }
            )
            await websocket.close(code=4001, reason="Authentication failed")
            return

        user_id = str(user.id)

        # Verify user has access to conversation
        has_access = await _verify_conversation_access(
            conversation_id,
            UUID(user_id),
            session,
        )
        if not has_access:
            await websocket.accept()
            await websocket.send_json(
                {
                    "type": WebSocketMessageType.ERROR.value,
                    "data": {"message": "Access denied to conversation"},
                }
            )
            await websocket.close(code=4003, reason="Access denied")
            return

        # Connect to WebSocket manager
        connection = await websocket_manager.connect(
            websocket=websocket,
            conversation_id=str(conversation_id),
            user_id=user_id,
        )

        try:
            while True:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                message_type = message.get("type")

                if message_type == "message":
                    # Create a new database session for message creation
                    await _handle_send_message(
                        websocket_manager=websocket_manager,
                        conversation_id=str(conversation_id),
                        user_id=user_id,
                        content=message.get("content", ""),
                    )

                elif message_type == "typing_start":
                    await websocket_manager.handle_typing_start(
                        str(conversation_id),
                        user_id,
                    )

                elif message_type == "typing_stop":
                    await websocket_manager.handle_typing_stop(
                        str(conversation_id),
                        user_id,
                    )

                else:
                    # Unknown message type - send error
                    await websocket.send_json(
                        {
                            "type": WebSocketMessageType.ERROR.value,
                            "data": {
                                "message": f"Unknown message type: {message_type}"
                            },
                        }
                    )

        except WebSocketDisconnect:
            await websocket_manager.disconnect(connection)
        except json.JSONDecodeError:
            await websocket.send_json(
                {
                    "type": WebSocketMessageType.ERROR.value,
                    "data": {"message": "Invalid JSON"},
                }
            )
        except Exception as e:
            await websocket.send_json(
                {
                    "type": WebSocketMessageType.ERROR.value,
                    "data": {"message": str(e)},
                }
            )
            await websocket_manager.disconnect(connection)


async def _handle_send_message(
    websocket_manager: WebSocketManager,
    conversation_id: str,
    user_id: str,
    content: str,
) -> None:
    """Handle sending a message via WebSocket.

    Creates the message in the database and broadcasts to all participants.

    Args:
        websocket_manager: The WebSocket manager instance.
        conversation_id: The conversation ID.
        user_id: The sender's user ID.
        content: The message content.
    """
    if not content or not content.strip():
        return

    async with AsyncSessionLocal() as session:
        try:
            messaging_repo = MessagingRepository(session)

            # Create message in database
            message = await messaging_repo.create_message(
                conversation_id=UUID(conversation_id),
                sender_id=UUID(user_id),
                content=content.strip(),
            )
            await session.commit()

            # Get sender info for notification
            user_repo = UserRepository(session)
            sender = await user_repo.get_by_id(UUID(user_id))

            # Broadcast to conversation participants
            await websocket_manager.send_new_message_notification(
                conversation_id=conversation_id,
                message_data={
                    "id": str(message.id),
                    "content": message.content,
                    "sender_id": user_id,
                    "sender_name": f"{sender.first_name} {sender.last_name}"
                    if sender
                    else "Unknown",
                    "created_at": message.created_at.isoformat(),
                    "message_type": message.message_type.value,
                },
                sender_id=user_id,
            )

            # Also send confirmation back to sender
            await websocket_manager.broadcast_to_conversation(
                conversation_id=conversation_id,
                message=WebSocketMessage(
                    type=WebSocketMessageType.MESSAGE_SENT,
                    conversation_id=conversation_id,
                    data={
                        "id": str(message.id),
                        "content": message.content,
                        "created_at": message.created_at.isoformat(),
                    },
                    sender_id=user_id,
                ),
                exclude_user_id=None,  # Send to everyone including sender
            )

        except Exception:
            # Log error but don't crash the WebSocket connection
            pass
