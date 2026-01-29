"""Users router for user profile management operations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUser
from app.models.user import UserType
from app.repositories.host_profile import HostProfileRepository
from app.repositories.user import UserRepository
from app.schemas.host_profile import (
    CreateHostProfileRequest,
    DanceStyleRequest,
    HostDanceStyleResponse,
    HostProfileResponse,
    UpdateHostProfileRequest,
)

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
