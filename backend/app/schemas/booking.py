"""Pydantic schemas for booking operations."""

from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.availability import AvailabilityOverrideType, DayOfWeek
from app.models.booking import BookingStatus

# --- Location Schema ---


class BookingLocationRequest(BaseModel):
    """Schema for booking location."""

    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude (-90 to 90)")
    longitude: float = Field(
        ..., ge=-180.0, le=180.0, description="Longitude (-180 to 180)"
    )
    location_name: str | None = Field(
        default=None, max_length=255, description="Human-readable location name/address"
    )
    location_notes: str | None = Field(
        default=None, max_length=1000, description="Additional location instructions"
    )


# --- Booking Request Schemas ---


class CreateBookingRequest(BaseModel):
    """Schema for creating a new booking.

    Duration must be between 30 and 240 minutes (0.5 to 4 hours).
    """

    host_id: str = Field(..., description="UUID of the host to book")
    dance_style_id: str | None = Field(
        default=None, description="UUID of the dance style (optional)"
    )
    scheduled_start: datetime = Field(
        ..., description="Scheduled start time (with timezone)"
    )
    duration_minutes: int = Field(
        ..., ge=30, le=240, description="Duration in minutes (30-240)"
    )
    location: BookingLocationRequest | None = Field(
        default=None, description="Session location"
    )
    client_notes: str | None = Field(
        default=None, max_length=1000, description="Notes from the client"
    )

    @field_validator("duration_minutes")
    @classmethod
    def validate_duration(cls, v: int) -> int:
        """Validate duration is within allowed range."""
        if v < 30:
            msg = "Duration must be at least 30 minutes"
            raise ValueError(msg)
        if v > 240:
            msg = "Duration cannot exceed 240 minutes (4 hours)"
            raise ValueError(msg)
        return v


class CancelBookingRequest(BaseModel):
    """Schema for cancelling a booking."""

    reason: str | None = Field(
        default=None, max_length=1000, description="Reason for cancellation"
    )


# --- User Summary Schema (for booking responses) ---


class UserSummaryResponse(BaseModel):
    """Condensed user info for booking responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="User UUID")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")


class DanceStyleSummaryResponse(BaseModel):
    """Condensed dance style info for booking responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Dance style UUID")
    name: str = Field(..., description="Dance style name")


# --- Booking Response Schemas ---


class BookingResponse(BaseModel):
    """Schema for booking in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Booking UUID")
    client_id: str = Field(..., description="Client user UUID")
    host_id: str = Field(..., description="Host user UUID")
    host_profile_id: str = Field(..., description="Host profile UUID")
    dance_style_id: str | None = Field(None, description="Dance style UUID")
    status: BookingStatus = Field(..., description="Current booking status")

    # Scheduling
    scheduled_start: datetime = Field(..., description="Scheduled start time")
    scheduled_end: datetime = Field(..., description="Scheduled end time")
    actual_start: datetime | None = Field(None, description="Actual start time")
    actual_end: datetime | None = Field(None, description="Actual end time")
    duration_minutes: int = Field(..., description="Duration in minutes")

    # Location
    latitude: float | None = Field(None, description="Location latitude")
    longitude: float | None = Field(None, description="Location longitude")
    location_name: str | None = Field(None, description="Location name/address")
    location_notes: str | None = Field(None, description="Location notes")

    # Pricing
    hourly_rate_cents: int = Field(
        ..., description="Hourly rate at booking time (cents)"
    )
    amount_cents: int = Field(..., description="Total amount (cents)")
    platform_fee_cents: int = Field(..., description="Platform fee (cents)")
    host_payout_cents: int = Field(..., description="Host payout amount (cents)")

    # Notes
    client_notes: str | None = Field(None, description="Notes from client")
    host_notes: str | None = Field(None, description="Notes from host")

    # Cancellation info
    cancellation_reason: str | None = Field(None, description="Cancellation reason")
    cancelled_by_id: str | None = Field(None, description="Who cancelled (user UUID)")
    cancelled_at: datetime | None = Field(None, description="When cancelled")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class BookingWithDetailsResponse(BookingResponse):
    """Booking response with related entity details."""

    client: UserSummaryResponse | None = Field(None, description="Client details")
    host: UserSummaryResponse | None = Field(None, description="Host details")
    dance_style: DanceStyleSummaryResponse | None = Field(
        None, description="Dance style details"
    )


class BookingListResponse(BaseModel):
    """Paginated response for booking list."""

    items: list[BookingWithDetailsResponse] = Field(..., description="List of bookings")
    total: int = Field(..., description="Total number of bookings")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Results per page")
    total_pages: int = Field(..., description="Total number of pages")


# --- Availability Schemas ---


class AvailabilitySlot(BaseModel):
    """Schema for an availability time slot."""

    start_time: time = Field(..., description="Start time of the slot")
    end_time: time = Field(..., description="End time of the slot")


class AvailabilitySlotWithDate(BaseModel):
    """Schema for an availability slot with date."""

    slot_date: date = Field(..., description="Date of the slot")
    start_time: time = Field(..., description="Start time of the slot")
    end_time: time = Field(..., description="End time of the slot")


class RecurringAvailabilityResponse(BaseModel):
    """Schema for recurring availability in responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Recurring availability UUID")
    day_of_week: DayOfWeek = Field(..., description="Day of week (0=Monday, 6=Sunday)")
    start_time: time = Field(..., description="Start time")
    end_time: time = Field(..., description="End time")
    is_active: bool = Field(..., description="Whether this schedule is active")


