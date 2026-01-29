"""Hosts router for public host profile search and viewing."""

import math
from datetime import date, timedelta
from typing import Annotated
from uuid import UUID

import stripe
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUser
from app.core.geo import extract_coordinates_from_geography
from app.models.host_profile import VerificationStatus
from app.repositories.availability import AvailabilityRepository
from app.repositories.host_profile import HostProfileRepository
from app.repositories.review import ReviewRepository
from app.schemas.booking import (
    AvailabilityForDateRangeResponse,
    AvailabilityForDateResponse,
    AvailabilitySlot,
)
from app.schemas.host_profile import (
    DanceStyleResponse,
    HostDanceStyleResponse,
    HostProfileSummaryResponse,
    HostProfileWithUserResponse,
    HostSearchCursorResponse,
    HostSearchResponse,
)
from app.schemas.review import (
    ReviewListResponse,
    ReviewUserSummary,
    ReviewWithUserResponse,
)
from app.schemas.stripe import (
    StripeAccountStatusResponse,
    StripeOnboardRequest,
    StripeOnboardResponse,
)
from app.schemas.verification import (
    SubmitVerificationRequest,
    SubmitVerificationResponse,
    VerificationDocumentResponse,
    VerificationStatusResponse,
)
from app.services.stripe import StripeAccountStatus, stripe_service
from app.services.verification import get_verification_service

router = APIRouter(prefix="/api/v1/hosts", tags=["hosts"])

