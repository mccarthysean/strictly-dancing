"""Unit tests for the Booking database model."""

from datetime import UTC, datetime, timedelta

from app.models.booking import Booking, BookingStatus


class TestBookingModel:
    """Tests for Booking model definition."""

    def test_booking_model_instantiation(self) -> None:
        """Test that Booking model can be instantiated with required fields."""
        now = datetime.now(UTC)
        booking = Booking(
            client_id="11111111-1111-1111-1111-111111111111",
            host_id="22222222-2222-2222-2222-222222222222",
            host_profile_id="33333333-3333-3333-3333-333333333333",
            scheduled_start=now,
            scheduled_end=now + timedelta(hours=1),
            duration_minutes=60,
            hourly_rate_cents=5000,
            amount_cents=5000,
        )

        assert booking.client_id == "11111111-1111-1111-1111-111111111111"
        assert booking.host_id == "22222222-2222-2222-2222-222222222222"
        assert booking.host_profile_id == "33333333-3333-3333-3333-333333333333"
        assert booking.duration_minutes == 60
        assert booking.hourly_rate_cents == 5000
        assert booking.amount_cents == 5000

    def test_booking_model_with_all_fields(self) -> None:
        """Test that Booking model can be instantiated with all fields."""
        now = datetime.now(UTC)
        booking = Booking(
            client_id="11111111-1111-1111-1111-111111111111",
            host_id="22222222-2222-2222-2222-222222222222",
            host_profile_id="33333333-3333-3333-3333-333333333333",
            dance_style_id="44444444-4444-4444-4444-444444444444",
            status=BookingStatus.CONFIRMED,
            scheduled_start=now,
            scheduled_end=now + timedelta(hours=2),
            actual_start=now + timedelta(minutes=5),
            actual_end=now + timedelta(hours=2, minutes=5),
            duration_minutes=120,
            location_name="Dance Studio NYC",
            location_notes="Second floor, studio B",
            hourly_rate_cents=7500,
            amount_cents=15000,
            platform_fee_cents=1500,
            host_payout_cents=13500,
            stripe_payment_intent_id="pi_123456789",
            stripe_transfer_id="tr_123456789",
            client_notes="Looking forward to learning salsa!",
            host_notes="Client has some experience with bachata.",
        )

        assert booking.dance_style_id == "44444444-4444-4444-4444-444444444444"
        assert booking.status == BookingStatus.CONFIRMED
        assert booking.duration_minutes == 120
        assert booking.location_name == "Dance Studio NYC"
        assert booking.location_notes == "Second floor, studio B"
        assert booking.hourly_rate_cents == 7500
        assert booking.amount_cents == 15000
        assert booking.platform_fee_cents == 1500
        assert booking.host_payout_cents == 13500
        assert booking.stripe_payment_intent_id == "pi_123456789"
        assert booking.stripe_transfer_id == "tr_123456789"
        assert booking.client_notes == "Looking forward to learning salsa!"
        assert booking.host_notes == "Client has some experience with bachata."

    def test_booking_model_has_required_fields(self) -> None:
        """Test that Booking model has all required fields."""
        columns = Booking.__table__.columns.keys()

        required_fields = [
            "id",
            "client_id",
            "host_id",
            "host_profile_id",
            "dance_style_id",
            "status",
            "scheduled_start",
            "scheduled_end",
            "actual_start",
            "actual_end",
            "duration_minutes",
            "location",
            "location_name",
            "location_notes",
            "hourly_rate_cents",
            "amount_cents",
            "platform_fee_cents",
            "host_payout_cents",
            "stripe_payment_intent_id",
            "stripe_transfer_id",
            "client_notes",
            "host_notes",
            "cancellation_reason",
            "cancelled_by_id",
            "cancelled_at",
            "created_at",
            "updated_at",
        ]

        for field in required_fields:
            assert field in columns, f"Missing required field: {field}"

    def test_booking_model_tablename(self) -> None:
        """Test that Booking model has correct table name."""
        assert Booking.__tablename__ == "bookings"


