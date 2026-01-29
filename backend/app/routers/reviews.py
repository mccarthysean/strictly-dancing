"""Reviews router for review management operations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUser
from app.repositories.review import ReviewRepository
from app.schemas.review import (
    AddResponseRequest,
    ReviewUserSummary,
    ReviewWithUserResponse,
)

router = APIRouter(prefix="/api/v1/reviews", tags=["reviews"])

# Type alias for database session dependency
DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.post(
    "/{review_id}/response",
    response_model=ReviewWithUserResponse,
    status_code=status.HTTP_200_OK,
    summary="Add a host response to a review",
    description="Host adds or updates their response to a review.",
)
async def add_review_response(
    review_id: UUID,
    request: AddResponseRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> ReviewWithUserResponse:
    """Add or update a host response to a review.

    Only the reviewee (host) can respond to their review.

    Args:
        review_id: The review's unique identifier.
        request: The response text.
        db: The database session (injected).
        current_user: The authenticated user (injected).

    Returns:
        ReviewWithUserResponse with the updated review.

    Raises:
        HTTPException: 403 if user is not the reviewee (host).
        HTTPException: 404 if review not found.
    """
    review_repo = ReviewRepository(db)

    # Get the review
    review = await review_repo.get_by_id(review_id, load_relationships=True)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )

    # Verify that the current user is the reviewee (host)
    if review.reviewee_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the host can respond to this review",
        )

    # Add the response
    review = await review_repo.add_response(review_id, request.response)

    await db.commit()

    # Reload with relationships
    review = await review_repo.get_by_id(review_id, load_relationships=True)

    return ReviewWithUserResponse(
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


@router.delete(
    "/{review_id}/response",
    response_model=ReviewWithUserResponse,
    status_code=status.HTTP_200_OK,
    summary="Remove a host response from a review",
    description="Host removes their response from a review.",
)
async def delete_review_response(
    review_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> ReviewWithUserResponse:
    """Remove a host response from a review.

    Only the reviewee (host) can remove their response.

    Args:
        review_id: The review's unique identifier.
        db: The database session (injected).
        current_user: The authenticated user (injected).

    Returns:
        ReviewWithUserResponse with the updated review.

    Raises:
        HTTPException: 403 if user is not the reviewee (host).
        HTTPException: 404 if review not found.
    """
    review_repo = ReviewRepository(db)

    # Get the review
    review = await review_repo.get_by_id(review_id, load_relationships=True)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )

    # Verify that the current user is the reviewee (host)
    if review.reviewee_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the host can remove the response to this review",
        )

    # Remove the response
    review = await review_repo.remove_response(review_id)

    await db.commit()

    # Reload with relationships
    review = await review_repo.get_by_id(review_id, load_relationships=True)

    return ReviewWithUserResponse(
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


@router.get(
    "/{review_id}",
    response_model=ReviewWithUserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a review by ID",
    description="Get a specific review.",
)
async def get_review(
    review_id: UUID,
    db: DbSession,
) -> ReviewWithUserResponse:
    """Get a review by its ID.

    Reviews are public and can be viewed by anyone.

    Args:
        review_id: The review's unique identifier.
        db: The database session (injected).

    Returns:
        ReviewWithUserResponse with the review.

    Raises:
        HTTPException: 404 if review not found.
    """
    review_repo = ReviewRepository(db)

    review = await review_repo.get_by_id(review_id, load_relationships=True)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )

    return ReviewWithUserResponse(
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