# Type alias for database session dependency
DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.get(
    "",
    response_model=HostSearchResponse,
    summary="Search for hosts",
    description="Search for dance hosts with location-based filtering and sorting.",
)
async def search_hosts(
    db: DbSession,
    lat: Annotated[
        float | None,
        Query(
            ge=-90.0,
            le=90.0,
            description="Search center latitude",
        ),
    ] = None,
    lng: Annotated[
        float | None,
        Query(
            ge=-180.0,
            le=180.0,
            description="Search center longitude",
        ),
    ] = None,
    radius_km: Annotated[
        float,
        Query(
            ge=1.0,
            le=500.0,
            description="Search radius in kilometers",
        ),
    ] = 50.0,
    styles: Annotated[
        list[str] | None,
        Query(
            description="Filter by dance style UUIDs",
        ),
    ] = None,
    min_rating: Annotated[
        float | None,
        Query(
            ge=1.0,
            le=5.0,
            description="Minimum rating filter",
        ),
    ] = None,
    max_price: Annotated[
        int | None,
        Query(
            ge=100,
            description="Maximum hourly rate in cents",
        ),
    ] = None,
    verified_only: Annotated[
        bool,
        Query(
            description="Only show verified hosts",
        ),
    ] = False,
    sort_by: Annotated[
        str,
        Query(
            description="Sort field: 'distance', 'rating', 'price', 'reviews', 'relevance'",
        ),
    ] = "distance",
    sort_order: Annotated[
        str,
        Query(
            description="Sort order: 'asc' or 'desc'",
        ),
    ] = "asc",
    page: Annotated[
        int,
        Query(
            ge=1,
            description="Page number (1-indexed)",
        ),
    ] = 1,
    page_size: Annotated[
        int,
        Query(
            ge=1,
            le=100,
            description="Results per page (1-100)",
        ),
    ] = 20,
    q: Annotated[
        str | None,
        Query(
            max_length=200,
            description="Search query for fuzzy matching on host names and bio",
        ),
    ] = None,
) -> HostSearchResponse:
    """Search for dance hosts with filters and geospatial search.

    This endpoint provides location-based host discovery with various
    filtering and sorting options. Supports fuzzy text search using
    PostgreSQL pg_trgm extension.

    Args:
        db: The database session (injected).
        lat: Search center latitude (required for distance sorting).
        lng: Search center longitude (required for distance sorting).
        radius_km: Search radius in kilometers (default 50km).
        styles: List of dance style UUIDs to filter by.
        min_rating: Minimum average rating filter.
        max_price: Maximum hourly rate in cents.
        verified_only: Only return verified hosts.
        sort_by: Sort field - 'distance', 'rating', 'price', 'reviews', or 'relevance'.
        sort_order: Sort order - 'asc' or 'desc'.
        page: Page number (1-indexed).
        page_size: Number of results per page.
        q: Optional search query for fuzzy text matching on host names and bio.

    Returns:
        HostSearchResponse with paginated list of host profiles.
    """
    # Validate sort_by
    allowed_sort_fields = {"distance", "rating", "price", "reviews", "relevance"}
    if sort_by not in allowed_sort_fields:
        # Default to relevance if query provided, otherwise distance
        sort_by = "relevance" if q else "distance"

    # Validate sort_order
    if sort_order not in {"asc", "desc"}:
        sort_order = "asc"

    host_repo = HostProfileRepository(db)

    # Convert style strings to UUIDs if provided
    style_uuids = None
    if styles:
        style_uuids = [UUID(s) for s in styles]

    # Calculate offset from page
    offset = (page - 1) * page_size

    # Map sort_by to repository order_by
    order_by_map = {
        "distance": "distance",
        "rating": "rating",
        "price": "price",
        "reviews": "rating",  # Use rating for reviews too since we don't have a separate field
        "relevance": "relevance",  # For text search ranking
    }
    order_by = order_by_map.get(sort_by, "distance")

    # Execute search
    profiles, total_count = await host_repo.search(
        latitude=lat,
        longitude=lng,
        radius_km=radius_km if lat is not None and lng is not None else None,
        style_ids=style_uuids,
        min_rating=min_rating,
        max_price_cents=max_price,
        order_by=order_by,
        limit=page_size,
        offset=offset,
        query=q,
    )

    # Filter by verification status if requested
    if verified_only:
        profiles = [
            p for p in profiles if p.verification_status == VerificationStatus.VERIFIED
        ]
        # Note: This post-filtering means total_count may be inaccurate for verified_only
        # A production implementation would filter in the repository query

    # Calculate distances if location provided
    items = []
    for profile in profiles:
        # Calculate distance if location provided
        distance_km = None
        if lat is not None and lng is not None and profile.location is not None:
            # We need to compute distance manually since search doesn't return it
            # This is a simplification - in production, the repository would return distances
            distance_km = _calculate_distance_km(lat, lng, profile)

        items.append(
            HostProfileSummaryResponse(
                id=str(profile.id),
                user_id=str(profile.user_id),
                first_name=profile.user.first_name,
                last_name=profile.user.last_name,
                headline=profile.headline,
                hourly_rate_cents=profile.hourly_rate_cents,
                rating_average=profile.rating_average,
                total_reviews=profile.total_reviews,
                verification_status=profile.verification_status,
                distance_km=distance_km,
            )
        )

    # Sort by sort_order if desc
    if sort_order == "desc":
        if sort_by == "distance" and lat is not None and lng is not None:
            items.sort(key=lambda x: x.distance_km or 0, reverse=True)
        elif sort_by == "rating":
            items.sort(key=lambda x: x.rating_average or 0, reverse=True)
        elif sort_by == "price":
            items.sort(key=lambda x: x.hourly_rate_cents, reverse=True)

    # Calculate total pages
    total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1

    return HostSearchResponse(
        items=items,
        total=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/search",
    response_model=HostSearchCursorResponse,
    summary="Search for hosts with cursor pagination",
    description="Search for dance hosts with cursor-based pagination for infinite scroll.",
)
async def search_hosts_cursor(
    db: DbSession,
    cursor: Annotated[
        str | None,
        Query(
            description="Cursor for pagination (host profile ID from previous page)",
        ),
    ] = None,
    lat: Annotated[
        float | None,
        Query(
            ge=-90.0,
            le=90.0,
            description="Search center latitude",
        ),
    ] = None,
    lng: Annotated[
        float | None,
        Query(
            ge=-180.0,
            le=180.0,
            description="Search center longitude",
        ),
    ] = None,
    radius_km: Annotated[
        float,
        Query(
            ge=1.0,
            le=500.0,
            description="Search radius in kilometers",
        ),
    ] = 50.0,
    styles: Annotated[
        list[str] | None,
        Query(
            description="Filter by dance style UUIDs",
        ),
    ] = None,
    min_rating: Annotated[
        float | None,
        Query(
            ge=1.0,
            le=5.0,
            description="Minimum rating filter",
        ),
    ] = None,
    max_price: Annotated[
        int | None,
        Query(
            ge=100,
            description="Maximum hourly rate in cents",
        ),
    ] = None,
    verified_only: Annotated[
        bool,
        Query(
            description="Only show verified hosts",
        ),
    ] = False,
    sort_by: Annotated[
        str,
        Query(
            description="Sort field: 'distance', 'rating', 'price', 'relevance'",
        ),
    ] = "distance",
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=100,
            description="Results per page (1-100)",
        ),
    ] = 20,
    q: Annotated[
        str | None,
        Query(
            max_length=200,
            description="Search query for fuzzy matching on host names and bio",
        ),
    ] = None,
) -> HostSearchCursorResponse:
    """Search for dance hosts with cursor-based pagination.

    This endpoint provides location-based host discovery with cursor-based
    pagination optimized for infinite scroll. Use next_cursor from the
    response to fetch the next page of results.

    Args:
        db: The database session (injected).
        cursor: Cursor from previous page (host profile ID).
        lat: Search center latitude (required for distance sorting).
        lng: Search center longitude (required for distance sorting).
        radius_km: Search radius in kilometers (default 50km).
        styles: List of dance style UUIDs to filter by.
        min_rating: Minimum average rating filter.
        max_price: Maximum hourly rate in cents.
        verified_only: Only return verified hosts.
        sort_by: Sort field - 'distance', 'rating', 'price', or 'relevance'.
        limit: Number of results per page.
        q: Optional search query for fuzzy text matching.

    Returns:
        HostSearchCursorResponse with items, next_cursor, has_more, and total.
    """
    # Validate sort_by
    allowed_sort_fields = {"distance", "rating", "price", "relevance"}
    if sort_by not in allowed_sort_fields:
        sort_by = "relevance" if q else "distance"

    host_repo = HostProfileRepository(db)

    # Convert style strings to UUIDs if provided
    style_uuids = None
    if styles:
        style_uuids = [UUID(s) for s in styles]

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

    # Map sort_by to repository order_by
    order_by_map = {
        "distance": "distance",
        "rating": "rating",
        "price": "price",
        "relevance": "relevance",
    }
    order_by = order_by_map.get(sort_by, "distance")

    # Execute cursor-based search
    profiles, total_count, next_cursor, has_more = await host_repo.search_with_cursor(
        cursor=cursor_uuid,
        latitude=lat,
        longitude=lng,
        radius_km=radius_km if lat is not None and lng is not None else None,
        style_ids=style_uuids,
        min_rating=min_rating,
        max_price_cents=max_price,
        order_by=order_by,
        limit=limit,
        query=q,
    )

    # Filter by verification status if requested
    if verified_only:
        profiles = [
            p for p in profiles if p.verification_status == VerificationStatus.VERIFIED
        ]
        # Note: Post-filtering means total and has_more may be slightly inaccurate

    # Build response items
    items = []
    for profile in profiles:
        # Calculate distance if location provided
        distance_km = None
        if lat is not None and lng is not None and profile.location is not None:
            distance_km = _calculate_distance_km(lat, lng, profile)

        items.append(
            HostProfileSummaryResponse(
                id=str(profile.id),
                user_id=str(profile.user_id),
                first_name=profile.user.first_name,
                last_name=profile.user.last_name,
                headline=profile.headline,
                hourly_rate_cents=profile.hourly_rate_cents,
                rating_average=profile.rating_average,
                total_reviews=profile.total_reviews,
                verification_status=profile.verification_status,
                distance_km=distance_km,
            )
        )

    return HostSearchCursorResponse(
        items=items,
        next_cursor=next_cursor,
        has_more=has_more,
        total=total_count,
    )


