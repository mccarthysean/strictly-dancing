"""Bookings router for booking management operations."""

import contextlib
from datetime import datetime, timedelta
from typing import Annotated
from uuid import UUID

import stripe
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import CurrentUser
from app.models.booking import BookingStatus
from app.repositories.availability import AvailabilityRepository
from app.repositories.booking import BookingRepository
from app.repositories.host_profile import HostProfileRepository
from app.schemas.booking import (
    BookingListCursorResponse,
    BookingResponse,
    BookingWithDetailsResponse,
    CancelBookingRequest,
    CreateBookingRequest,
    DanceStyleSummaryResponse,
    UserSummaryResponse,
)
from app.services.stripe import stripe_service

router = APIRouter(prefix="/api/v1/bookings", tags=["bookings"])

# Type alias for database session dependency
DbSession = Annotated[AsyncSession, Depends(get_db)]

# Platform fee percentage (e.g., 15% = 1500 basis points)
PLATFORM_FEE_PERCENTAGE = 15  # 15%


def _calculate_platform_fee(amount_cents: int) -> int:
    """Calculate the platform fee from total amount.

    Args:
        amount_cents: Total booking amount in cents.

    Returns:
        Platform fee in cents (15% of total).
    """
    return int(amount_cents * PLATFORM_FEE_PERCENTAGE / 100)


def _build_booking_response(booking, *, include_details: bool = True):
    """Build a booking response from a Booking model.

    Args:
        booking: The Booking model instance.
        include_details: If True, include related entity details.

    Returns:
        BookingWithDetailsResponse or BookingResponse.
    """
    base_response = {
        "id": str(booking.id),
        "client_id": str(booking.client_id),
        "host_id": str(booking.host_id),
        "host_profile_id": str(booking.host_profile_id),
        "dance_style_id": str(booking.dance_style_id)
        if booking.dance_style_id
        else None,
        "status": booking.status,
        "scheduled_start": booking.scheduled_start,
        "scheduled_end": booking.scheduled_end,
        "actual_start": booking.actual_start,
        "actual_end": booking.actual_end,
        "duration_minutes": booking.duration_minutes,
        "latitude": None,  # TODO: Extract from PostGIS location
        "longitude": None,
        "location_name": booking.location_name,
        "location_notes": booking.location_notes,
        "hourly_rate_cents": booking.hourly_rate_cents,
        "amount_cents": booking.amount_cents,
        "platform_fee_cents": booking.platform_fee_cents,
        "host_payout_cents": booking.host_payout_cents,
        "client_notes": booking.client_notes,
        "host_notes": booking.host_notes,
        "cancellation_reason": booking.cancellation_reason,
        "cancelled_by_id": str(booking.cancelled_by_id)
        if booking.cancelled_by_id
        else None,
        "cancelled_at": booking.cancelled_at,
        "created_at": booking.created_at,
        "updated_at": booking.updated_at,
    }

    if include_details and booking.client is not None and booking.host is not None:
        client = UserSummaryResponse(
            id=str(booking.client.id),
            first_name=booking.client.first_name,
            last_name=booking.client.last_name,
        )
        host = UserSummaryResponse(
            id=str(booking.host.id),
            first_name=booking.host.first_name,
            last_name=booking.host.last_name,
        )
        dance_style = None
        if booking.dance_style is not None:
            dance_style = DanceStyleSummaryResponse(
                id=str(booking.dance_style.id),
                name=booking.dance_style.name,
            )
        return BookingWithDetailsResponse(
            **base_response,
            client=client,
            host=host,
            dance_style=dance_style,
        )

    return BookingResponse(**base_response)


