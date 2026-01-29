"""Users router for user profile management operations."""

import logging
from datetime import date, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUser
from app.models.availability import DayOfWeek
from app.models.user import UserType
from app.repositories.availability import AvailabilityRepository
from app.repositories.host_profile import HostProfileRepository
from app.repositories.user import UserRepository
from app.schemas.booking import (
    AvailabilityOverrideRequest,
    AvailabilityOverrideResponse,
    HostAvailabilityResponse,
    RecurringAvailabilityResponse,
    SetAvailabilityRequest,
)
from app.schemas.host_profile import (
    CreateHostProfileRequest,
    DanceStyleRequest,
    HostDanceStyleResponse,
    HostProfileResponse,
    UpdateHostProfileRequest,
)
from app.schemas.user import AvatarUploadResponse
from app.services.storage import StorageService, get_storage_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/users", tags=["users"])

# Type alias for database session dependency
DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.post(
    "/me/become-host",
    response_model=HostProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Become a host",
    description="Convert the current user to a host by creating a host profile.",
)
async def become_host(
    request: CreateHostProfileRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> HostProfileResponse:
    """Create a host profile for the current user.

    Creates a new HostProfile linked to the authenticated user and updates
    the user's user_type to include host capabilities.

    Args:
        request: Optional profile data (bio, headline, hourly_rate, location).
        current_user: The authenticated user (injected via auth middleware).
        db: The database session (injected).

    Returns:
        HostProfileResponse with the newly created host profile.

    Raises:
        HTTPException 409: If the user is already a host.
    """
    host_repo = HostProfileRepository(db)

    # Check if user already has a host profile
    existing_profile = await host_repo.get_by_user_id(UUID(str(current_user.id)))
    if existing_profile is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a host",
        )

    # Extract location coordinates if provided
    latitude = None
    longitude = None
    if request.location is not None:
        latitude = request.location.latitude
        longitude = request.location.longitude

    # Create the host profile
    profile = await host_repo.create(
        user_id=UUID(str(current_user.id)),
        bio=request.bio,
        headline=request.headline,
        hourly_rate_cents=request.hourly_rate_cents,
        latitude=latitude,
        longitude=longitude,
    )

    # Update user type to include host
    user_repo = UserRepository(db)
    new_user_type = (
        UserType.BOTH if current_user.user_type == UserType.CLIENT else UserType.HOST
    )
    await user_repo.update_user_type(
        user_id=UUID(str(current_user.id)),
        user_type=new_user_type,
    )

    # Build response (new profile has no dance styles yet)
    return await _build_profile_response(profile, [])


async def _build_profile_response(
    profile,
    dance_styles: list,
) -> HostProfileResponse:
    """Build a HostProfileResponse from a profile and its dance styles.

    Args:
        profile: The HostProfile model instance.
        dance_styles: List of HostDanceStyle records with joined dance_style.

    Returns:
        HostProfileResponse with all profile data.
    """
    dance_style_responses = [
        HostDanceStyleResponse(
            dance_style_id=str(hds.dance_style_id),
            skill_level=hds.skill_level,
            dance_style={
                "id": str(hds.dance_style.id),
                "name": hds.dance_style.name,
                "slug": hds.dance_style.slug,
                "category": hds.dance_style.category,
                "description": hds.dance_style.description,
            },
        )
        for hds in dance_styles
    ]

    return HostProfileResponse(
        id=str(profile.id),
        user_id=str(profile.user_id),
        bio=profile.bio,
        headline=profile.headline,
        hourly_rate_cents=profile.hourly_rate_cents,
        rating_average=profile.rating_average,
        total_reviews=profile.total_reviews,
        total_sessions=profile.total_sessions,
        verification_status=profile.verification_status,
        latitude=None,  # Location is stored as PostGIS geometry
        longitude=None,
        stripe_onboarding_complete=profile.stripe_onboarding_complete,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
        dance_styles=dance_style_responses,
    )


@router.get(
    "/me/host-profile",
    response_model=HostProfileResponse,
    summary="Get current user's host profile",
    description="Get the host profile for the authenticated user.",
)
async def get_my_host_profile(
    current_user: CurrentUser,
    db: DbSession,
) -> HostProfileResponse:
    """Get the current user's host profile.

    Args:
        current_user: The authenticated user (injected via auth middleware).
        db: The database session (injected).

    Returns:
        HostProfileResponse with the user's host profile.

    Raises:
        HTTPException 404: If the user doesn't have a host profile.
    """
    host_repo = HostProfileRepository(db)

    profile = await host_repo.get_by_user_id(UUID(str(current_user.id)))
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not have a host profile",
        )

    # Get dance styles for the profile
    dance_styles = await host_repo.get_dance_styles(UUID(str(profile.id)))

    return await _build_profile_response(profile, dance_styles)


