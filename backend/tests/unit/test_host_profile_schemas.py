"""Unit tests for host profile Pydantic schemas."""

import pytest
from pydantic import ValidationError

from app.models.dance_style import DanceStyleCategory
from app.models.host_profile import VerificationStatus
from app.schemas.host_profile import (
    CreateHostProfileRequest,
    DanceStyleRequest,
    DanceStyleResponse,
    HostDanceStyleResponse,
    HostProfileResponse,
    HostProfileSummaryResponse,
    HostSearchRequest,
    HostSearchResponse,
    LocationRequest,
    UpdateHostProfileRequest,
)


class TestLocationRequest:
    """Tests for LocationRequest schema."""

    def test_valid_coordinates(self):
        """Test valid latitude and longitude."""
        location = LocationRequest(latitude=40.7128, longitude=-74.0060)
        assert location.latitude == 40.7128
        assert location.longitude == -74.0060

    def test_latitude_at_bounds(self):
        """Test latitude at valid bounds."""
        # Min bound
        location = LocationRequest(latitude=-90.0, longitude=0.0)
        assert location.latitude == -90.0

        # Max bound
        location = LocationRequest(latitude=90.0, longitude=0.0)
        assert location.latitude == 90.0

    def test_longitude_at_bounds(self):
        """Test longitude at valid bounds."""
        # Min bound
        location = LocationRequest(latitude=0.0, longitude=-180.0)
        assert location.longitude == -180.0

        # Max bound
        location = LocationRequest(latitude=0.0, longitude=180.0)
        assert location.longitude == 180.0

    def test_latitude_below_minimum_fails(self):
        """Test latitude below -90 fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            LocationRequest(latitude=-90.1, longitude=0.0)
        assert "latitude" in str(exc_info.value)

    def test_latitude_above_maximum_fails(self):
        """Test latitude above 90 fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            LocationRequest(latitude=90.1, longitude=0.0)
        assert "latitude" in str(exc_info.value)

    def test_longitude_below_minimum_fails(self):
        """Test longitude below -180 fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            LocationRequest(latitude=0.0, longitude=-180.1)
        assert "longitude" in str(exc_info.value)

    def test_longitude_above_maximum_fails(self):
        """Test longitude above 180 fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            LocationRequest(latitude=0.0, longitude=180.1)
        assert "longitude" in str(exc_info.value)


class TestDanceStyleRequest:
    """Tests for DanceStyleRequest schema."""

    def test_valid_dance_style_request(self):
        """Test valid dance style request."""
        request = DanceStyleRequest(
            dance_style_id="550e8400-e29b-41d4-a716-446655440000",
            skill_level=3,
        )
        assert request.dance_style_id == "550e8400-e29b-41d4-a716-446655440000"
        assert request.skill_level == 3

    def test_skill_level_at_bounds(self):
        """Test skill level at valid bounds."""
        # Min bound
        request = DanceStyleRequest(dance_style_id="test-id", skill_level=1)
        assert request.skill_level == 1

        # Max bound
        request = DanceStyleRequest(dance_style_id="test-id", skill_level=5)
        assert request.skill_level == 5

    def test_skill_level_below_minimum_fails(self):
        """Test skill level below 1 fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            DanceStyleRequest(dance_style_id="test-id", skill_level=0)
        assert "skill_level" in str(exc_info.value)

    def test_skill_level_above_maximum_fails(self):
        """Test skill level above 5 fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            DanceStyleRequest(dance_style_id="test-id", skill_level=6)
        assert "skill_level" in str(exc_info.value)


