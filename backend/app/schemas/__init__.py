"""Pydantic schemas for request/response validation."""

from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.booking import (
    AvailabilityForDateRangeResponse,
    AvailabilityForDateResponse,
    AvailabilityOverrideRequest,
    AvailabilityOverrideResponse,
    AvailabilitySlot,
    AvailabilitySlotWithDate,
    BookingListCursorResponse,
    BookingListResponse,
    BookingLocationRequest,
    BookingResponse,
    BookingWithDetailsResponse,
    CancelBookingRequest,
    CreateBookingRequest,
    DanceStyleSummaryResponse,
    HostAvailabilityResponse,
    RecurringAvailabilityRequest,
    RecurringAvailabilityResponse,
    SetAvailabilityRequest,
    UserSummaryResponse,
)
from app.schemas.host_profile import (
    CreateHostProfileRequest,
    DanceStyleRequest,
    DanceStyleResponse,
    HostDanceStyleResponse,
    HostProfileResponse,
    HostProfileSummaryResponse,
    HostProfileWithUserResponse,
    HostSearchRequest,
    HostSearchResponse,
    LocationRequest,
    UpdateHostProfileRequest,
)
from app.schemas.stripe import (
    StripeAccountStatusResponse,
    StripeDashboardLinkResponse,
    StripeOnboardRequest,
    StripeOnboardResponse,
)
from app.schemas.user import UserCreate, UserResponse, UserUpdate

__all__ = [
    # User schemas
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    # Auth schemas
    "RegisterRequest",
    "LoginRequest",
    "TokenResponse",
    "RefreshRequest",
    "RefreshResponse",
    # Host profile schemas
    "CreateHostProfileRequest",
    "UpdateHostProfileRequest",
    "HostProfileResponse",
    "HostProfileWithUserResponse",
    "HostProfileSummaryResponse",
    "HostSearchRequest",
    "HostSearchResponse",
    "LocationRequest",
    "DanceStyleRequest",
    "DanceStyleResponse",
    "HostDanceStyleResponse",
    # Booking schemas
    "CreateBookingRequest",
    "CancelBookingRequest",
    "BookingLocationRequest",
    "BookingResponse",
    "BookingWithDetailsResponse",
    "BookingListResponse",
    "BookingListCursorResponse",
    "UserSummaryResponse",
    "DanceStyleSummaryResponse",
    # Availability schemas
    "AvailabilitySlot",
    "AvailabilitySlotWithDate",
    "RecurringAvailabilityRequest",
    "RecurringAvailabilityResponse",
    "AvailabilityOverrideRequest",
    "AvailabilityOverrideResponse",
    "HostAvailabilityResponse",
    "AvailabilityForDateResponse",
    "AvailabilityForDateRangeResponse",
    "SetAvailabilityRequest",
    # Stripe schemas
    "StripeOnboardRequest",
    "StripeOnboardResponse",
    "StripeAccountStatusResponse",
    "StripeDashboardLinkResponse",
]