def _calculate_distance_km(lat: float, lng: float, profile) -> float | None:
    """Calculate approximate distance in km using Haversine formula.

    This is a simplified calculation. In production, PostGIS would
    handle this more accurately.

    Args:
        lat: Search center latitude.
        lng: Search center longitude.
        profile: The host profile with location.

    Returns:
        Distance in kilometers, or None if location not available.
    """
    # Extract coordinates from PostGIS Geography field
    coords = extract_coordinates_from_geography(profile.location)
    if coords is None:
        return None

    # Haversine formula for distance calculation
    from math import asin, cos, radians, sin, sqrt

    # Convert to radians
    lat1 = radians(lat)
    lat2 = radians(coords.latitude)
    lng1 = radians(lng)
    lng2 = radians(coords.longitude)

    # Haversine formula
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
    c = 2 * asin(sqrt(a))

    # Earth's radius in km
    earth_radius_km = 6371.0

    return earth_radius_km * c


@router.get(
    "/{host_id}/availability",
    response_model=AvailabilityForDateRangeResponse,
    summary="Get host availability",
    description="Get available time slots for a host over a date range.",
)
async def get_host_availability(
    db: DbSession,
    host_id: UUID,
    start_date: Annotated[
        date | None,
        Query(description="Start date (default: today)"),
    ] = None,
    end_date: Annotated[
        date | None,
        Query(description="End date (default: 14 days from start)"),
    ] = None,
) -> AvailabilityForDateRangeResponse:
    """Get available time slots for a host over a date range.

    Returns available slots for each day, accounting for:
    - Recurring weekly availability
    - One-time availability additions
    - Blocked time periods
    - Existing bookings (excluded from available slots)

    Args:
        db: The database session (injected).
        host_id: The host profile UUID.
        start_date: Start date for availability (default: today).
        end_date: End date for availability (default: 14 days from start).

    Returns:
        AvailabilityForDateRangeResponse with available slots by date.

    Raises:
        HTTPException: 404 if host profile not found.
    """
    host_repo = HostProfileRepository(db)
    avail_repo = AvailabilityRepository(db)

    # Verify host exists
    profile = await host_repo.get_by_id(host_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Host profile not found",
        )

    # Set default date range if not provided
    if start_date is None:
        start_date = date.today()
    if end_date is None:
        end_date = start_date + timedelta(days=14)

    # Ensure end_date is after start_date
    if end_date < start_date:
        end_date = start_date

    # Get bookings for the date range to exclude booked slots
    bookings = await avail_repo.get_bookings_for_date_range(
        host_id,
        start_date,
        end_date,
    )

    # Build a dict of booked time ranges by date
    booked_by_date: dict[date, list[tuple]] = {}
    for booking in bookings:
        booking_date = booking.scheduled_start.date()
        if booking_date not in booked_by_date:
            booked_by_date[booking_date] = []
        booked_by_date[booking_date].append(
            (booking.scheduled_start.time(), booking.scheduled_end.time())
        )

    # Get availability for each date
    availability_list: list[AvailabilityForDateResponse] = []
    current_date = start_date
    while current_date <= end_date:
        # Get base availability for the date
        slots = await avail_repo.get_availability_for_date(host_id, current_date)

        # Subtract booked slots
        if current_date in booked_by_date:
            for booked_start, booked_end in booked_by_date[current_date]:
                slots = avail_repo._subtract_time_range(slots, booked_start, booked_end)

        # Convert to response format
        slot_responses = [
            AvailabilitySlot(start_time=slot[0], end_time=slot[1]) for slot in slots
        ]

        availability_list.append(
            AvailabilityForDateResponse(
                availability_date=current_date,
                slots=slot_responses,
            )
        )

        current_date += timedelta(days=1)

    return AvailabilityForDateRangeResponse(
        host_profile_id=str(host_id),
        start_date=start_date,
        end_date=end_date,
        availability=availability_list,
    )


