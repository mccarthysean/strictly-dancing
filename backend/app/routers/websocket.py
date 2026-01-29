"""WebSocket endpoints for real-time chat and location tracking functionality."""

from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.booking import BookingStatus
from app.models.user import User
from app.repositories.booking import BookingRepository
from app.repositories.messaging import MessagingRepository
from app.repositories.user import UserRepository
from app.services.websocket import (
    WebSocketManager,
    WebSocketMessage,
    WebSocketMessageType,
    verify_websocket_token,
    websocket_manager,
)
from app.services.websocket_location import (
    LocationMessageType,
    LocationUpdate,
    location_websocket_manager,
    verify_location_websocket_token,
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


async def _get_user_for_location(
    token: str,
    session: AsyncSession,
) -> User | None:
    """Get user from JWT token for location WebSocket.

    Args:
        token: The JWT access token.
        session: Database session.

    Returns:
        User if valid and active, None otherwise.
    """
    user_id = await verify_location_websocket_token(token)
    if user_id is None:
        return None

    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)

    if user is None or not user.is_active:
        return None

    return user


async def _verify_booking_access(
    booking_id: UUID,
    user_id: UUID,
    session: AsyncSession,
) -> tuple[bool, str | None]:
    """Verify user has access to the booking and it's in progress.

    Args:
        booking_id: The booking ID.
        user_id: The user ID.
        session: Database session.

    Returns:
        Tuple of (has_access, user_role). user_role is 'client' or 'host'.
    """
    booking_repo = BookingRepository(session)
    booking = await booking_repo.get_by_id(booking_id)

    if booking is None:
        return False, None

    user_id_str = str(user_id)

    # Check if user is client or host
    if booking.client_id == user_id_str:
        user_role = "client"
    elif booking.host_id == user_id_str:
        user_role = "host"
    else:
        return False, None

    # Check if booking is in progress
    if booking.status != BookingStatus.IN_PROGRESS:
        return False, None

    return True, user_role


@router.websocket("/ws/location/{booking_id}")
async def websocket_location(
    websocket: WebSocket,
    booking_id: UUID,
    token: str = Query(..., description="JWT access token"),
) -> None:
    """WebSocket endpoint for real-time location tracking during active sessions.

    Allows participants of an active (in_progress) session to share their
    real-time location with each other for safety and coordination.

    Authentication is done via JWT token passed as query parameter.

    Message Types (client -> server):
    - location_update: Send current location
      {"type": "location_update", "latitude": 40.7128, "longitude": -74.0060,
       "accuracy": 10.0, "altitude": null, "heading": null, "speed": null}

    Message Types (server -> client):
    - connected: Connection established
      {"type": "connected", "data": {"user_id": "...", "user_role": "client"}}

    - location_received: Location update from other participant
      {"type": "location_received", "data": {"user_id": "...", "location": {...}}}

    - disconnected: Other participant disconnected
      {"type": "disconnected", "data": {"user_id": "..."}}

    - session_ended: The session has been completed
      {"type": "session_ended", "data": {"message": "Session has ended"}}

    - error: Error message
      {"type": "error", "data": {"message": "..."}}

    Args:
        websocket: The WebSocket connection.
        booking_id: The booking UUID for the active session.
        token: JWT access token for authentication.
    """
    async with AsyncSessionLocal() as session:
        # Authenticate user
        user = await _get_user_for_location(token, session)
        if user is None:
            await websocket.accept()
            await websocket.send_json(
                {
                    "type": LocationMessageType.ERROR.value,
                    "data": {"message": "Authentication failed"},
                }
            )
            await websocket.close(code=4001, reason="Authentication failed")
            return

        user_id = str(user.id)

        # Verify user has access to booking and it's in progress
        has_access, user_role = await _verify_booking_access(
            booking_id,
            UUID(user_id),
            session,
        )
        if not has_access or user_role is None:
            await websocket.accept()
            await websocket.send_json(
                {
                    "type": LocationMessageType.ERROR.value,
                    "data": {"message": "Access denied or session not in progress"},
                }
            )
            await websocket.close(code=4003, reason="Access denied")
            return

        # Connect to location WebSocket manager
        connection = await location_websocket_manager.connect(
            websocket=websocket,
            booking_id=str(booking_id),
            user_id=user_id,
            user_role=user_role,
        )

        try:
            while True:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                message_type = message.get("type")

                if message_type == "location_update":
                    # Validate and process location update
                    try:
                        location = LocationUpdate(
                            latitude=float(message.get("latitude", 0)),
                            longitude=float(message.get("longitude", 0)),
                            accuracy=message.get("accuracy"),
                            altitude=message.get("altitude"),
                            heading=message.get("heading"),
                            speed=message.get("speed"),
                        )

                        # Validate coordinates
                        if not (-90 <= location.latitude <= 90):
                            raise ValueError("Invalid latitude")
                        if not (-180 <= location.longitude <= 180):
                            raise ValueError("Invalid longitude")

                        await location_websocket_manager.handle_location_update(
                            str(booking_id),
                            user_id,
                            location,
                        )
                    except (ValueError, TypeError) as e:
                        await websocket.send_json(
                            {
                                "type": LocationMessageType.ERROR.value,
                                "data": {"message": f"Invalid location data: {e}"},
                            }
                        )

                else:
                    # Unknown message type - send error
                    await websocket.send_json(
                        {
                            "type": LocationMessageType.ERROR.value,
                            "data": {
                                "message": f"Unknown message type: {message_type}"
                            },
                        }
                    )

        except WebSocketDisconnect:
            await location_websocket_manager.disconnect(connection)
        except json.JSONDecodeError:
            await websocket.send_json(
                {
                    "type": LocationMessageType.ERROR.value,
                    "data": {"message": "Invalid JSON"},
                }
            )
        except Exception as e:
            await websocket.send_json(
                {
                    "type": LocationMessageType.ERROR.value,
                    "data": {"message": str(e)},
                }
            )
            await location_websocket_manager.disconnect(connection)
