"""Pydantic schemas for host profile operations."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.dance_style import DanceStyleCategory
from app.models.host_profile import VerificationStatus


class CoordinatesBase(BaseModel):
    """Base schema for coordinate validation.

    Validates latitude and longitude ranges:
    - Latitude: -90 to 90 degrees
    - Longitude: -180 to 180 degrees
    """

    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude (-90 to 90)")
    longitude: float = Field(
        ..., ge=-180.0, le=180.0, description="Longitude (-180 to 180)"
    )


class LocationRequest(CoordinatesBase):
    """Schema for location in requests."""

    pass


class DanceStyleRequest(BaseModel):
    """Schema for adding a dance style to a host profile."""

    dance_style_id: str = Field(..., description="UUID of the dance style")
    skill_level: int = Field(
        ..., ge=1, le=5, description="Skill level (1=beginner, 5=expert)"
    )


class DanceStyleResponse(BaseModel):
    """Schema for dance style in responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Dance style UUID")
    name: str = Field(..., description="Dance style name")
    slug: str = Field(..., description="URL-friendly slug")
    category: DanceStyleCategory = Field(..., description="Dance style category")
    description: str | None = Field(None, description="Dance style description")


class HostDanceStyleResponse(BaseModel):
    """Schema for host's dance style with skill level."""

    model_config = ConfigDict(from_attributes=True)

    dance_style_id: str = Field(..., description="Dance style UUID")
    skill_level: int = Field(..., description="Skill level (1-5)")
    dance_style: DanceStyleResponse = Field(..., description="Dance style details")


# --- Create/Update Request Schemas ---


class CreateHostProfileRequest(BaseModel):
    """Schema for creating a new host profile.

    Used when a user becomes a host. All fields are optional at creation,
    with sensible defaults applied.
    """

    bio: str | None = Field(
        default=None, max_length=2000, description="Host's biography/description"
    )
    headline: str | None = Field(
        default=None, max_length=200, description="Short tagline for profile display"
    )
    hourly_rate_cents: int = Field(
        default=5000, ge=100, le=100000, description="Hourly rate in cents ($1-$1000)"
    )
    location: LocationRequest | None = Field(
        default=None, description="Host's location (latitude/longitude)"
    )


class UpdateHostProfileRequest(BaseModel):
    """Schema for updating a host profile.

    All fields are optional - only provided fields will be updated.
    """

    bio: str | None = Field(
        default=None, max_length=2000, description="Host's biography/description"
    )
    headline: str | None = Field(
        default=None, max_length=200, description="Short tagline for profile display"
    )
    hourly_rate_cents: int | None = Field(
        default=None, ge=100, le=100000, description="Hourly rate in cents ($1-$1000)"
    )
    location: LocationRequest | None = Field(
        default=None, description="Host's location (latitude/longitude)"
    )


# --- Response Schemas ---


class HostProfileResponse(BaseModel):
    """Schema for host profile in API responses.

    Includes all public host profile information.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Host profile UUID")
    user_id: str = Field(..., description="Associated user UUID")
    bio: str | None = Field(None, description="Host's biography/description")
    headline: str | None = Field(None, description="Short tagline")
    hourly_rate_cents: int = Field(..., description="Hourly rate in cents")
    rating_average: float | None = Field(None, description="Average rating (1.00-5.00)")
    total_reviews: int = Field(..., description="Number of reviews")
    total_sessions: int = Field(..., description="Number of completed sessions")
    verification_status: VerificationStatus = Field(
        ..., description="Verification status"
    )
    latitude: float | None = Field(None, description="Latitude (if location set)")
    longitude: float | None = Field(None, description="Longitude (if location set)")
    stripe_onboarding_complete: bool = Field(
        ..., description="Whether Stripe onboarding is finished"
    )
    created_at: datetime = Field(..., description="Profile creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    # Dance styles associated with this host
    dance_styles: list[HostDanceStyleResponse] = Field(
        default_factory=list, description="Host's dance styles with skill levels"
    )


class HostProfileWithUserResponse(HostProfileResponse):
    """Host profile response with user details."""

    first_name: str = Field(..., description="Host's first name")
    last_name: str = Field(..., description="Host's last name")


class HostProfileSummaryResponse(BaseModel):
    """Condensed host profile for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Host profile UUID")
    user_id: str = Field(..., description="Associated user UUID")
    first_name: str = Field(..., description="Host's first name")
    last_name: str = Field(..., description="Host's last name")
    headline: str | None = Field(None, description="Short tagline")
    hourly_rate_cents: int = Field(..., description="Hourly rate in cents")
    rating_average: float | None = Field(None, description="Average rating (1.00-5.00)")
    total_reviews: int = Field(..., description="Number of reviews")
    verification_status: VerificationStatus = Field(
        ..., description="Verification status"
    )
    distance_km: float | None = Field(
        None, description="Distance from search location (km)"
    )


# --- Search Request Schemas ---


class HostSearchRequest(BaseModel):
    """Schema for host search with filters and pagination.

    Used for GET /api/v1/hosts endpoint query parameters.
    """

    # Location-based search (required for geospatial queries)
    latitude: float | None = Field(
        default=None, ge=-90.0, le=90.0, description="Search center latitude"
    )
    longitude: float | None = Field(
        default=None, ge=-180.0, le=180.0, description="Search center longitude"
    )
    radius_km: float = Field(
        default=50.0, ge=1.0, le=500.0, description="Search radius in kilometers"
    )

    # Filters
    style_ids: list[str] | None = Field(
        default=None, description="Filter by dance style UUIDs"
    )
    min_rating: float | None = Field(
        default=None, ge=1.0, le=5.0, description="Minimum rating filter"
    )
    max_price_cents: int | None = Field(
        default=None, ge=100, description="Maximum hourly rate in cents"
    )
    verified_only: bool = Field(default=False, description="Only show verified hosts")

    # Sorting
    sort_by: str = Field(
        default="distance",
        description="Sort field: 'distance', 'rating', 'price', 'reviews'",
    )
    sort_order: str = Field(default="asc", description="Sort order: 'asc' or 'desc'")

    # Pagination
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(
        default=20, ge=1, le=100, description="Results per page (1-100)"
    )

    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(cls, v: str) -> str:
        """Validate sort_by field."""
        allowed = {"distance", "rating", "price", "reviews"}
        if v not in allowed:
            msg = f"sort_by must be one of: {', '.join(sorted(allowed))}"
            raise ValueError(msg)
        return v

    @field_validator("sort_order")
    @classmethod
    def validate_sort_order(cls, v: str) -> str:
        """Validate sort_order field."""
        if v not in {"asc", "desc"}:
            msg = "sort_order must be 'asc' or 'desc'"
            raise ValueError(msg)
        return v


class HostSearchResponse(BaseModel):
    """Paginated response for host search results (offset-based)."""

    items: list[HostProfileSummaryResponse] = Field(
        ..., description="List of host profiles"
    )
    total: int = Field(..., description="Total number of matching hosts")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Results per page")
    total_pages: int = Field(..., description="Total number of pages")


class HostSearchCursorResponse(BaseModel):
    """Cursor-based paginated response for host search results.

    Supports infinite scroll with cursor-based pagination for better
    performance with large datasets and real-time updates.
    """

    items: list[HostProfileSummaryResponse] = Field(
        ..., description="List of host profiles"
    )
    next_cursor: str | None = Field(
        None, description="Cursor for next page (host profile ID), null if no more"
    )
    has_more: bool = Field(
        ..., description="Whether there are more results after this page"
    )
    total: int = Field(..., description="Total number of matching hosts")
