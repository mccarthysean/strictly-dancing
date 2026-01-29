"""Unit tests for ReviewRepository."""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.review import Review
from app.repositories.review import ReviewRepository


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create a mock async session."""
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.execute = AsyncMock()
    session.delete = AsyncMock()
    return session


@pytest.fixture
def repository(mock_session: AsyncMock) -> ReviewRepository:
    """Create a ReviewRepository with a mock session."""
    return ReviewRepository(mock_session)


class TestReviewRepositoryInitialization:
    """Tests for ReviewRepository initialization."""

    def test_repository_accepts_session(self, mock_session: AsyncMock) -> None:
        """Test that repository accepts an async session."""
        repo = ReviewRepository(mock_session)
        assert repo._session is mock_session


class TestCreateReview:
    """Tests for create() method."""

    @pytest.mark.asyncio
    async def test_create_review_success(
        self, repository: ReviewRepository, mock_session: AsyncMock
    ) -> None:
        """Test creating a review successfully."""
        booking_id = uuid4()
        reviewer_id = uuid4()
        reviewee_id = uuid4()

        review = await repository.create(
            booking_id=booking_id,
            reviewer_id=reviewer_id,
            reviewee_id=reviewee_id,
            rating=5,
            comment="Great session!",
        )

        assert review is not None
        assert review.rating == 5
        assert review.comment == "Great session!"
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_review_without_comment(
        self, repository: ReviewRepository, mock_session: AsyncMock
    ) -> None:
        """Test creating a review without a comment."""
        review = await repository.create(
            booking_id=uuid4(),
            reviewer_id=uuid4(),
            reviewee_id=uuid4(),
            rating=4,
        )

        assert review.comment is None

    @pytest.mark.asyncio
    async def test_create_review_rating_too_low(
        self, repository: ReviewRepository
    ) -> None:
        """Test creating a review with rating below 1 raises error."""
        with pytest.raises(ValueError, match="Rating must be between 1 and 5"):
            await repository.create(
                booking_id=uuid4(),
                reviewer_id=uuid4(),
                reviewee_id=uuid4(),
                rating=0,
            )

    @pytest.mark.asyncio
    async def test_create_review_rating_too_high(
        self, repository: ReviewRepository
    ) -> None:
        """Test creating a review with rating above 5 raises error."""
        with pytest.raises(ValueError, match="Rating must be between 1 and 5"):
            await repository.create(
                booking_id=uuid4(),
                reviewer_id=uuid4(),
                reviewee_id=uuid4(),
                rating=6,
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("rating", [1, 2, 3, 4, 5])
    async def test_create_review_valid_ratings(
        self, repository: ReviewRepository, mock_session: AsyncMock, rating: int
    ) -> None:
        """Test creating reviews with all valid ratings."""
        review = await repository.create(
            booking_id=uuid4(),
            reviewer_id=uuid4(),
            reviewee_id=uuid4(),
            rating=rating,
        )
        assert review.rating == rating


class TestGetById:
    """Tests for get_by_id() method."""

    @pytest.mark.asyncio
    async def test_get_by_id_found(
        self, repository: ReviewRepository, mock_session: AsyncMock
    ) -> None:
        """Test getting a review by ID when it exists."""
        review_id = uuid4()
        mock_review = Review(id=str(review_id), rating=5)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_review
        mock_session.execute.return_value = mock_result

        result = await repository.get_by_id(review_id)

        assert result is mock_review

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(
        self, repository: ReviewRepository, mock_session: AsyncMock
    ) -> None:
        """Test getting a review by ID when it doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repository.get_by_id(uuid4())

        assert result is None