@router.patch(
    "/me/host-profile",
    response_model=HostProfileResponse,
    summary="Update current user's host profile",
    description="Update the host profile for the authenticated user.",
)
async def update_my_host_profile(
    request: UpdateHostProfileRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> HostProfileResponse:
    """Update the current user's host profile.

    Args:
        request: The profile data to update.
        current_user: The authenticated user (injected via auth middleware).
        db: The database session (injected).

    Returns:
        HostProfileResponse with the updated host profile.

    Raises:
        HTTPException 404: If the user doesn't have a host profile.
    """
    host_repo = HostProfileRepository(db)

    profile = await host_repo.get_by_user_id(UUID(str(current_user.id)))
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not have a host profile",
        )

    # Extract location if provided
    latitude = None
    longitude = None
    update_location = False
    if request.location is not None:
        latitude = request.location.latitude
        longitude = request.location.longitude
        update_location = True

    # Update the profile
    updated_profile = await host_repo.update(
        profile_id=UUID(str(profile.id)),
        bio=request.bio,
        headline=request.headline,
        hourly_rate_cents=request.hourly_rate_cents,
        latitude=latitude,
        longitude=longitude,
        _update_location=update_location,
    )

    # Get dance styles for the profile
    dance_styles = await host_repo.get_dance_styles(UUID(str(profile.id)))

    return await _build_profile_response(updated_profile, dance_styles)


@router.post(
    "/me/host-profile/dance-styles",
    response_model=HostDanceStyleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add dance style to host profile",
    description="Add a dance style to the current user's host profile.",
)
async def add_dance_style_to_profile(
    request: DanceStyleRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> HostDanceStyleResponse:
    """Add a dance style to the current user's host profile.

    Args:
        request: The dance style ID and skill level.
        current_user: The authenticated user (injected via auth middleware).
        db: The database session (injected).

    Returns:
        HostDanceStyleResponse with the created dance style association.

    Raises:
        HTTPException 404: If the user doesn't have a host profile or dance style not found.
    """
    host_repo = HostProfileRepository(db)

    profile = await host_repo.get_by_user_id(UUID(str(current_user.id)))
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not have a host profile",
        )

    # Verify dance style exists
    dance_style = await host_repo.get_dance_style_by_id(UUID(request.dance_style_id))
    if dance_style is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dance style not found",
        )

    # Add dance style to profile
    host_dance_style = await host_repo.add_dance_style(
        profile_id=UUID(str(profile.id)),
        dance_style_id=UUID(request.dance_style_id),
        skill_level=request.skill_level,
    )

    return HostDanceStyleResponse(
        dance_style_id=str(host_dance_style.dance_style_id),
        skill_level=host_dance_style.skill_level,
        dance_style={
            "id": str(dance_style.id),
            "name": dance_style.name,
            "slug": dance_style.slug,
            "category": dance_style.category,
            "description": dance_style.description,
        },
    )


@router.delete(
    "/me/host-profile/dance-styles/{dance_style_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove dance style from host profile",
    description="Remove a dance style from the current user's host profile.",
)
async def remove_dance_style_from_profile(
    dance_style_id: str,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    """Remove a dance style from the current user's host profile.

    Args:
        dance_style_id: The dance style UUID to remove.
        current_user: The authenticated user (injected via auth middleware).
        db: The database session (injected).

    Raises:
        HTTPException 404: If the user doesn't have a host profile or dance style not found.
    """
    host_repo = HostProfileRepository(db)

    profile = await host_repo.get_by_user_id(UUID(str(current_user.id)))
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not have a host profile",
        )

    # Try to remove the dance style
    removed = await host_repo.remove_dance_style(
        profile_id=UUID(str(profile.id)),
        dance_style_id=UUID(dance_style_id),
    )

    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dance style not found on host profile",
        )


