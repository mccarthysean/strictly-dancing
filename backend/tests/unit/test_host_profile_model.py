"""Unit tests for the HostProfile database model."""

from decimal import Decimal

from app.models.host_profile import HostProfile, VerificationStatus


class TestHostProfileModel:
    """Tests for HostProfile model definition."""

    def test_host_profile_model_instantiation(self) -> None:
        """Test that HostProfile model can be instantiated with required fields."""
        profile = HostProfile(
            user_id="12345678-1234-1234-1234-123456789012",
            hourly_rate_cents=5000,
        )

        assert profile.user_id == "12345678-1234-1234-1234-123456789012"
        assert profile.hourly_rate_cents == 5000

    def test_host_profile_model_with_all_fields(self) -> None:
        """Test that HostProfile model can be instantiated with all fields."""
        profile = HostProfile(
            user_id="12345678-1234-1234-1234-123456789012",
            bio="Experienced dance instructor specializing in Latin styles.",
            headline="Professional Latin Dance Host",
            hourly_rate_cents=7500,
            rating_average=Decimal("4.85"),
            total_reviews=42,
            total_sessions=150,
            verification_status=VerificationStatus.VERIFIED,
            stripe_account_id="acct_123456789",
            stripe_onboarding_complete=True,
        )

        assert (
            profile.bio == "Experienced dance instructor specializing in Latin styles."
        )
        assert profile.headline == "Professional Latin Dance Host"
        assert profile.hourly_rate_cents == 7500
        assert profile.rating_average == Decimal("4.85")
        assert profile.total_reviews == 42
        assert profile.total_sessions == 150
        assert profile.verification_status == VerificationStatus.VERIFIED
        assert profile.stripe_account_id == "acct_123456789"
        assert profile.stripe_onboarding_complete is True

    def test_host_profile_model_has_required_fields(self) -> None:
        """Test that HostProfile model has all required fields."""
        columns = HostProfile.__table__.columns.keys()

        required_fields = [
            "id",
            "user_id",
            "bio",
            "headline",
            "hourly_rate_cents",
            "rating_average",
            "total_reviews",
            "total_sessions",
            "verification_status",
            "location",
            "stripe_account_id",
            "stripe_onboarding_complete",
            "created_at",
            "updated_at",
        ]

        for field in required_fields:
            assert field in columns, f"Missing required field: {field}"

    def test_host_profile_model_tablename(self) -> None:
        """Test that HostProfile model has correct table name."""
        assert HostProfile.__tablename__ == "host_profiles"


class TestHostProfileDefaults:
    """Tests for HostProfile model default values."""

    def test_default_hourly_rate(self) -> None:
        """Test that hourly_rate_cents has default value."""
        col = HostProfile.__table__.columns["hourly_rate_cents"]
        assert col.default is not None
        assert col.default.arg == 5000

    def test_default_total_reviews(self) -> None:
        """Test that total_reviews has default value of 0."""
        col = HostProfile.__table__.columns["total_reviews"]
        assert col.default is not None
        assert col.default.arg == 0

    def test_default_total_sessions(self) -> None:
        """Test that total_sessions has default value of 0."""
        col = HostProfile.__table__.columns["total_sessions"]
        assert col.default is not None
        assert col.default.arg == 0

    def test_default_verification_status(self) -> None:
        """Test that verification_status has default value of unverified."""
        col = HostProfile.__table__.columns["verification_status"]
        assert col.default is not None
        assert col.default.arg == VerificationStatus.UNVERIFIED

    def test_default_stripe_onboarding(self) -> None:
        """Test that stripe_onboarding_complete defaults to False."""
        col = HostProfile.__table__.columns["stripe_onboarding_complete"]
        assert col.default is not None
        assert col.default.arg is False