class TestCreateHostProfileRequest:
    """Tests for CreateHostProfileRequest schema."""

    def test_defaults(self):
        """Test default values."""
        request = CreateHostProfileRequest()
        assert request.bio is None
        assert request.headline is None
        assert request.hourly_rate_cents == 5000
        assert request.location is None

    def test_with_all_fields(self):
        """Test with all fields provided."""
        request = CreateHostProfileRequest(
            bio="I love dancing!",
            headline="Professional dancer",
            hourly_rate_cents=7500,
            location=LocationRequest(latitude=40.7128, longitude=-74.0060),
        )
        assert request.bio == "I love dancing!"
        assert request.headline == "Professional dancer"
        assert request.hourly_rate_cents == 7500
        assert request.location is not None
        assert request.location.latitude == 40.7128

    def test_hourly_rate_minimum(self):
        """Test hourly rate minimum ($1 = 100 cents)."""
        request = CreateHostProfileRequest(hourly_rate_cents=100)
        assert request.hourly_rate_cents == 100

    def test_hourly_rate_maximum(self):
        """Test hourly rate maximum ($1000 = 100000 cents)."""
        request = CreateHostProfileRequest(hourly_rate_cents=100000)
        assert request.hourly_rate_cents == 100000

    def test_hourly_rate_below_minimum_fails(self):
        """Test hourly rate below $1 fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            CreateHostProfileRequest(hourly_rate_cents=99)
        assert "hourly_rate_cents" in str(exc_info.value)

    def test_hourly_rate_above_maximum_fails(self):
        """Test hourly rate above $1000 fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            CreateHostProfileRequest(hourly_rate_cents=100001)
        assert "hourly_rate_cents" in str(exc_info.value)

    def test_bio_max_length(self):
        """Test bio max length enforcement."""
        long_bio = "x" * 2000
        request = CreateHostProfileRequest(bio=long_bio)
        assert len(request.bio) == 2000

    def test_bio_too_long_fails(self):
        """Test bio exceeding max length fails."""
        with pytest.raises(ValidationError) as exc_info:
            CreateHostProfileRequest(bio="x" * 2001)
        assert "bio" in str(exc_info.value)

    def test_headline_max_length(self):
        """Test headline max length enforcement."""
        headline = "x" * 200
        request = CreateHostProfileRequest(headline=headline)
        assert len(request.headline) == 200

    def test_headline_too_long_fails(self):
        """Test headline exceeding max length fails."""
        with pytest.raises(ValidationError) as exc_info:
            CreateHostProfileRequest(headline="x" * 201)
        assert "headline" in str(exc_info.value)


class TestUpdateHostProfileRequest:
    """Tests for UpdateHostProfileRequest schema."""

    def test_all_fields_optional(self):
        """Test all fields are optional."""
        request = UpdateHostProfileRequest()
        assert request.bio is None
        assert request.headline is None
        assert request.hourly_rate_cents is None
        assert request.location is None

    def test_partial_update(self):
        """Test partial update with some fields."""
        request = UpdateHostProfileRequest(hourly_rate_cents=6000)
        assert request.hourly_rate_cents == 6000
        assert request.bio is None

    def test_hourly_rate_validation(self):
        """Test hourly rate validation on update."""
        with pytest.raises(ValidationError) as exc_info:
            UpdateHostProfileRequest(hourly_rate_cents=50)
        assert "hourly_rate_cents" in str(exc_info.value)