@router.get(
    "/me/host-profile/availability",
    response_model=HostAvailabilityResponse,
    summary="Get host availability",
    description="Get the current user's host availability schedule including recurring and overrides.",
)
async def get_my_host_availability(
    current_user: CurrentUser,
    db: DbSession,
    start_date: Annotated[
        date | None,
        Query(description="Start date for overrides (default: today)"),
    ] = None,
    end_date: Annotated[
        date | None,
        Query(description="End date for overrides (default: 30 days from start)"),
    ] = None,
) -> HostAvailabilityResponse:
    """Get the current user's host availability schedule.

    Returns recurring weekly availability and any overrides for the date range.

    Args:
        current_user: The authenticated user (injected via auth middleware).
        db: The database session (injected).
        start_date: Start date for overrides (default: today).
        end_date: End date for overrides (default: 30 days from start).

    Returns:
        HostAvailabilityResponse with recurring schedules and overrides.

    Raises:
        HTTPException 404: If the user doesn't have a host profile.
    """
    host_repo = HostProfileRepository(db)
    avail_repo = AvailabilityRepository(db)

    profile = await host_repo.get_by_user_id(UUID(str(current_user.id)))
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not have a host profile",
        )

    # Set default date range if not provided
    if start_date is None:
        start_date = date.today()
    if end_date is None:
        end_date = start_date + timedelta(days=30)

    # Get recurring availability
    recurring = await avail_repo.get_recurring_availability(
        UUID(str(profile.id)),
        active_only=False,  # Show all schedules including inactive
    )

    # Get overrides for the date range
    overrides = await avail_repo.get_overrides_for_date_range(
        UUID(str(profile.id)),
        start_date,
        end_date,
    )

    # Build response
    recurring_response = [
        RecurringAvailabilityResponse(
            id=str(rec.id),
            day_of_week=DayOfWeek(rec.day_of_week),
            start_time=rec.start_time,
            end_time=rec.end_time,
            is_active=rec.is_active,
        )
        for rec in recurring
    ]

    overrides_response = [
        AvailabilityOverrideResponse(
            id=str(ovr.id),
            override_date=ovr.override_date,
            override_type=ovr.override_type,
            start_time=ovr.start_time,
            end_time=ovr.end_time,
            all_day=ovr.all_day,
            reason=ovr.reason,
        )
        for ovr in overrides
    ]

    return HostAvailabilityResponse(
        host_profile_id=str(profile.id),
        recurring=recurring_response,
        overrides=overrides_response,
    )


@router.put(
    "/me/host-profile/availability",
    response_model=HostAvailabilityResponse,
    summary="Set host availability",
    description="Replace the host's weekly recurring availability schedule.",
)
async def set_my_host_availability(
    request: SetAvailabilityRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> HostAvailabilityResponse:
    """Set the current user's host availability schedule.

    This replaces all existing recurring availability with the new schedule.
    Overrides are not affected.

    Args:
        request: The new availability schedule.
        current_user: The authenticated user (injected via auth middleware).
        db: The database session (injected).

    Returns:
        HostAvailabilityResponse with the updated schedule.

    Raises:
        HTTPException 404: If the user doesn't have a host profile.
    """
    host_repo = HostProfileRepository(db)
    avail_repo = AvailabilityRepository(db)

    profile = await host_repo.get_by_user_id(UUID(str(current_user.id)))
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not have a host profile",
        )

    profile_id = UUID(str(profile.id))

    # Clear existing recurring availability
    await avail_repo.clear_recurring_availability(profile_id)

    # Set new recurring availability
    for rec in request.recurring:
        await avail_repo.set_recurring_availability(
            host_profile_id=profile_id,
            day_of_week=rec.day_of_week,
            start_time=rec.start_time,
            end_time=rec.end_time,
            is_active=True,
        )

    # Get updated availability
    recurring = await avail_repo.get_recurring_availability(
        profile_id,
        active_only=False,
    )

    # Get overrides for next 30 days
    start_date = date.today()
    end_date = start_date + timedelta(days=30)
    overrides = await avail_repo.get_overrides_for_date_range(
        profile_id,
        start_date,
        end_date,
    )

    # Build response
    recurring_response = [
        RecurringAvailabilityResponse(
            id=str(rec.id),
            day_of_week=DayOfWeek(rec.day_of_week),
            start_time=rec.start_time,
            end_time=rec.end_time,
            is_active=rec.is_active,
        )
        for rec in recurring
    ]

    overrides_response = [
        AvailabilityOverrideResponse(
            id=str(ovr.id),
            override_date=ovr.override_date,
            override_type=ovr.override_type,
            start_time=ovr.start_time,
            end_time=ovr.end_time,
            all_day=ovr.all_day,
            reason=ovr.reason,
        )
        for ovr in overrides
    ]

    return HostAvailabilityResponse(
        host_profile_id=str(profile.id),
        recurring=recurring_response,
        overrides=overrides_response,
    )