@router.post(
    "",
    response_model=BookingWithDetailsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new booking",
    description="Create a new booking with payment authorization.",
)
async def create_booking(
    db: DbSession,
    current_user: CurrentUser,
    request: CreateBookingRequest,
) -> BookingWithDetailsResponse:
    """Create a new booking with Stripe payment hold.

    This endpoint:
    1. Validates the host exists and has completed Stripe onboarding
    2. Validates the requested time slot is available
    3. Calculates the total amount and platform fee
    4. Creates a Stripe PaymentIntent with manual capture (hold)
    5. Creates a pending booking record

    The payment is authorized but not captured until the session is completed.

    Args:
        db: The database session (injected).
        current_user: The authenticated user (injected).
        request: The booking request data.

    Returns:
        BookingWithDetailsResponse with the created booking.

    Raises:
        HTTPException: 400 if validation fails (invalid host, unavailable slot, etc.)
        HTTPException: 404 if host profile not found.
        HTTPException: 409 if time slot is not available.
        HTTPException: 500 if Stripe API fails.
    """
    settings = get_settings()
    host_repo = HostProfileRepository(db)
    availability_repo = AvailabilityRepository(db)
    booking_repo = BookingRepository(db)

    # Parse host_id
    try:
        host_profile_id = UUID(request.host_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid host_id format",
        ) from e

    # Get the host profile
    host_profile = await host_repo.get_by_id(host_profile_id)
    if host_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Host profile not found",
        )

    # Ensure user is not booking themselves
    if host_profile.user_id == str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot book yourself",
        )

    # Verify host has completed Stripe onboarding (skip for testing without Stripe)
    if settings.stripe_secret_key and not host_profile.stripe_onboarding_complete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Host has not completed payment setup",
        )

    # Check host has an hourly rate set
    if host_profile.hourly_rate_cents is None or host_profile.hourly_rate_cents <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Host has not set an hourly rate",
        )

    # Validate dance_style_id if provided
    dance_style_id = None
    if request.dance_style_id:
        try:
            dance_style_id = UUID(request.dance_style_id)
            dance_style = await host_repo.get_dance_style_by_id(dance_style_id)
            if dance_style is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid dance style ID",
                )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid dance_style_id format",
            ) from e

    # Calculate scheduled end time
    scheduled_end = request.scheduled_start + timedelta(
        minutes=request.duration_minutes
    )

    # Check availability - validates against host's schedule and existing bookings
    is_available = await availability_repo.is_available_for_slot(
        host_profile_id=host_profile_id,
        start_datetime=request.scheduled_start,
        end_datetime=scheduled_end,
    )

    if not is_available:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The requested time slot is not available",
        )

    # Calculate pricing
    # Amount = (hourly_rate / 60) * duration_minutes
    hourly_rate_cents = host_profile.hourly_rate_cents
    amount_cents = int(hourly_rate_cents * request.duration_minutes / 60)
    platform_fee_cents = _calculate_platform_fee(amount_cents)
    host_payout_cents = amount_cents - platform_fee_cents

    # Create Stripe PaymentIntent with manual capture
    stripe_payment_intent_id = None
    if settings.stripe_secret_key and host_profile.stripe_account_id:
        try:
            payment_intent_id, _ = await stripe_service.create_payment_intent(
                amount_cents=amount_cents,
                currency="usd",
                connected_account_id=host_profile.stripe_account_id,
                platform_fee_cents=platform_fee_cents,
                metadata={
                    "client_id": str(current_user.id),
                    "host_id": str(host_profile.user_id),
                    "host_profile_id": str(host_profile_id),
                },
                capture_method="manual",
            )
            stripe_payment_intent_id = payment_intent_id
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Payment processing error: {e!s}",
            ) from e
        except stripe.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Stripe error: {e.user_message if hasattr(e, 'user_message') else e!s}",
            ) from e

    # Create the booking record
    booking = await booking_repo.create(
        client_id=current_user.id,
        host_id=UUID(host_profile.user_id),
        host_profile_id=host_profile_id,
        scheduled_start=request.scheduled_start,
        scheduled_end=scheduled_end,
        duration_minutes=request.duration_minutes,
        hourly_rate_cents=hourly_rate_cents,
        amount_cents=amount_cents,
        platform_fee_cents=platform_fee_cents,
        host_payout_cents=host_payout_cents,
        dance_style_id=dance_style_id,
        location=None,  # TODO: Create PostGIS point from request.location
        location_name=request.location.location_name if request.location else None,
        location_notes=request.location.location_notes if request.location else None,
        client_notes=request.client_notes,
        stripe_payment_intent_id=stripe_payment_intent_id,
    )

    # Reload with relationships for response
    booking = await booking_repo.get_by_id(booking.id, load_relationships=True)

    return _build_booking_response(booking, include_details=True)