class TestGetForBooking:
    """Tests for get_for_booking() method."""

    @pytest.mark.asyncio
    async def test_get_for_booking_found(
        self, repository: ReviewRepository, mock_session: AsyncMock
    ) -> None:
        """Test getting a review for a booking when it exists."""
        booking_id = uuid4()
        mock_review = Review(booking_id=str(booking_id), rating=4)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_review
        mock_session.execute.return_value = mock_result

        result = await repository.get_for_booking(booking_id)

        assert result is mock_review

    @pytest.mark.asyncio
    async def test_get_for_booking_not_found(
        self, repository: ReviewRepository, mock_session: AsyncMock
    ) -> None:
        """Test getting a review for a booking when none exists."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repository.get_for_booking(uuid4())

        assert result is None


class TestGetForUser:
    """Tests for get_for_user() method."""

    @pytest.mark.asyncio
    async def test_get_for_user_as_reviewee(
        self, repository: ReviewRepository, mock_session: AsyncMock
    ) -> None:
        """Test getting reviews where user is the reviewee."""
        user_id = uuid4()
        mock_reviews = [
            Review(id=str(uuid4()), reviewee_id=str(user_id), rating=5),
            Review(id=str(uuid4()), reviewee_id=str(user_id), rating=4),
        ]

        mock_scalars = MagicMock()
        mock_scalars.unique.return_value.all.return_value = mock_reviews
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_for_user(user_id, as_reviewee=True)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_for_user_as_reviewer(
        self, repository: ReviewRepository, mock_session: AsyncMock
    ) -> None:
        """Test getting reviews where user is the reviewer."""
        mock_scalars = MagicMock()
        mock_scalars.unique.return_value.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_for_user(
            uuid4(), as_reviewer=True, as_reviewee=False
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_get_for_user_no_conditions(
        self, repository: ReviewRepository
    ) -> None:
        """Test getting reviews with neither reviewer nor reviewee returns empty."""
        result = await repository.get_for_user(
            uuid4(), as_reviewer=False, as_reviewee=False
        )

        assert result == []


class TestGetForHostProfile:
    """Tests for get_for_host_profile() method."""

    @pytest.mark.asyncio
    async def test_get_for_host_profile(
        self, repository: ReviewRepository, mock_session: AsyncMock
    ) -> None:
        """Test getting reviews for a host profile."""
        mock_scalars = MagicMock()
        mock_scalars.unique.return_value.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_for_host_profile(uuid4())

        assert result == []


class TestAddResponse:
    """Tests for add_response() method."""

    @pytest.mark.asyncio
    async def test_add_response_success(
        self, repository: ReviewRepository, mock_session: AsyncMock
    ) -> None:
        """Test adding a host response to a review."""
        review_id = uuid4()
        mock_review = Review(id=str(review_id), rating=5)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_review
        mock_session.execute.return_value = mock_result

        result = await repository.add_response(review_id, "Thank you!")

        assert result is not None
        assert result.host_response == "Thank you!"
        assert result.host_responded_at is not None
        mock_session.flush.assert_called()

    @pytest.mark.asyncio
    async def test_add_response_review_not_found(
        self, repository: ReviewRepository, mock_session: AsyncMock
    ) -> None:
        """Test adding a response when review doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repository.add_response(uuid4(), "Thank you!")

        assert result is None


