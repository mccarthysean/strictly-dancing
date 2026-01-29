"""Unit tests for Review model."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import CheckConstraint

from app.models.review import Review


class TestReviewModelInstantiation:
    """Tests for Review model instantiation."""

    def test_review_model_instantiation(self) -> None:
        """Test that Review can be instantiated."""
        review = Review(
            booking_id=str(uuid4()),
            reviewer_id=str(uuid4()),
            reviewee_id=str(uuid4()),
            rating=5,
            comment="Great dance session!",
        )
        assert review is not None

    def test_review_model_has_id_field(self) -> None:
        """Test that Review has id field."""
        review = Review()
        assert hasattr(review, "id")

    def test_review_model_has_booking_id_field(self) -> None:
        """Test that Review has booking_id field."""
        booking_id = str(uuid4())
        review = Review(booking_id=booking_id)
        assert review.booking_id == booking_id

    def test_review_model_has_reviewer_id_field(self) -> None:
        """Test that Review has reviewer_id field."""
        reviewer_id = str(uuid4())
        review = Review(reviewer_id=reviewer_id)
        assert review.reviewer_id == reviewer_id

    def test_review_model_has_reviewee_id_field(self) -> None:
        """Test that Review has reviewee_id field."""
        reviewee_id = str(uuid4())
        review = Review(reviewee_id=reviewee_id)
        assert review.reviewee_id == reviewee_id

    def test_review_model_has_rating_field(self) -> None:
        """Test that Review has rating field."""
        review = Review(rating=4)
        assert review.rating == 4

    def test_review_model_has_comment_field(self) -> None:
        """Test that Review has comment field."""
        review = Review(comment="Excellent experience!")
        assert review.comment == "Excellent experience!"

    def test_review_model_has_host_response_field(self) -> None:
        """Test that Review has host_response field."""
        review = Review(host_response="Thank you for the kind words!")
        assert review.host_response == "Thank you for the kind words!"

    def test_review_model_has_host_responded_at_field(self) -> None:
        """Test that Review has host_responded_at field."""
        responded_at = datetime.now(UTC)
        review = Review(host_responded_at=responded_at)
        assert review.host_responded_at == responded_at

    def test_review_model_has_created_at_field(self) -> None:
        """Test that Review has created_at field."""
        review = Review()
        assert hasattr(review, "created_at")

    def test_review_model_has_updated_at_field(self) -> None:
        """Test that Review has updated_at field."""
        review = Review()
        assert hasattr(review, "updated_at")


class TestReviewModelTableName:
    """Tests for Review model table name."""

    def test_review_tablename(self) -> None:
        """Test that Review has correct tablename."""
        assert Review.__tablename__ == "reviews"


class TestReviewModelRequiredFields:
    """Tests for Review model required fields."""

    def test_booking_id_is_required(self) -> None:
        """Test that booking_id is a required field."""
        column = Review.__table__.c.booking_id
        assert column.nullable is False

    def test_reviewer_id_is_required(self) -> None:
        """Test that reviewer_id is a required field."""
        column = Review.__table__.c.reviewer_id
        assert column.nullable is False

    def test_reviewee_id_is_required(self) -> None:
        """Test that reviewee_id is a required field."""
        column = Review.__table__.c.reviewee_id
        assert column.nullable is False

    def test_rating_is_required(self) -> None:
        """Test that rating is a required field."""
        column = Review.__table__.c.rating
        assert column.nullable is False


class TestReviewModelOptionalFields:
    """Tests for Review model optional fields."""

    def test_comment_is_optional(self) -> None:
        """Test that comment is an optional field."""
        column = Review.__table__.c.comment
        assert column.nullable is True

    def test_host_response_is_optional(self) -> None:
        """Test that host_response is an optional field."""
        column = Review.__table__.c.host_response
        assert column.nullable is True

    def test_host_responded_at_is_optional(self) -> None:
        """Test that host_responded_at is an optional field."""
        column = Review.__table__.c.host_responded_at
        assert column.nullable is True


class TestReviewModelConstraints:
    """Tests for Review model constraints."""

    def test_booking_id_is_unique(self) -> None:
        """Test that booking_id has unique constraint (one review per booking)."""
        column = Review.__table__.c.booking_id
        assert column.unique is True

    def test_rating_has_check_constraint(self) -> None:
        """Test that rating has check constraint for range 1-5."""
        constraints = [
            c for c in Review.__table__.constraints if isinstance(c, CheckConstraint)
        ]
        rating_constraint = None
        for constraint in constraints:
            if constraint.name == "rating_range_1_to_5":
                rating_constraint = constraint
                break
        assert rating_constraint is not None


class TestReviewModelForeignKeys:
    """Tests for Review model foreign keys."""

    def test_booking_id_is_foreign_key(self) -> None:
        """Test that booking_id is a foreign key to bookings."""
        column = Review.__table__.c.booking_id
        fk = list(column.foreign_keys)[0]
        assert fk.column.table.name == "bookings"

    def test_reviewer_id_is_foreign_key(self) -> None:
        """Test that reviewer_id is a foreign key to users."""
        column = Review.__table__.c.reviewer_id
        fk = list(column.foreign_keys)[0]
        assert fk.column.table.name == "users"

    def test_reviewee_id_is_foreign_key(self) -> None:
        """Test that reviewee_id is a foreign key to users."""
        column = Review.__table__.c.reviewee_id
        fk = list(column.foreign_keys)[0]
        assert fk.column.table.name == "users"


class TestReviewModelIndexes:
    """Tests for Review model indexes."""

    def test_booking_id_is_indexed(self) -> None:
        """Test that booking_id has an index."""
        column = Review.__table__.c.booking_id
        assert column.index is True

    def test_reviewer_id_is_indexed(self) -> None:
        """Test that reviewer_id has an index."""
        column = Review.__table__.c.reviewer_id
        assert column.index is True

    def test_reviewee_id_is_indexed(self) -> None:
        """Test that reviewee_id has an index."""
        column = Review.__table__.c.reviewee_id
        assert column.index is True


class TestReviewModelRelationships:
    """Tests for Review model relationships."""

    def test_review_has_booking_relationship(self) -> None:
        """Test that Review has a relationship to Booking."""
        assert hasattr(Review, "booking")

    def test_review_has_reviewer_relationship(self) -> None:
        """Test that Review has a relationship to User (reviewer)."""
        assert hasattr(Review, "reviewer")

    def test_review_has_reviewee_relationship(self) -> None:
        """Test that Review has a relationship to User (reviewee)."""
        assert hasattr(Review, "reviewee")


class TestReviewModelRepr:
    """Tests for Review model __repr__ method."""

    def test_review_repr(self) -> None:
        """Test Review __repr__ output."""
        booking_id = str(uuid4())
        review = Review(
            id=str(uuid4()),
            booking_id=booking_id,
            rating=5,
        )
        repr_str = repr(review)
        assert "Review" in repr_str
        assert booking_id in repr_str
        assert "5" in repr_str


class TestReviewModelRatingValues:
    """Tests for Review model rating field values."""

    @pytest.mark.parametrize("rating", [1, 2, 3, 4, 5])
    def test_valid_rating_values(self, rating: int) -> None:
        """Test that valid rating values can be set."""
        review = Review(rating=rating)
        assert review.rating == rating

    def test_rating_minimum_is_1(self) -> None:
        """Test that minimum rating value is 1."""
        # The check constraint name indicates 1-5 range
        constraints = [
            c for c in Review.__table__.constraints if isinstance(c, CheckConstraint)
        ]
        constraint = [c for c in constraints if c.name == "rating_range_1_to_5"][0]
        assert "rating >= 1" in str(constraint.sqltext)

    def test_rating_maximum_is_5(self) -> None:
        """Test that maximum rating value is 5."""
        constraints = [
            c for c in Review.__table__.constraints if isinstance(c, CheckConstraint)
        ]
        constraint = [c for c in constraints if c.name == "rating_range_1_to_5"][0]
        assert "rating <= 5" in str(constraint.sqltext)


class TestReviewModelHostResponse:
    """Tests for Review model host_response field."""

    def test_host_response_can_be_set(self) -> None:
        """Test that host_response can be set."""
        review = Review()
        review.host_response = "Thank you for your review!"
        assert review.host_response == "Thank you for your review!"

    def test_host_response_can_be_none(self) -> None:
        """Test that host_response can be None."""
        review = Review()
        assert review.host_response is None

    def test_host_responded_at_tracks_response_time(self) -> None:
        """Test that host_responded_at can track when response was added."""
        review = Review()
        now = datetime.now(UTC)
        review.host_response = "Thanks!"
        review.host_responded_at = now
        assert review.host_responded_at == now