@router.get(
    "/{host_id}",
    response_model=HostProfileWithUserResponse,
    summary="Get host profile by ID",
    description="Get a public host profile by its unique identifier.",
)
async def get_host_profile(
    db: DbSession,
    host_id: UUID,
) -> HostProfileWithUserResponse:
    """Get a host profile by ID.

    Returns the full public profile for a host, including their dance styles,
    rating, and other public information. Excludes sensitive data like
    password_hash.

    Args:
        db: The database session (injected).
        host_id: The host profile UUID.

    Returns:
        HostProfileWithUserResponse with full profile data.

    Raises:
        HTTPException: 404 if host profile not found.
    """
    host_repo = HostProfileRepository(db)

    # Get the host profile
    profile = await host_repo.get_by_id(host_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Host profile not found",
        )

    # Get dance styles for the profile
    dance_styles = await host_repo.get_dance_styles(host_id)

    # Build dance styles response
    dance_styles_response = [
        HostDanceStyleResponse(
            dance_style_id=str(hds.dance_style_id),
            skill_level=hds.skill_level,
            dance_style=DanceStyleResponse(
                id=str(hds.dance_style.id),
                name=hds.dance_style.name,
                slug=hds.dance_style.slug,
                category=hds.dance_style.category,
                description=hds.dance_style.description,
            ),
        )
        for hds in dance_styles
    ]

    # Extract coordinates from PostGIS location
    coords = extract_coordinates_from_geography(profile.location)
    latitude = coords.latitude if coords else None
    longitude = coords.longitude if coords else None

    # Build and return response
    return HostProfileWithUserResponse(
        id=str(profile.id),
        user_id=str(profile.user_id),
        bio=profile.bio,
        headline=profile.headline,
        hourly_rate_cents=profile.hourly_rate_cents,
        rating_average=profile.rating_average,
        total_reviews=profile.total_reviews,
        total_sessions=profile.total_sessions,
        verification_status=profile.verification_status,
        latitude=latitude,
        longitude=longitude,
        stripe_onboarding_complete=profile.stripe_onboarding_complete,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
        dance_styles=dance_styles_response,
        first_name=profile.user.first_name,
        last_name=profile.user.last_name,
    )