class TestBookingStatus:
    """Tests for BookingStatus enumeration."""

    def test_booking_status_enum_values(self) -> None:
        """Test that BookingStatus enum has all required values."""
        assert BookingStatus.PENDING.value == "pending"
        assert BookingStatus.CONFIRMED.value == "confirmed"
        assert BookingStatus.IN_PROGRESS.value == "in_progress"
        assert BookingStatus.COMPLETED.value == "completed"
        assert BookingStatus.CANCELLED.value == "cancelled"
        assert BookingStatus.DISPUTED.value == "disputed"

    def test_booking_status_enum_is_string_enum(self) -> None:
        """Test that BookingStatus is a string enum."""
        assert isinstance(BookingStatus.PENDING, str)
        assert BookingStatus.PENDING == "pending"

    def test_booking_status_enum_count(self) -> None:
        """Test that BookingStatus has exactly 6 values."""
        assert len(BookingStatus) == 6

    def test_booking_status_enum_complete(self) -> None:
        """Test that BookingStatus has all expected status values."""
        expected_statuses = {
            "pending",
            "confirmed",
            "in_progress",
            "completed",
            "cancelled",
            "disputed",
        }
        actual_statuses = {status.value for status in BookingStatus}
        assert actual_statuses == expected_statuses


class TestBookingDefaults:
    """Tests for Booking model default values."""

    def test_default_status(self) -> None:
        """Test that status has default value of pending."""
        col = Booking.__table__.columns["status"]
        assert col.default is not None
        assert col.default.arg == BookingStatus.PENDING

    def test_default_platform_fee_cents(self) -> None:
        """Test that platform_fee_cents has default value of 0."""
        col = Booking.__table__.columns["platform_fee_cents"]
        assert col.default is not None
        assert col.default.arg == 0

    def test_default_host_payout_cents(self) -> None:
        """Test that host_payout_cents has default value of 0."""
        col = Booking.__table__.columns["host_payout_cents"]
        assert col.default is not None
        assert col.default.arg == 0


class TestBookingForeignKeys:
    """Tests for Booking model foreign key constraints."""

    def test_client_id_is_foreign_key(self) -> None:
        """Test that client_id column has foreign key to users table."""
        col = Booking.__table__.columns["client_id"]
        foreign_keys = list(col.foreign_keys)
        assert len(foreign_keys) == 1
        assert foreign_keys[0].column.table.name == "users"
        assert foreign_keys[0].column.name == "id"

    def test_host_id_is_foreign_key(self) -> None:
        """Test that host_id column has foreign key to users table."""
        col = Booking.__table__.columns["host_id"]
        foreign_keys = list(col.foreign_keys)
        assert len(foreign_keys) == 1
        assert foreign_keys[0].column.table.name == "users"
        assert foreign_keys[0].column.name == "id"

    def test_host_profile_id_is_foreign_key(self) -> None:
        """Test that host_profile_id column has foreign key to host_profiles table."""
        col = Booking.__table__.columns["host_profile_id"]
        foreign_keys = list(col.foreign_keys)
        assert len(foreign_keys) == 1
        assert foreign_keys[0].column.table.name == "host_profiles"
        assert foreign_keys[0].column.name == "id"

    def test_dance_style_id_is_foreign_key(self) -> None:
        """Test that dance_style_id column has foreign key to dance_styles table."""
        col = Booking.__table__.columns["dance_style_id"]
        foreign_keys = list(col.foreign_keys)
        assert len(foreign_keys) == 1
        assert foreign_keys[0].column.table.name == "dance_styles"
        assert foreign_keys[0].column.name == "id"

    def test_cancelled_by_id_is_foreign_key(self) -> None:
        """Test that cancelled_by_id column has foreign key to users table."""
        col = Booking.__table__.columns["cancelled_by_id"]
        foreign_keys = list(col.foreign_keys)
        assert len(foreign_keys) == 1
        assert foreign_keys[0].column.table.name == "users"
        assert foreign_keys[0].column.name == "id"


class TestBookingIndexes:
    """Tests for Booking model indexes."""

    def test_client_id_is_indexed(self) -> None:
        """Test that client_id column is indexed."""
        col = Booking.__table__.columns["client_id"]
        assert col.index is True

    def test_host_id_is_indexed(self) -> None:
        """Test that host_id column is indexed."""
        col = Booking.__table__.columns["host_id"]
        assert col.index is True

    def test_host_profile_id_is_indexed(self) -> None:
        """Test that host_profile_id column is indexed."""
        col = Booking.__table__.columns["host_profile_id"]
        assert col.index is True

    def test_dance_style_id_is_indexed(self) -> None:
        """Test that dance_style_id column is indexed."""
        col = Booking.__table__.columns["dance_style_id"]
        assert col.index is True

    def test_status_is_indexed(self) -> None:
        """Test that status column is indexed."""
        col = Booking.__table__.columns["status"]
        assert col.index is True

    def test_stripe_payment_intent_id_is_indexed(self) -> None:
        """Test that stripe_payment_intent_id column is indexed."""
        col = Booking.__table__.columns["stripe_payment_intent_id"]
        assert col.index is True


