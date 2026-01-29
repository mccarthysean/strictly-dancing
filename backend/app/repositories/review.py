"""Review repository for review data access operations."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.booking import Booking
from app.models.host_profile import HostProfile
from app.models.review import Review


class ReviewRepository:
    """Repository for Review CRUD operations.

    Implements the repository pattern for review data access,
    providing an abstraction layer over SQLAlchemy operations.

    All methods use async patterns for non-blocking database access.

    Attributes:
        session: The async database session for executing queries.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session.

        Args:
            session: An async SQLAlchemy session.
        """
        self._session = session

    async def create(
        self,
        booking_id: UUID,
        reviewer_id: UUID,
        reviewee_id: UUID,
        rating: int,
        comment: str | None = None,
    ) -> Review:
        """Create a new review.

        Args:
            booking_id: The booking being reviewed.
            reviewer_id: The user leaving the review.
            reviewee_id: The user being reviewed (typically the host).
            rating: Rating from 1 to 5.
            comment: Optional review text.

        Returns:
            The newly created Review.

        Raises:
            ValueError: If rating is not between 1 and 5.
        """
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")

        review = Review(
            booking_id=str(booking_id),
            reviewer_id=str(reviewer_id),
            reviewee_id=str(reviewee_id),
            rating=rating,
            comment=comment,
        )
        self._session.add(review)
        await self._session.flush()
        return review

    async def get_by_id(
        self,
        review_id: UUID,
        load_relationships: bool = False,
    ) -> Review | None:
        """Get a review by its ID.

        Args:
            review_id: The review's UUID.
            load_relationships: Whether to eagerly load related entities.

        Returns:
            The Review if found, None otherwise.
        """
        stmt = select(Review).where(Review.id == str(review_id))

        if load_relationships:
            stmt = stmt.options(
                joinedload(Review.booking),
                joinedload(Review.reviewer),
                joinedload(Review.reviewee),
            )

        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_for_booking(
        self,
        booking_id: UUID,
        load_relationships: bool = False,
    ) -> Review | None:
        """Get the review for a specific booking.

        Args:
            booking_id: The booking's UUID.
            load_relationships: Whether to eagerly load related entities.

        Returns:
            The Review if found, None otherwise.
        """
        stmt = select(Review).where(Review.booking_id == str(booking_id))

        if load_relationships:
            stmt = stmt.options(
                joinedload(Review.booking),
                joinedload(Review.reviewer),
                joinedload(Review.reviewee),
            )

        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_for_user(
        self,
        user_id: UUID,
        as_reviewer: bool = False,
        as_reviewee: bool = True,
        limit: int = 20,
        cursor: UUID | None = None,
    ) -> list[Review]:
        """Get reviews for a user (as reviewer or reviewee).

        Args:
            user_id: The user's UUID.
            as_reviewer: Include reviews written by this user.
            as_reviewee: Include reviews about this user.
            limit: Maximum number of reviews to return.
            cursor: Review ID to start after (for pagination).

        Returns:
            List of Review objects ordered by created_at descending.
        """
        conditions = []
        user_id_str = str(user_id)

        if as_reviewer:
            conditions.append(Review.reviewer_id == user_id_str)
        if as_reviewee:
            conditions.append(Review.reviewee_id == user_id_str)

        if not conditions:
            return []

        from sqlalchemy import or_

        stmt = select(Review).where(or_(*conditions))

        if cursor:
            # Get the review at cursor to get its created_at
            cursor_review = await self.get_by_id(cursor)
            if cursor_review:
                stmt = stmt.where(Review.created_at < cursor_review.created_at)

        stmt = stmt.order_by(Review.created_at.desc()).limit(limit)
        stmt = stmt.options(
            joinedload(Review.reviewer),
            joinedload(Review.reviewee),
        )

        result = await self._session.execute(stmt)
        return list(result.scalars().unique().all())

    async def get_for_host_profile(
        self,
        host_profile_id: UUID,
        limit: int = 20,
        cursor: UUID | None = None,
    ) -> list[Review]:
        """Get reviews for a host profile.

        Args:
            host_profile_id: The host profile's UUID.
            limit: Maximum number of reviews to return.
            cursor: Review ID to start after (for pagination).

        Returns:
            List of Review objects ordered by created_at descending.
        """
        # Reviews are linked via booking -> host_profile_id
        stmt = (
            select(Review)
            .join(Booking, Review.booking_id == Booking.id)
            .where(Booking.host_profile_id == str(host_profile_id))
        )

        if cursor:
            cursor_review = await self.get_by_id(cursor)
            if cursor_review:
                stmt = stmt.where(Review.created_at < cursor_review.created_at)

        stmt = stmt.order_by(Review.created_at.desc()).limit(limit)
        stmt = stmt.options(
            joinedload(Review.reviewer),
            joinedload(Review.reviewee),
        )

        result = await self._session.execute(stmt)
        return list(result.scalars().unique().all())

    async def add_response(
        self,
        review_id: UUID,
        response: str,
    ) -> Review | None:
        """Add or update a host response to a review.

        Args:
            review_id: The review's UUID.
            response: The host's response text.

        Returns:
            The updated Review if found, None otherwise.
        """
        review = await self.get_by_id(review_id)
        if not review:
            return None

        review.host_response = response
        review.host_responded_at = datetime.now(UTC)
        await self._session.flush()
        return review

    async def remove_response(
        self,
        review_id: UUID,
    ) -> Review | None:
        """Remove a host response from a review.

        Args:
            review_id: The review's UUID.

        Returns:
            The updated Review if found, None otherwise.
        """
        review = await self.get_by_id(review_id)
        if not review:
            return None

        review.host_response = None
        review.host_responded_at = None
        await self._session.flush()
        return review

    async def calculate_rating_average(
        self,
        host_profile_id: UUID,
    ) -> tuple[Decimal | None, int]:
        """Calculate the average rating and count for a host profile.

        Note: This is typically handled by the database trigger, but
        this method is provided for manual calculation if needed.

        Args:
            host_profile_id: The host profile's UUID.

        Returns:
            A tuple of (average_rating, total_reviews).
            average_rating is None if there are no reviews.
        """
        stmt = (
            select(
                func.round(func.avg(Review.rating).cast(Decimal), 2).label("avg"),
                func.count(Review.id).label("count"),
            )
            .select_from(Review)
            .join(Booking, Review.booking_id == Booking.id)
            .where(Booking.host_profile_id == str(host_profile_id))
        )

        result = await self._session.execute(stmt)
        row = result.one()

        return row.avg, row.count

    async def update_host_profile_rating(
        self,
        host_profile_id: UUID,
    ) -> None:
        """Manually update a host profile's rating stats.

        Note: This is typically handled by the database trigger on insert/update/delete,
        but this method allows manual recalculation if needed.

        Args:
            host_profile_id: The host profile's UUID.
        """
        avg_rating, total_reviews = await self.calculate_rating_average(host_profile_id)

        stmt = (
            update(HostProfile)
            .where(HostProfile.id == str(host_profile_id))
            .values(
                rating_average=avg_rating,
                total_reviews=total_reviews,
            )
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def count_for_host_profile(
        self,
        host_profile_id: UUID,
    ) -> int:
        """Count reviews for a host profile.

        Args:
            host_profile_id: The host profile's UUID.

        Returns:
            The total number of reviews.
        """
        stmt = (
            select(func.count(Review.id))
            .select_from(Review)
            .join(Booking, Review.booking_id == Booking.id)
            .where(Booking.host_profile_id == str(host_profile_id))
        )

        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def exists_for_booking(
        self,
        booking_id: UUID,
    ) -> bool:
        """Check if a review exists for a booking.

        Args:
            booking_id: The booking's UUID.

        Returns:
            True if a review exists, False otherwise.
        """
        stmt = select(func.count(Review.id)).where(Review.booking_id == str(booking_id))
        result = await self._session.execute(stmt)
        return (result.scalar() or 0) > 0

    async def delete(
        self,
        review_id: UUID,
    ) -> bool:
        """Delete a review.

        Args:
            review_id: The review's UUID.

        Returns:
            True if the review was deleted, False if not found.
        """
        review = await self.get_by_id(review_id)
        if not review:
            return False

        await self._session.delete(review)
        await self._session.flush()
        return True
