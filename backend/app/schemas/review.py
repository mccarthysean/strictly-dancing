"""Pydantic schemas for review requests and responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReviewUserSummary(BaseModel):
    """Condensed user info for review responses."""

    id: str = Field(..., description="User UUID")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")

    model_config = ConfigDict(from_attributes=True)


class CreateReviewRequest(BaseModel):
    """Request schema for creating a review."""

    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
    comment: str | None = Field(
        None, min_length=1, max_length=2000, description="Optional review comment"
    )


class ReviewResponse(BaseModel):
    """Response schema for a review."""

    id: str = Field(..., description="Review UUID")
    booking_id: str = Field(..., description="Booking UUID")
    reviewer_id: str = Field(..., description="Reviewer user UUID")
    reviewee_id: str = Field(..., description="Reviewee user UUID")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
    comment: str | None = Field(None, description="Review comment")
    host_response: str | None = Field(None, description="Host's response to the review")
    host_responded_at: datetime | None = Field(
        None, description="When the host responded"
    )
    created_at: datetime = Field(..., description="When the review was created")
    updated_at: datetime = Field(..., description="When the review was last updated")

    model_config = ConfigDict(from_attributes=True)


class ReviewWithUserResponse(ReviewResponse):
    """Review response with reviewer details."""

    reviewer: ReviewUserSummary | None = Field(None, description="Reviewer details")
    reviewee: ReviewUserSummary | None = Field(None, description="Reviewee details")


class ReviewListResponse(BaseModel):
    """Response schema for paginated review list."""

    items: list[ReviewWithUserResponse] = Field(
        default_factory=list, description="List of reviews"
    )
    next_cursor: str | None = Field(
        None, description="Cursor for next page (review ID)"
    )
    has_more: bool = Field(..., description="Whether there are more reviews")
    total: int = Field(..., description="Total number of reviews")


class AddResponseRequest(BaseModel):
    """Request schema for adding a host response to a review."""

    response: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Host's response to the review",
    )