class TestBookingNullability:
    """Tests for Booking model nullability constraints."""

    def test_client_id_is_not_nullable(self) -> None:
        """Test that client_id column is not nullable."""
        col = Booking.__table__.columns["client_id"]
        assert col.nullable is False

    def test_host_id_is_not_nullable(self) -> None:
        """Test that host_id column is not nullable."""
        col = Booking.__table__.columns["host_id"]
        assert col.nullable is False

    def test_host_profile_id_is_not_nullable(self) -> None:
        """Test that host_profile_id column is not nullable."""
        col = Booking.__table__.columns["host_profile_id"]
        assert col.nullable is False

    def test_dance_style_id_is_nullable(self) -> None:
        """Test that dance_style_id column is nullable (optional style)."""
        col = Booking.__table__.columns["dance_style_id"]
        assert col.nullable is True

    def test_status_is_not_nullable(self) -> None:
        """Test that status column is not nullable."""
        col = Booking.__table__.columns["status"]
        assert col.nullable is False

    def test_scheduled_start_is_not_nullable(self) -> None:
        """Test that scheduled_start column is not nullable."""
        col = Booking.__table__.columns["scheduled_start"]
        assert col.nullable is False

    def test_scheduled_end_is_not_nullable(self) -> None:
        """Test that scheduled_end column is not nullable."""
        col = Booking.__table__.columns["scheduled_end"]
        assert col.nullable is False

    def test_actual_start_is_nullable(self) -> None:
        """Test that actual_start column is nullable (only set when session starts)."""
        col = Booking.__table__.columns["actual_start"]
        assert col.nullable is True

    def test_actual_end_is_nullable(self) -> None:
        """Test that actual_end column is nullable (only set when session ends)."""
        col = Booking.__table__.columns["actual_end"]
        assert col.nullable is True

    def test_duration_minutes_is_not_nullable(self) -> None:
        """Test that duration_minutes column is not nullable."""
        col = Booking.__table__.columns["duration_minutes"]
        assert col.nullable is False

    def test_hourly_rate_cents_is_not_nullable(self) -> None:
        """Test that hourly_rate_cents column is not nullable."""
        col = Booking.__table__.columns["hourly_rate_cents"]
        assert col.nullable is False

    def test_amount_cents_is_not_nullable(self) -> None:
        """Test that amount_cents column is not nullable."""
        col = Booking.__table__.columns["amount_cents"]
        assert col.nullable is False

    def test_location_is_nullable(self) -> None:
        """Test that location column is nullable."""
        col = Booking.__table__.columns["location"]
        assert col.nullable is True

    def test_cancellation_reason_is_nullable(self) -> None:
        """Test that cancellation_reason column is nullable."""
        col = Booking.__table__.columns["cancellation_reason"]
        assert col.nullable is True

    def test_cancelled_by_id_is_nullable(self) -> None:
        """Test that cancelled_by_id column is nullable."""
        col = Booking.__table__.columns["cancelled_by_id"]
        assert col.nullable is True

    def test_cancelled_at_is_nullable(self) -> None:
        """Test that cancelled_at column is nullable."""
        col = Booking.__table__.columns["cancelled_at"]
        assert col.nullable is True


class TestBookingLocation:
    """Tests for Booking PostGIS location field."""

    def test_location_column_exists(self) -> None:
        """Test that location column exists."""
        columns = Booking.__table__.columns.keys()
        assert "location" in columns

    def test_location_is_geography_type(self) -> None:
        """Test that location column uses PostGIS GEOGRAPHY type."""
        col = Booking.__table__.columns["location"]
        col_type = col.type
        # GeoAlchemy2 Geography type
        assert col_type.__class__.__name__ == "Geography"


class TestBookingRepr:
    """Tests for Booking model representation."""

    def test_booking_repr(self) -> None:
        """Test that Booking __repr__ returns expected format."""
        now = datetime.now(UTC)
        booking = Booking(
            id="12345678-1234-1234-1234-123456789012",
            client_id="11111111-1111-1111-1111-111111111111",
            host_id="22222222-2222-2222-2222-222222222222",
            host_profile_id="33333333-3333-3333-3333-333333333333",
            status=BookingStatus.PENDING,
            scheduled_start=now,
            scheduled_end=now + timedelta(hours=1),
            duration_minutes=60,
            hourly_rate_cents=5000,
            amount_cents=5000,
        )

        repr_str = repr(booking)
        assert "12345678-1234-1234-1234-123456789012" in repr_str
        assert "11111111-1111-1111-1111-111111111111" in repr_str
        assert "22222222-2222-2222-2222-222222222222" in repr_str
        assert "PENDING" in repr_str or "pending" in repr_str