class TestRemoveResponse:
    """Tests for remove_response() method."""

    @pytest.mark.asyncio
    async def test_remove_response_success(
        self, repository: ReviewRepository, mock_session: AsyncMock
    ) -> None:
        """Test removing a host response from a review."""
        review_id = uuid4()
        mock_review = Review(
            id=str(review_id),
            rating=5,
            host_response="Old response",
            host_responded_at=datetime.now(UTC),
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_review
        mock_session.execute.return_value = mock_result

        result = await repository.remove_response(review_id)

        assert result is not None
        assert result.host_response is None
        assert result.host_responded_at is None

    @pytest.mark.asyncio
    async def test_remove_response_not_found(
        self, repository: ReviewRepository, mock_session: AsyncMock
    ) -> None:
        """Test removing a response when review doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repository.remove_response(uuid4())

        assert result is None


class TestCalculateRatingAverage:
    """Tests for calculate_rating_average() method."""

    @pytest.mark.asyncio
    async def test_calculate_rating_average_with_reviews(
        self, repository: ReviewRepository, mock_session: AsyncMock
    ) -> None:
        """Test calculating average rating when reviews exist."""
        mock_row = MagicMock()
        mock_row.avg = Decimal("4.50")
        mock_row.count = 10

        mock_result = MagicMock()
        mock_result.one.return_value = mock_row
        mock_session.execute.return_value = mock_result

        avg, count = await repository.calculate_rating_average(uuid4())

        assert avg == Decimal("4.50")
        assert count == 10

    @pytest.mark.asyncio
    async def test_calculate_rating_average_no_reviews(
        self, repository: ReviewRepository, mock_session: AsyncMock
    ) -> None:
        """Test calculating average rating when no reviews exist."""
        mock_row = MagicMock()
        mock_row.avg = None
        mock_row.count = 0

        mock_result = MagicMock()
        mock_result.one.return_value = mock_row
        mock_session.execute.return_value = mock_result

        avg, count = await repository.calculate_rating_average(uuid4())

        assert avg is None
        assert count == 0


class TestUpdateHostProfileRating:
    """Tests for update_host_profile_rating() method."""

    @pytest.mark.asyncio
    async def test_update_host_profile_rating(
        self, repository: ReviewRepository, mock_session: AsyncMock
    ) -> None:
        """Test manually updating host profile rating stats."""
        host_profile_id = uuid4()

        # Mock calculate_rating_average
        mock_row = MagicMock()
        mock_row.avg = Decimal("4.75")
        mock_row.count = 20

        mock_result = MagicMock()
        mock_result.one.return_value = mock_row
        mock_session.execute.return_value = mock_result

        await repository.update_host_profile_rating(host_profile_id)

        # Should have been called for avg calc and update
        assert mock_session.execute.call_count >= 1
        mock_session.flush.assert_called()


class TestCountForHostProfile:
    """Tests for count_for_host_profile() method."""

    @pytest.mark.asyncio
    async def test_count_for_host_profile(
        self, repository: ReviewRepository, mock_session: AsyncMock
    ) -> None:
        """Test counting reviews for a host profile."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 15
        mock_session.execute.return_value = mock_result

        count = await repository.count_for_host_profile(uuid4())

        assert count == 15

    @pytest.mark.asyncio
    async def test_count_for_host_profile_none(
        self, repository: ReviewRepository, mock_session: AsyncMock
    ) -> None:
        """Test counting reviews when result is None."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_session.execute.return_value = mock_result

        count = await repository.count_for_host_profile(uuid4())

        assert count == 0


class TestExistsForBooking:
    """Tests for exists_for_booking() method."""

    @pytest.mark.asyncio
    async def test_exists_for_booking_true(
        self, repository: ReviewRepository, mock_session: AsyncMock
    ) -> None:
        """Test checking if review exists for booking when it does."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1
        mock_session.execute.return_value = mock_result

        exists = await repository.exists_for_booking(uuid4())

        assert exists is True

    @pytest.mark.asyncio
    async def test_exists_for_booking_false(
        self, repository: ReviewRepository, mock_session: AsyncMock
    ) -> None:
        """Test checking if review exists for booking when it doesn't."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 0
        mock_session.execute.return_value = mock_result

        exists = await repository.exists_for_booking(uuid4())

        assert exists is False


class TestDelete:
    """Tests for delete() method."""

    @pytest.mark.asyncio
    async def test_delete_success(
        self, repository: ReviewRepository, mock_session: AsyncMock
    ) -> None:
        """Test deleting a review successfully."""
        review_id = uuid4()
        mock_review = Review(id=str(review_id), rating=5)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_review
        mock_session.execute.return_value = mock_result

        result = await repository.delete(review_id)

        assert result is True
        mock_session.delete.assert_called_once_with(mock_review)
        mock_session.flush.assert_called()

    @pytest.mark.asyncio
    async def test_delete_not_found(
        self, repository: ReviewRepository, mock_session: AsyncMock
    ) -> None:
        """Test deleting a review that doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repository.delete(uuid4())

        assert result is False
        mock_session.delete.assert_not_called()


class TestRepositoryHasRequiredMethods:
    """Tests to verify repository has all required methods."""

    def test_has_create_method(self, repository: ReviewRepository) -> None:
        """Test that repository has create method."""
        assert hasattr(repository, "create")
        assert callable(repository.create)

    def test_has_get_for_booking_method(self, repository: ReviewRepository) -> None:
        """Test that repository has get_for_booking method."""
        assert hasattr(repository, "get_for_booking")
        assert callable(repository.get_for_booking)

    def test_has_get_for_user_method(self, repository: ReviewRepository) -> None:
        """Test that repository has get_for_user method."""
        assert hasattr(repository, "get_for_user")
        assert callable(repository.get_for_user)

    def test_has_add_response_method(self, repository: ReviewRepository) -> None:
        """Test that repository has add_response method."""
        assert hasattr(repository, "add_response")
        assert callable(repository.add_response)

    def test_has_calculate_rating_average_method(
        self, repository: ReviewRepository
    ) -> None:
        """Test that repository has calculate_rating_average method."""
        assert hasattr(repository, "calculate_rating_average")
        assert callable(repository.calculate_rating_average)