@router.post(
    "/{booking_id}/confirm",
    response_model=BookingWithDetailsResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm a booking",
    description="Host confirms a pending booking request.",
)
async def confirm_booking(
    booking_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> BookingWithDetailsResponse:
    """Confirm a pending booking.

    This endpoint allows a host to confirm a booking request from a client.
    Only the host can confirm their own bookings.

    Args:
        booking_id: The booking's unique identifier.
        db: The database session (injected).
        current_user: The authenticated user (injected).

    Returns:
        BookingWithDetailsResponse with the confirmed booking.

    Raises:
        HTTPException: 400 if booking is not in pending status.
        HTTPException: 403 if user is not the host of the booking.
        HTTPException: 404 if booking not found.
    """
    booking_repo = BookingRepository(db)

    # Get the booking
    booking = await booking_repo.get_by_id(booking_id, load_relationships=True)
    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    # Verify that the current user is the host
    if booking.host_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the host can confirm this booking",
        )

    # Verify the booking is in pending status
    if booking.status != BookingStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending bookings can be confirmed",
        )

    # Update the status to confirmed
    booking = await booking_repo.update_status(booking_id, BookingStatus.CONFIRMED)

    # Reload with relationships for response
    booking = await booking_repo.get_by_id(booking_id, load_relationships=True)

    return _build_booking_response(booking, include_details=True)


@router.post(
    "/{booking_id}/cancel",
    response_model=BookingWithDetailsResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel a booking",
    description="Client or host cancels a pending or confirmed booking.",
)
async def cancel_booking(
    booking_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
    request: CancelBookingRequest | None = None,
) -> BookingWithDetailsResponse:
    """Cancel a booking and release payment authorization.

    This endpoint allows either the client or host to cancel a booking.
    When cancelled:
    - The Stripe PaymentIntent authorization is released
    - The booking status is set to CANCELLED
    - The cancellation details are recorded

    Args:
        booking_id: The booking's unique identifier.
        db: The database session (injected).
        current_user: The authenticated user (injected).
        request: Optional cancellation request with reason.

    Returns:
        BookingWithDetailsResponse with the cancelled booking.

    Raises:
        HTTPException: 400 if booking cannot be cancelled (already cancelled/completed).
        HTTPException: 403 if user is not the client or host of the booking.
        HTTPException: 404 if booking not found.
    """
    settings = get_settings()
    booking_repo = BookingRepository(db)

    # Get the booking
    booking = await booking_repo.get_by_id(booking_id, load_relationships=True)
    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    # Verify that the current user is either the client or the host
    user_id_str = str(current_user.id)
    is_client = booking.client_id == user_id_str
    is_host = booking.host_id == user_id_str

    if not is_client and not is_host:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the client or host can cancel this booking",
        )

    # Verify the booking can be cancelled (pending or confirmed)
    cancellable_statuses = [BookingStatus.PENDING, BookingStatus.CONFIRMED]
    if booking.status not in cancellable_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel a booking with status '{booking.status.value}'",
        )

    # Release the Stripe authorization if there's a payment intent
    # If cancellation fails, the authorization will expire anyway
    if booking.stripe_payment_intent_id and settings.stripe_secret_key:
        with contextlib.suppress(stripe.StripeError):
            await stripe_service.cancel_payment_intent(booking.stripe_payment_intent_id)

    # Update the booking status to cancelled
    cancellation_reason = request.reason if request else None
    booking = await booking_repo.update_status(
        booking_id,
        BookingStatus.CANCELLED,
        cancelled_by_id=current_user.id,
        cancellation_reason=cancellation_reason,
    )

    # Reload with relationships for response
    booking = await booking_repo.get_by_id(booking_id, load_relationships=True)

    return _build_booking_response(booking, include_details=True)