class TestBookingRelationships:
    """Tests for Booking model relationships."""

    def test_client_relationship_exists(self) -> None:
        """Test that Booking has client relationship defined."""
        assert hasattr(Booking, "client")
        from sqlalchemy.orm import RelationshipProperty

        client_prop = Booking.__mapper__.relationships.get("client")
        assert client_prop is not None
        assert isinstance(client_prop, RelationshipProperty)

    def test_host_relationship_exists(self) -> None:
        """Test that Booking has host relationship defined."""
        assert hasattr(Booking, "host")
        from sqlalchemy.orm import RelationshipProperty

        host_prop = Booking.__mapper__.relationships.get("host")
        assert host_prop is not None
        assert isinstance(host_prop, RelationshipProperty)

    def test_host_profile_relationship_exists(self) -> None:
        """Test that Booking has host_profile relationship defined."""
        assert hasattr(Booking, "host_profile")
        from sqlalchemy.orm import RelationshipProperty

        hp_prop = Booking.__mapper__.relationships.get("host_profile")
        assert hp_prop is not None
        assert isinstance(hp_prop, RelationshipProperty)

    def test_dance_style_relationship_exists(self) -> None:
        """Test that Booking has dance_style relationship defined."""
        assert hasattr(Booking, "dance_style")
        from sqlalchemy.orm import RelationshipProperty

        ds_prop = Booking.__mapper__.relationships.get("dance_style")
        assert ds_prop is not None
        assert isinstance(ds_prop, RelationshipProperty)

    def test_cancelled_by_relationship_exists(self) -> None:
        """Test that Booking has cancelled_by relationship defined."""
        assert hasattr(Booking, "cancelled_by")
        from sqlalchemy.orm import RelationshipProperty

        cb_prop = Booking.__mapper__.relationships.get("cancelled_by")
        assert cb_prop is not None
        assert isinstance(cb_prop, RelationshipProperty)

    def test_client_relationship_target(self) -> None:
        """Test that client relationship targets User model."""
        client_prop = Booking.__mapper__.relationships.get("client")
        assert client_prop is not None
        assert client_prop.mapper.class_.__name__ == "User"

    def test_host_relationship_target(self) -> None:
        """Test that host relationship targets User model."""
        host_prop = Booking.__mapper__.relationships.get("host")
        assert host_prop is not None
        assert host_prop.mapper.class_.__name__ == "User"

    def test_host_profile_relationship_target(self) -> None:
        """Test that host_profile relationship targets HostProfile model."""
        hp_prop = Booking.__mapper__.relationships.get("host_profile")
        assert hp_prop is not None
        assert hp_prop.mapper.class_.__name__ == "HostProfile"

    def test_dance_style_relationship_target(self) -> None:
        """Test that dance_style relationship targets DanceStyle model."""
        ds_prop = Booking.__mapper__.relationships.get("dance_style")
        assert ds_prop is not None
        assert ds_prop.mapper.class_.__name__ == "DanceStyle"


class TestBookingAmountFields:
    """Tests for Booking amount fields (in cents)."""

    def test_hourly_rate_cents_column_type(self) -> None:
        """Test that hourly_rate_cents uses Integer type (in cents)."""
        col = Booking.__table__.columns["hourly_rate_cents"]
        assert col.type.__class__.__name__ == "Integer"

    def test_amount_cents_column_type(self) -> None:
        """Test that amount_cents uses Integer type (in cents)."""
        col = Booking.__table__.columns["amount_cents"]
        assert col.type.__class__.__name__ == "Integer"

    def test_platform_fee_cents_column_type(self) -> None:
        """Test that platform_fee_cents uses Integer type (in cents)."""
        col = Booking.__table__.columns["platform_fee_cents"]
        assert col.type.__class__.__name__ == "Integer"

    def test_host_payout_cents_column_type(self) -> None:
        """Test that host_payout_cents uses Integer type (in cents)."""
        col = Booking.__table__.columns["host_payout_cents"]
        assert col.type.__class__.__name__ == "Integer"


class TestBookingPrimaryKey:
    """Tests for Booking primary key."""

    def test_id_is_primary_key(self) -> None:
        """Test that id column is primary key."""
        col = Booking.__table__.columns["id"]
        assert col.primary_key is True