@router.post(
    "/stripe/onboard",
    response_model=StripeOnboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Initiate Stripe Connect onboarding",
    description="Start the Stripe Connect onboarding process for a host.",
)
async def initiate_stripe_onboarding(
    db: DbSession,
    current_user: CurrentUser,
    request: StripeOnboardRequest,
) -> StripeOnboardResponse:
    """Initiate Stripe Connect onboarding for a host.

    Creates a Stripe Connect Express account if the host doesn't have one,
    then returns an onboarding URL for the host to complete their setup.

    Args:
        db: The database session (injected).
        current_user: The authenticated user (injected).
        request: The onboarding request with redirect URLs.

    Returns:
        StripeOnboardResponse with account ID and onboarding URL.

    Raises:
        HTTPException: 404 if user is not a host.
        HTTPException: 500 if Stripe API fails.
    """
    host_repo = HostProfileRepository(db)

    # Get the host profile
    profile = await host_repo.get_by_user_id(current_user.id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Host profile not found. Please become a host first.",
        )

    try:
        # Create Stripe Connect account if not exists
        if not profile.stripe_account_id:
            account_id = await stripe_service.create_connect_account(
                email=current_user.email,
            )
            # Update host profile with account ID
            await host_repo.update(
                profile.id,
                stripe_account_id=account_id,
            )
        else:
            account_id = profile.stripe_account_id

        # Create onboarding link
        onboarding_url = await stripe_service.create_account_link(
            account_id=account_id,
            refresh_url=str(request.refresh_url),
            return_url=str(request.return_url),
        )

        return StripeOnboardResponse(
            account_id=account_id,
            onboarding_url=onboarding_url,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e
    except stripe.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stripe error: {e.user_message or str(e)}",
        ) from e


