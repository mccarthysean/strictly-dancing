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
from app.schemas.host_profile import CreateHostProfileRequest, HostProfileResponse

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
        dance_styles=[],  # New profile has no dance styles yet
    )