class AvailabilityOverrideResponse(BaseModel):
    """Schema for availability override in responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Override UUID")
    override_date: date = Field(..., description="Date of the override")
    override_type: AvailabilityOverrideType = Field(
        ..., description="Type: 'available' or 'blocked'"
    )
    start_time: time | None = Field(None, description="Start time (null for all-day)")
    end_time: time | None = Field(None, description="End time (null for all-day)")
    all_day: bool = Field(..., description="Whether this applies to entire day")
    reason: str | None = Field(None, description="Reason for override")


class RecurringAvailabilityRequest(BaseModel):
    """Schema for setting recurring availability."""

    day_of_week: DayOfWeek = Field(..., description="Day of week (0=Monday, 6=Sunday)")
    start_time: time = Field(..., description="Start time")
    end_time: time = Field(..., description="End time")

    @field_validator("end_time")
    @classmethod
    def validate_end_after_start(cls, v: time, info) -> time:
        """Validate that end_time is after start_time."""
        start = info.data.get("start_time")
        if start and v <= start:
            msg = "end_time must be after start_time"
            raise ValueError(msg)
        return v


class AvailabilityOverrideRequest(BaseModel):
    """Schema for creating an availability override."""

    override_date: date = Field(..., description="Date of the override")
    override_type: AvailabilityOverrideType = Field(
        ..., description="Type: 'available' or 'blocked'"
    )
    start_time: time | None = Field(
        default=None, description="Start time (null for all-day)"
    )
    end_time: time | None = Field(
        default=None, description="End time (null for all-day)"
    )
    all_day: bool = Field(
        default=False, description="Whether this applies to entire day"
    )
    reason: str | None = Field(
        default=None, max_length=500, description="Reason for override"
    )

    @model_validator(mode="after")
    def validate_times(self) -> "AvailabilityOverrideRequest":
        """Validate time logic."""
        # If all_day is True, times should be None
        if self.all_day and (self.start_time is not None or self.end_time is not None):
            msg = "start_time and end_time should be None when all_day is True"
            raise ValueError(msg)

        # If times are provided, end must be after start
        if (
            self.start_time is not None
            and self.end_time is not None
            and self.end_time <= self.start_time
        ):
            msg = "end_time must be after start_time"
            raise ValueError(msg)

        return self


class HostAvailabilityResponse(BaseModel):
    """Response containing host's full availability."""

    host_profile_id: str = Field(..., description="Host profile UUID")
    recurring: list[RecurringAvailabilityResponse] = Field(
        default_factory=list, description="Weekly recurring schedules"
    )
    overrides: list[AvailabilityOverrideResponse] = Field(
        default_factory=list, description="One-time overrides"
    )


class AvailabilityForDateResponse(BaseModel):
    """Response containing available slots for a specific date."""

    availability_date: date = Field(..., description="The date")
    slots: list[AvailabilitySlot] = Field(
        default_factory=list, description="Available time slots"
    )


class AvailabilityForDateRangeResponse(BaseModel):
    """Response containing available slots for a date range."""

    host_profile_id: str = Field(..., description="Host profile UUID")
    start_date: date = Field(..., description="Start of date range")
    end_date: date = Field(..., description="End of date range")
    availability: list[AvailabilityForDateResponse] = Field(
        default_factory=list, description="Available slots by date"
    )