@router.get(
    "/stripe/status",
    response_model=StripeAccountStatusResponse,
    summary="Get Stripe account status",
    description="Get the current status of the host's Stripe Connect account.",
)
async def get_stripe_account_status(
    db: DbSession,
    current_user: CurrentUser,
) -> StripeAccountStatusResponse:
    """Get the status of a host's Stripe Connect account.

    Args:
        db: The database session (injected).
        current_user: The authenticated user (injected).

    Returns:
        StripeAccountStatusResponse with account status details.

    Raises:
        HTTPException: 404 if user is not a host or has no Stripe account.
        HTTPException: 500 if Stripe API fails.
    """
    host_repo = HostProfileRepository(db)

    # Get the host profile
    profile = await host_repo.get_by_user_id(current_user.id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Host profile not found.",
        )

    if not profile.stripe_account_id:
        return StripeAccountStatusResponse(
            account_id="",
            status=StripeAccountStatus.NOT_CREATED,
            charges_enabled=False,
            payouts_enabled=False,
            details_submitted=False,
            requirements_due=[],
        )

    try:
        account_status = await stripe_service.get_account_status(
            profile.stripe_account_id
        )

        # Update onboarding status if now complete
        if (
            account_status.charges_enabled
            and account_status.payouts_enabled
            and not profile.stripe_onboarding_complete
        ):
            await host_repo.update(
                profile.id,
                stripe_onboarding_complete=True,
            )

        return StripeAccountStatusResponse(
            account_id=account_status.account_id,
            status=account_status.status,
            charges_enabled=account_status.charges_enabled,
            payouts_enabled=account_status.payouts_enabled,
            details_submitted=account_status.details_submitted,
            requirements_due=account_status.requirements_due,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e
    except stripe.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stripe error: {e.user_message or str(e)}",
        ) from e


# Type aliases for reviews query parameters
ReviewCursorQuery = Annotated[
    str | None,
    Query(description="Cursor for pagination (review ID from previous page)"),
]
ReviewLimitQuery = Annotated[
    int,
    Query(ge=1, le=50, description="Maximum number of reviews to return (1-50)"),
]