class TestVerificationStatus:
    """Tests for VerificationStatus enumeration."""

    def test_verification_status_enum_values(self) -> None:
        """Test that VerificationStatus enum has all required values."""
        assert VerificationStatus.UNVERIFIED.value == "unverified"
        assert VerificationStatus.PENDING.value == "pending"
        assert VerificationStatus.VERIFIED.value == "verified"
        assert VerificationStatus.REJECTED.value == "rejected"

    def test_verification_status_enum_is_string_enum(self) -> None:
        """Test that VerificationStatus is a string enum."""
        assert isinstance(VerificationStatus.UNVERIFIED, str)
        assert VerificationStatus.UNVERIFIED == "unverified"

    def test_verification_status_enum_count(self) -> None:
        """Test that VerificationStatus has exactly 4 values."""
        assert len(VerificationStatus) == 4


class TestHostProfileConstraints:
    """Tests for HostProfile model constraints."""

    def test_user_id_is_foreign_key(self) -> None:
        """Test that user_id column has foreign key constraint."""
        col = HostProfile.__table__.columns["user_id"]
        foreign_keys = list(col.foreign_keys)
        assert len(foreign_keys) == 1
        assert foreign_keys[0].column.table.name == "users"
        assert foreign_keys[0].column.name == "id"

    def test_user_id_is_unique(self) -> None:
        """Test that user_id column has unique constraint (one-to-one)."""
        col = HostProfile.__table__.columns["user_id"]
        assert col.unique is True

    def test_user_id_is_indexed(self) -> None:
        """Test that user_id column is indexed."""
        col = HostProfile.__table__.columns["user_id"]
        assert col.index is True

    def test_user_id_is_not_nullable(self) -> None:
        """Test that user_id column is not nullable."""
        col = HostProfile.__table__.columns["user_id"]
        assert col.nullable is False

    def test_id_is_primary_key(self) -> None:
        """Test that id column is primary key."""
        col = HostProfile.__table__.columns["id"]
        assert col.primary_key is True

    def test_hourly_rate_cents_is_not_nullable(self) -> None:
        """Test that hourly_rate_cents is not nullable."""
        col = HostProfile.__table__.columns["hourly_rate_cents"]
        assert col.nullable is False

    def test_verification_status_is_not_nullable(self) -> None:
        """Test that verification_status is not nullable."""
        col = HostProfile.__table__.columns["verification_status"]
        assert col.nullable is False


class TestHostProfileLocation:
    """Tests for HostProfile PostGIS location field."""

    def test_location_column_exists(self) -> None:
        """Test that location column exists."""
        columns = HostProfile.__table__.columns.keys()
        assert "location" in columns

    def test_location_is_nullable(self) -> None:
        """Test that location column is nullable."""
        col = HostProfile.__table__.columns["location"]
        assert col.nullable is True

    def test_location_is_geography_type(self) -> None:
        """Test that location column uses PostGIS GEOGRAPHY type."""
        col = HostProfile.__table__.columns["location"]
        col_type = col.type
        # GeoAlchemy2 Geography type
        assert col_type.__class__.__name__ == "Geography"


class TestHostProfileRepr:
    """Tests for HostProfile model representation."""

    def test_host_profile_repr(self) -> None:
        """Test that HostProfile __repr__ returns expected format."""
        profile = HostProfile(
            id="12345678-1234-1234-1234-123456789012",
            user_id="abcdefab-1234-1234-1234-123456789012",
            hourly_rate_cents=7500,
        )

        repr_str = repr(profile)
        assert "12345678-1234-1234-1234-123456789012" in repr_str
        assert "abcdefab-1234-1234-1234-123456789012" in repr_str
        assert "7500" in repr_str


class TestHostProfileRelationships:
    """Tests for HostProfile model relationships."""

    def test_user_relationship_exists(self) -> None:
        """Test that HostProfile has user relationship defined."""
        # Check the relationship is defined
        assert hasattr(HostProfile, "user")
        # The relationship mapper property should exist
        from sqlalchemy.orm import RelationshipProperty

        user_prop = HostProfile.__mapper__.relationships.get("user")
        assert user_prop is not None
        assert isinstance(user_prop, RelationshipProperty)

    def test_user_relationship_target(self) -> None:
        """Test that user relationship targets User model."""
        user_prop = HostProfile.__mapper__.relationships.get("user")
        assert user_prop is not None
        assert user_prop.mapper.class_.__name__ == "User"
