"""Push notification API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUser
from app.schemas.push import (
    PushTokenListResponse,
    PushTokenResponse,
    RegisterPushTokenRequest,
    UnregisterPushTokenRequest,
)
from app.services.push_notifications import PushNotificationService

router = APIRouter(prefix="/api/v1/push", tags=["push"])

# Type alias for database session dependency
DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.post(
    "/register",
    response_model=PushTokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register push token",
    description="Register an Expo push token for the current user's device.",
)
async def register_push_token(
    request: RegisterPushTokenRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> PushTokenResponse:
    """Register a push token for push notifications.

    This endpoint registers a device's Expo push token so the server
    can send push notifications to the user's mobile device.

    Args:
        request: The push token registration details.
        current_user: The authenticated user.
        db: The database session.

    Returns:
        The registered push token.

    Raises:
        HTTPException 400: If the token format is invalid.
    """
    push_service = PushNotificationService(db)

    try:
        token = await push_service.register_token(
            user_id=UUID(str(current_user.id)),
            token=request.token,
            platform=request.platform,
            device_id=request.device_id,
            device_name=request.device_name,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    return PushTokenResponse.model_validate(token)


@router.post(
    "/unregister",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unregister push token",
    description="Unregister an Expo push token to stop receiving notifications on a device.",
)
async def unregister_push_token(
    request: UnregisterPushTokenRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    """Unregister a push token.

    This endpoint deactivates a push token so the device will no longer
    receive push notifications.

    Args:
        request: The push token to unregister.
        current_user: The authenticated user.
        db: The database session.
    """
    push_service = PushNotificationService(db)
    await push_service.unregister_token(request.token)


@router.get(
    "/tokens",
    response_model=PushTokenListResponse,
    summary="Get my push tokens",
    description="Get all push tokens registered for the current user.",
)
async def get_my_push_tokens(
    current_user: CurrentUser,
    db: DbSession,
) -> PushTokenListResponse:
    """Get all push tokens for the current user.

    Returns all active and inactive tokens registered for the user.

    Args:
        current_user: The authenticated user.
        db: The database session.

    Returns:
        List of push tokens.
    """
    push_service = PushNotificationService(db)
    tokens = await push_service.get_user_tokens(
        UUID(str(current_user.id)),
        active_only=False,
    )

    return PushTokenListResponse(
        items=[PushTokenResponse.model_validate(t) for t in tokens],
        count=len(tokens),
    )


@router.delete(
    "/tokens/{token_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete push token",
    description="Delete a specific push token by ID.",
)
async def delete_push_token(
    token_id: str,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    """Delete a specific push token.

    Args:
        token_id: The push token UUID to delete.
        current_user: The authenticated user.
        db: The database session.

    Raises:
        HTTPException 404: If the token is not found or doesn't belong to user.
    """
    from sqlalchemy import select

    from app.models.push_token import PushToken

    query = select(PushToken).where(
        PushToken.id == token_id,
        PushToken.user_id == str(current_user.id),
    )
    result = await db.execute(query)
    token = result.scalar_one_or_none()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Push token not found",
        )

    token.is_active = False
    await db.flush()