@router.post(
    "/{booking_id}/complete",
    response_model=BookingWithDetailsResponse,
    status_code=status.HTTP_200_OK,
    summary="Complete a booking session",
    description="Host completes an in-progress session, capturing payment and transferring funds.",
)
async def complete_booking(
    booking_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> BookingWithDetailsResponse:
    """Complete a booking session and process payment.

    This endpoint:
    1. Validates the booking is in IN_PROGRESS status
    2. Captures the Stripe PaymentIntent (charges the client)
    3. Creates a Transfer to the host's connected account
    4. Updates the booking status to COMPLETED

    Args:
        booking_id: The booking's unique identifier.
        db: The database session (injected).
        current_user: The authenticated user (injected).

    Returns:
        BookingWithDetailsResponse with the completed booking.

    Raises:
        HTTPException: 400 if booking is not in IN_PROGRESS status.
        HTTPException: 403 if user is not the host of the booking.
        HTTPException: 404 if booking not found.
        HTTPException: 500 if Stripe payment capture fails.
    """
    settings = get_settings()
    booking_repo = BookingRepository(db)
    host_repo = HostProfileRepository(db)

    # Get the booking
    booking = await booking_repo.get_by_id(booking_id, load_relationships=True)
    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    # Verify that the current user is the host
    if booking.host_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the host can complete this booking",
        )

    # Verify the booking is in IN_PROGRESS status
    if booking.status != BookingStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only in_progress bookings can be completed",
        )

    # Get the host profile for Stripe account
    host_profile = await host_repo.get_by_id(UUID(booking.host_profile_id))
    stripe_transfer_id = None

    # Capture the payment and create transfer if Stripe is configured
    if booking.stripe_payment_intent_id and settings.stripe_secret_key:
        try:
            # Capture the PaymentIntent (charges the client)
            capture_success = await stripe_service.capture_payment_intent(
                booking.stripe_payment_intent_id
            )

            if not capture_success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to capture payment",
                )

            # Create transfer to host's connected account
            if host_profile and host_profile.stripe_account_id:
                stripe_transfer_id = await stripe_service.create_transfer(
                    amount_cents=booking.host_payout_cents,
                    destination_account_id=host_profile.stripe_account_id,
                    metadata={
                        "booking_id": str(booking_id),
                        "client_id": booking.client_id,
                        "host_id": booking.host_id,
                    },
                )

        except stripe.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Payment processing error: {e.user_message if hasattr(e, 'user_message') else e!s}",
            ) from e

    # Update the booking status to COMPLETED
    booking = await booking_repo.update_status(
        booking_id,
        BookingStatus.COMPLETED,
        stripe_transfer_id=stripe_transfer_id,
    )

    # Reload with relationships for response
    booking = await booking_repo.get_by_id(booking_id, load_relationships=True)

    return _build_booking_response(booking, include_details=True)


# Type aliases for query parameters with validation
StatusFilterQuery = Annotated[
    list[BookingStatus] | None,
    Query(
        alias="status", description="Filter by booking status (can specify multiple)"
    ),
]
StartDateQuery = Annotated[
    datetime | None,
    Query(description="Filter bookings scheduled after this datetime (ISO 8601)"),
]
EndDateQuery = Annotated[
    datetime | None,
    Query(description="Filter bookings scheduled before this datetime (ISO 8601)"),
]
CursorQuery = Annotated[
    str | None,
    Query(description="Cursor for pagination (booking ID from previous page)"),
]
LimitQuery = Annotated[
    int,
    Query(ge=1, le=100, description="Maximum number of bookings to return (1-100)"),
]


@router.get(
    "",
    response_model=BookingListCursorResponse,
    status_code=status.HTTP_200_OK,
    summary="List bookings for current user",
    description="Get a list of bookings for the authenticated user with cursor-based pagination.",
)
async def list_bookings(
    db: DbSession,
    current_user: CurrentUser,
    status_filter: StatusFilterQuery = None,
    start_date: StartDateQuery = None,
    end_date: EndDateQuery = None,
    cursor: CursorQuery = None,
    limit: LimitQuery = 20,
) -> BookingListCursorResponse:
    """Get bookings for the authenticated user.

    This endpoint returns all bookings where the authenticated user is either
    the client or the host. Results use cursor-based pagination for efficient
    traversal of large result sets.

    Filters:
    - status: Filter by one or more booking statuses
    - start_date: Only include bookings scheduled on or after this datetime
    - end_date: Only include bookings scheduled on or before this datetime

    Pagination:
    - Results are ordered by scheduled_start descending (newest first)
    - Use the cursor parameter with the ID from the last item to get the next page
    - The response includes has_more and next_cursor for pagination

    Args:
        db: The database session (injected).
        current_user: The authenticated user (injected).
        status_filter: Optional status filter(s).
        start_date: Optional minimum scheduled_start datetime.
        end_date: Optional maximum scheduled_start datetime.
        cursor: Cursor from previous page (booking ID).
        limit: Maximum number of results to return.

    Returns:
        BookingListCursorResponse with bookings and pagination info.
    """
    booking_repo = BookingRepository(db)

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

    # Fetch bookings with one extra to check for more pages
    bookings = await booking_repo.get_for_user_with_cursor(
        user_id=current_user.id,
        status=status_filter,
        start_date=start_date,
        end_date=end_date,
        cursor=cursor_uuid,
        limit=limit,
        load_relationships=True,
    )

    # Determine if there are more results
    has_more = len(bookings) > limit
    if has_more:
        # Remove the extra item used for checking
        bookings = bookings[:limit]

    # Build response items
    items = [
        _build_booking_response(booking, include_details=True) for booking in bookings
    ]

    # Set next cursor to the last item's ID if there are results
    next_cursor = str(bookings[-1].id) if bookings and has_more else None

    return BookingListCursorResponse(
        items=items,
        next_cursor=next_cursor,
        has_more=has_more,
        limit=limit,
    )
