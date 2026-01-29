"""Bookings router for booking management operations."""

from datetime import timedelta
from typing import Annotated
from uuid import UUID

import stripe
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import CurrentUser
from app.models.booking import BookingStatus
from app.repositories.availability import AvailabilityRepository
from app.repositories.booking import BookingRepository
from app.repositories.host_profile import HostProfileRepository
from app.schemas.booking import (
    BookingResponse,
    BookingWithDetailsResponse,
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