@router.get(
    "/{host_id}/reviews",
    response_model=ReviewListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get reviews for a host",
    description="Get reviews for a host profile with cursor-based pagination.",
)
async def get_host_reviews(
    db: DbSession,
    host_id: UUID,
    cursor: ReviewCursorQuery = None,
    limit: ReviewLimitQuery = 20,
) -> ReviewListResponse:
    """Get reviews for a host profile.

    Reviews are public and can be viewed by anyone.
    Results are ordered by created_at descending (newest first).

    Args:
        db: The database session (injected).
        host_id: The host profile UUID.
        cursor: Cursor for pagination (review ID from previous page).
        limit: Maximum number of reviews to return (1-50).

    Returns:
        ReviewListResponse with reviews and pagination info.

    Raises:
        HTTPException: 404 if host profile not found.
    """
    host_repo = HostProfileRepository(db)
    review_repo = ReviewRepository(db)

    # Verify host exists
    profile = await host_repo.get_by_id(host_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Host profile not found",
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

    # Fetch reviews with one extra to check for more pages
    reviews = await review_repo.get_for_host_profile(
        host_profile_id=host_id,
        limit=limit + 1,
        cursor=cursor_uuid,
    )

    # Determine if there are more results
    has_more = len(reviews) > limit
    if has_more:
        reviews = reviews[:limit]

    # Get total count
    total = await review_repo.count_for_host_profile(host_id)

    # Build response items
    items = [
        ReviewWithUserResponse(
            id=review.id,
            booking_id=review.booking_id,
            reviewer_id=review.reviewer_id,
            reviewee_id=review.reviewee_id,
            rating=review.rating,
            comment=review.comment,
            host_response=review.host_response,
            host_responded_at=review.host_responded_at,
            created_at=review.created_at,
            updated_at=review.updated_at,
            reviewer=ReviewUserSummary(
                id=review.reviewer.id,
                first_name=review.reviewer.first_name,
                last_name=review.reviewer.last_name,
            )
            if review.reviewer
            else None,
            reviewee=ReviewUserSummary(
                id=review.reviewee.id,
                first_name=review.reviewee.first_name,
                last_name=review.reviewee.last_name,
            )
            if review.reviewee
            else None,
        )
        for review in reviews
    ]

    # Set next cursor to the last item's ID if there are more results
    next_cursor = reviews[-1].id if reviews and has_more else None

    return ReviewListResponse(
        items=items,
        next_cursor=next_cursor,
        has_more=has_more,
        total=total,
    )


# ==================== Verification Endpoints ====================


@router.post(
    "/verification/submit",
    response_model=SubmitVerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit verification documents",
    description="Submit ID documents for host identity verification.",
)
async def submit_verification(
    db: DbSession,
    current_user: CurrentUser,
    request: SubmitVerificationRequest,
) -> SubmitVerificationResponse:
    """Submit verification documents for a host profile.

    Hosts must submit identity verification documents before they
    can be verified. Once submitted, the verification status changes
    to PENDING until an admin reviews the documents.

    Args:
        db: The database session (injected).
        current_user: The authenticated user (injected).
        request: The verification submission request.

    Returns:
        SubmitVerificationResponse with submission status.

    Raises:
        HTTPException: 404 if user is not a host.
        HTTPException: 400 if already verified or pending.
    """
    host_repo = HostProfileRepository(db)
    verification_service = get_verification_service(db)

    # Get the host profile
    profile = await host_repo.get_by_user_id(current_user.id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Host profile not found. Please become a host first.",
        )

    # Submit verification
    result = await verification_service.submit_verification(
        host_profile_id=profile.id,
        document_type=request.document_type,
        document_url=request.document_url,
        document_number=request.document_number,
        notes=request.notes,
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error_message,
        )

    return SubmitVerificationResponse(
        success=True,
        document_id=result.document_id,
        message="Verification documents submitted successfully. Please allow 1-3 business days for review.",
    )


@router.get(
    "/verification/status",
    response_model=VerificationStatusResponse,
    summary="Get verification status",
    description="Get the current verification status for the authenticated host.",
)
async def get_verification_status(
    db: DbSession,
    current_user: CurrentUser,
) -> VerificationStatusResponse:
    """Get the verification status for the authenticated host.

    Returns the current verification status, whether the host can
    submit new documents, and any rejection reason if applicable.

    Args:
        db: The database session (injected).
        current_user: The authenticated user (injected).

    Returns:
        VerificationStatusResponse with status and documents.

    Raises:
        HTTPException: 404 if user is not a host.
    """
    host_repo = HostProfileRepository(db)
    verification_service = get_verification_service(db)

    # Get the host profile
    profile = await host_repo.get_by_user_id(current_user.id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Host profile not found. Please become a host first.",
        )

    # Get verification status
    status_result = await verification_service.get_verification_status(profile.id)
    if status_result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Host profile not found.",
        )

    # Convert documents to response format
    documents = [
        VerificationDocumentResponse(
            id=doc.id,
            document_type=doc.document_type,
            document_url=doc.document_url,
            document_number=doc.document_number,
            notes=doc.notes,
            reviewer_notes=doc.reviewer_notes,
            reviewed_at=doc.reviewed_at,
            created_at=doc.created_at,
        )
        for doc in status_result.documents
    ]

    return VerificationStatusResponse(
        status=status_result.status,
        can_submit=status_result.can_submit,
        rejection_reason=status_result.rejection_reason,
        documents=documents,
    )