class TestHostSearchRequest:
    """Tests for HostSearchRequest schema."""

    def test_defaults(self):
        """Test default values."""
        request = HostSearchRequest()
        assert request.latitude is None
        assert request.longitude is None
        assert request.radius_km == 50.0
        assert request.style_ids is None
        assert request.min_rating is None
        assert request.max_price_cents is None
        assert request.verified_only is False
        assert request.sort_by == "distance"
        assert request.sort_order == "asc"
        assert request.page == 1
        assert request.page_size == 20

    def test_with_location(self):
        """Test with location parameters."""
        request = HostSearchRequest(
            latitude=40.7128,
            longitude=-74.0060,
            radius_km=25.0,
        )
        assert request.latitude == 40.7128
        assert request.longitude == -74.0060
        assert request.radius_km == 25.0

    def test_with_filters(self):
        """Test with filter parameters."""
        request = HostSearchRequest(
            style_ids=["style-1", "style-2"],
            min_rating=4.0,
            max_price_cents=10000,
            verified_only=True,
        )
        assert request.style_ids == ["style-1", "style-2"]
        assert request.min_rating == 4.0
        assert request.max_price_cents == 10000
        assert request.verified_only is True

    def test_latitude_validation(self):
        """Test latitude range validation."""
        with pytest.raises(ValidationError) as exc_info:
            HostSearchRequest(latitude=91.0, longitude=0.0)
        assert "latitude" in str(exc_info.value)

    def test_longitude_validation(self):
        """Test longitude range validation."""
        with pytest.raises(ValidationError) as exc_info:
            HostSearchRequest(latitude=0.0, longitude=181.0)
        assert "longitude" in str(exc_info.value)

    def test_radius_minimum(self):
        """Test radius minimum (1 km)."""
        request = HostSearchRequest(radius_km=1.0)
        assert request.radius_km == 1.0

    def test_radius_maximum(self):
        """Test radius maximum (500 km)."""
        request = HostSearchRequest(radius_km=500.0)
        assert request.radius_km == 500.0

    def test_radius_below_minimum_fails(self):
        """Test radius below 1 km fails."""
        with pytest.raises(ValidationError) as exc_info:
            HostSearchRequest(radius_km=0.5)
        assert "radius_km" in str(exc_info.value)

    def test_radius_above_maximum_fails(self):
        """Test radius above 500 km fails."""
        with pytest.raises(ValidationError) as exc_info:
            HostSearchRequest(radius_km=501.0)
        assert "radius_km" in str(exc_info.value)

    def test_min_rating_range(self):
        """Test min_rating range validation."""
        # Valid range
        request = HostSearchRequest(min_rating=4.5)
        assert request.min_rating == 4.5

        # Below minimum
        with pytest.raises(ValidationError):
            HostSearchRequest(min_rating=0.5)

        # Above maximum
        with pytest.raises(ValidationError):
            HostSearchRequest(min_rating=5.5)

    def test_sort_by_valid_values(self):
        """Test valid sort_by values."""
        for sort_field in ["distance", "rating", "price", "reviews"]:
            request = HostSearchRequest(sort_by=sort_field)
            assert request.sort_by == sort_field

    def test_sort_by_invalid_value_fails(self):
        """Test invalid sort_by value fails."""
        with pytest.raises(ValidationError) as exc_info:
            HostSearchRequest(sort_by="invalid")
        assert "sort_by" in str(exc_info.value)

    def test_sort_order_valid_values(self):
        """Test valid sort_order values."""
        for order in ["asc", "desc"]:
            request = HostSearchRequest(sort_order=order)
            assert request.sort_order == order

    def test_sort_order_invalid_value_fails(self):
        """Test invalid sort_order value fails."""
        with pytest.raises(ValidationError) as exc_info:
            HostSearchRequest(sort_order="invalid")
        assert "sort_order" in str(exc_info.value)

    def test_page_minimum(self):
        """Test page minimum (1)."""
        request = HostSearchRequest(page=1)
        assert request.page == 1

    def test_page_below_minimum_fails(self):
        """Test page below 1 fails."""
        with pytest.raises(ValidationError) as exc_info:
            HostSearchRequest(page=0)
        assert "page" in str(exc_info.value)

    def test_page_size_range(self):
        """Test page_size range."""
        # Minimum
        request = HostSearchRequest(page_size=1)
        assert request.page_size == 1

        # Maximum
        request = HostSearchRequest(page_size=100)
        assert request.page_size == 100

    def test_page_size_above_maximum_fails(self):
        """Test page_size above 100 fails."""
        with pytest.raises(ValidationError) as exc_info:
            HostSearchRequest(page_size=101)
        assert "page_size" in str(exc_info.value)


class TestDanceStyleResponse:
    """Tests for DanceStyleResponse schema."""

    def test_from_dict(self):
        """Test creating from dictionary."""
        data = {
            "id": "style-id-123",
            "name": "Salsa",
            "slug": "salsa",
            "category": DanceStyleCategory.LATIN,
            "description": "A fun Latin dance!",
        }
        response = DanceStyleResponse(**data)
        assert response.id == "style-id-123"
        assert response.name == "Salsa"
        assert response.slug == "salsa"
        assert response.category == DanceStyleCategory.LATIN
        assert response.description == "A fun Latin dance!"

    def test_description_optional(self):
        """Test description is optional."""
        data = {
            "id": "style-id-123",
            "name": "Salsa",
            "slug": "salsa",
            "category": DanceStyleCategory.LATIN,
        }
        response = DanceStyleResponse(**data)
        assert response.description is None