@router.post(
    "/me/host-profile/availability/overrides",
    response_model=AvailabilityOverrideResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add availability override",
    description="Add a one-time availability override (available or blocked).",
)
async def add_availability_override(
    request: AvailabilityOverrideRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> AvailabilityOverrideResponse:
    """Add an availability override for the current user's host profile.

    Use this to add one-time available slots or block time periods.

    Args:
        request: The override details.
        current_user: The authenticated user (injected via auth middleware).
        db: The database session (injected).

    Returns:
        AvailabilityOverrideResponse with the created override.

    Raises:
        HTTPException 404: If the user doesn't have a host profile.
    """
    from app.models.availability import AvailabilityOverrideType

    host_repo = HostProfileRepository(db)
    avail_repo = AvailabilityRepository(db)

    profile = await host_repo.get_by_user_id(UUID(str(current_user.id)))
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not have a host profile",
        )

    profile_id = UUID(str(profile.id))

    # Create the override based on type
    if request.override_type == AvailabilityOverrideType.BLOCKED:
        override = await avail_repo.block_time_slot(
            host_profile_id=profile_id,
            override_date=request.override_date,
            start_time=request.start_time,
            end_time=request.end_time,
            all_day=request.all_day,
            reason=request.reason,
        )
    else:
        override = await avail_repo.add_one_time(
            host_profile_id=profile_id,
            override_date=request.override_date,
            start_time=request.start_time,
            end_time=request.end_time,
            all_day=request.all_day,
            reason=request.reason,
        )

    return AvailabilityOverrideResponse(
        id=str(override.id),
        override_date=override.override_date,
        override_type=override.override_type,
        start_time=override.start_time,
        end_time=override.end_time,
        all_day=override.all_day,
        reason=override.reason,
    )


@router.delete(
    "/me/host-profile/availability/overrides/{override_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete availability override",
    description="Delete an availability override.",
)
async def delete_availability_override(
    override_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    """Delete an availability override from the current user's host profile.

    Args:
        override_id: The override UUID to delete.
        current_user: The authenticated user (injected via auth middleware).
        db: The database session (injected).

    Raises:
        HTTPException 404: If the user doesn't have a host profile or override not found.
    """
    host_repo = HostProfileRepository(db)
    avail_repo = AvailabilityRepository(db)

    profile = await host_repo.get_by_user_id(UUID(str(current_user.id)))
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not have a host profile",
        )

    # Try to delete the override
    deleted = await avail_repo.delete_override(override_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Override not found",
        )


# Type alias for storage service dependency
StorageServiceDep = Annotated[StorageService, Depends(get_storage_service)]


@router.post(
    "/me/avatar",
    response_model=AvatarUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload avatar image",
    description="Upload and process a profile image. Resizes and creates thumbnail.",
)
async def upload_avatar(
    file: Annotated[UploadFile, File(description="Image file (JPEG, PNG, or WebP)")],
    current_user: CurrentUser,
    db: DbSession,
    storage: StorageServiceDep,
) -> AvatarUploadResponse:
    """Upload a new avatar image for the current user.

    The image is resized and a thumbnail is created. Supported formats
    are JPEG, PNG, and WebP. Maximum file size is 5MB.

    Args:
        current_user: The authenticated user (injected via auth middleware).
        db: The database session (injected).
        storage: Storage service for file uploads (injected).
        file: The uploaded image file.

    Returns:
        AvatarUploadResponse with avatar_url and avatar_thumbnail_url.

    Raises:
        HTTPException 400: If the file is invalid or too large.
    """
    # Read file contents
    file_data = await file.read()

    # Get content type from upload or infer from filename
    content_type = file.content_type
    if content_type is None:
        # Try to infer from filename
        filename = file.filename or ""
        if filename.lower().endswith(".jpg") or filename.lower().endswith(".jpeg"):
            content_type = "image/jpeg"
        elif filename.lower().endswith(".png"):
            content_type = "image/png"
        elif filename.lower().endswith(".webp"):
            content_type = "image/webp"
        else:
            content_type = "application/octet-stream"

    # Upload and process the image
    try:
        result = await storage.upload_avatar(
            user_id=str(current_user.id),
            file_data=file_data,
            content_type=content_type,
            filename=file.filename,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    # Update user record with new avatar URLs
    user_repo = UserRepository(db)
    await user_repo.update_avatar(
        user_id=UUID(str(current_user.id)),
        avatar_url=result["avatar_url"],
        avatar_thumbnail_url=result["avatar_thumbnail_url"],
    )

    logger.info(f"Avatar uploaded for user {current_user.id}")

    return AvatarUploadResponse(
        avatar_url=result["avatar_url"],
        avatar_thumbnail_url=result["avatar_thumbnail_url"],
    )


@router.delete(
    "/me/avatar",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete avatar image",
    description="Remove the current user's avatar image.",
)
async def delete_avatar(
    current_user: CurrentUser,
    db: DbSession,
    storage: StorageServiceDep,
) -> None:
    """Delete the current user's avatar image.

    Removes both the main avatar and thumbnail from storage.

    Args:
        current_user: The authenticated user (injected via auth middleware).
        db: The database session (injected).
        storage: Storage service for file operations (injected).

    Raises:
        HTTPException 404: If the user has no avatar.
    """
    if current_user.avatar_url is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User has no avatar",
        )

    # Delete from storage
    await storage.delete_avatar(current_user.avatar_url)

    # Update user record
    user_repo = UserRepository(db)
    await user_repo.delete_avatar(UUID(str(current_user.id)))

    logger.info(f"Avatar deleted for user {current_user.id}")