class TestHostDanceStyleResponse:
    """Tests for HostDanceStyleResponse schema."""

    def test_from_dict(self):
        """Test creating from dictionary."""
        data = {
            "dance_style_id": "style-id-123",
            "skill_level": 4,
            "dance_style": {
                "id": "style-id-123",
                "name": "Salsa",
                "slug": "salsa",
                "category": DanceStyleCategory.LATIN,
                "description": None,
            },
        }
        response = HostDanceStyleResponse(**data)
        assert response.dance_style_id == "style-id-123"
        assert response.skill_level == 4
        assert response.dance_style.name == "Salsa"


class TestHostProfileResponse:
    """Tests for HostProfileResponse schema."""

    def test_from_dict(self):
        """Test creating from dictionary."""
        from datetime import datetime

        data = {
            "id": "profile-id-123",
            "user_id": "user-id-456",
            "bio": "I love dancing!",
            "headline": "Professional dancer",
            "hourly_rate_cents": 7500,
            "rating_average": 4.75,
            "total_reviews": 10,
            "total_sessions": 25,
            "verification_status": VerificationStatus.VERIFIED,
            "latitude": 40.7128,
            "longitude": -74.0060,
            "stripe_onboarding_complete": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "dance_styles": [],
        }
        response = HostProfileResponse(**data)
        assert response.id == "profile-id-123"
        assert response.user_id == "user-id-456"
        assert response.hourly_rate_cents == 7500
        assert response.rating_average == 4.75
        assert response.verification_status == VerificationStatus.VERIFIED
        assert response.latitude == 40.7128
        assert response.longitude == -74.0060

    def test_optional_fields(self):
        """Test optional fields can be None."""
        from datetime import datetime

        data = {
            "id": "profile-id-123",
            "user_id": "user-id-456",
            "bio": None,
            "headline": None,
            "hourly_rate_cents": 5000,
            "rating_average": None,
            "total_reviews": 0,
            "total_sessions": 0,
            "verification_status": VerificationStatus.UNVERIFIED,
            "latitude": None,
            "longitude": None,
            "stripe_onboarding_complete": False,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        response = HostProfileResponse(**data)
        assert response.bio is None
        assert response.headline is None
        assert response.rating_average is None
        assert response.latitude is None
        assert response.longitude is None

    def test_dance_styles_default(self):
        """Test dance_styles defaults to empty list."""
        from datetime import datetime

        data = {
            "id": "profile-id-123",
            "user_id": "user-id-456",
            "hourly_rate_cents": 5000,
            "total_reviews": 0,
            "total_sessions": 0,
            "verification_status": VerificationStatus.UNVERIFIED,
            "stripe_onboarding_complete": False,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        response = HostProfileResponse(**data)
        assert response.dance_styles == []


class TestHostProfileSummaryResponse:
    """Tests for HostProfileSummaryResponse schema."""

    def test_from_dict(self):
        """Test creating from dictionary."""
        data = {
            "id": "profile-id-123",
            "user_id": "user-id-456",
            "first_name": "John",
            "last_name": "Doe",
            "headline": "Pro dancer",
            "hourly_rate_cents": 5000,
            "rating_average": 4.5,
            "total_reviews": 10,
            "verification_status": VerificationStatus.VERIFIED,
            "distance_km": 5.2,
        }
        response = HostProfileSummaryResponse(**data)
        assert response.first_name == "John"
        assert response.last_name == "Doe"
        assert response.distance_km == 5.2


class TestHostSearchResponse:
    """Tests for HostSearchResponse schema."""

    def test_from_dict(self):
        """Test creating from dictionary."""
        data = {
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": 20,
            "total_pages": 0,
        }
        response = HostSearchResponse(**data)
        assert response.items == []
        assert response.total == 0
        assert response.page == 1
        assert response.page_size == 20
        assert response.total_pages == 0

    def test_with_items(self):
        """Test with actual items."""
        item_data = {
            "id": "profile-id-123",
            "user_id": "user-id-456",
            "first_name": "John",
            "last_name": "Doe",
            "headline": "Pro dancer",
            "hourly_rate_cents": 5000,
            "rating_average": 4.5,
            "total_reviews": 10,
            "verification_status": VerificationStatus.VERIFIED,
            "distance_km": 5.2,
        }
        data = {
            "items": [item_data],
            "total": 1,
            "page": 1,
            "page_size": 20,
            "total_pages": 1,
        }
        response = HostSearchResponse(**data)
        assert len(response.items) == 1
        assert response.items[0].first_name == "John"
        assert response.total == 1
