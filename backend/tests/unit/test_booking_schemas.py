"""Unit tests for booking Pydantic schemas."""

from datetime import UTC, date, datetime, time

import pytest
from pydantic import ValidationError

from app.models.availability import AvailabilityOverrideType, DayOfWeek
from app.models.booking import BookingStatus
from app.schemas.booking import (
    AvailabilityForDateRangeResponse,
    AvailabilityForDateResponse,
    AvailabilityOverrideRequest,
    AvailabilityOverrideResponse,
    AvailabilitySlot,
    AvailabilitySlotWithDate,
    BookingListResponse,
    BookingLocationRequest,
    BookingResponse,
    BookingWithDetailsResponse,
    CancelBookingRequest,
    CreateBookingRequest,
    DanceStyleSummaryResponse,
    HostAvailabilityResponse,
    RecurringAvailabilityRequest,
    RecurringAvailabilityResponse,
    UserSummaryResponse,
)


class TestBookingLocationRequest:
    """Tests for BookingLocationRequest schema."""

    def test_valid_location(self):
        """Test valid booking location."""
        location = BookingLocationRequest(
            latitude=40.7128,
            longitude=-74.0060,
            location_name="Central Park",
            location_notes="Meet at the fountain",
        )
        assert location.latitude == 40.7128
        assert location.longitude == -74.0060
        assert location.location_name == "Central Park"
        assert location.location_notes == "Meet at the fountain"

    def test_location_without_name_and_notes(self):
        """Test location with only coordinates."""
        location = BookingLocationRequest(latitude=40.7128, longitude=-74.0060)
        assert location.latitude == 40.7128
        assert location.longitude == -74.0060
        assert location.location_name is None
        assert location.location_notes is None

    def test_latitude_at_bounds(self):
        """Test latitude at valid bounds."""
        location = BookingLocationRequest(latitude=-90.0, longitude=0.0)
        assert location.latitude == -90.0

        location = BookingLocationRequest(latitude=90.0, longitude=0.0)
        assert location.latitude == 90.0

    def test_longitude_at_bounds(self):
        """Test longitude at valid bounds."""
        location = BookingLocationRequest(latitude=0.0, longitude=-180.0)
        assert location.longitude == -180.0

        location = BookingLocationRequest(latitude=0.0, longitude=180.0)
        assert location.longitude == 180.0

    def test_latitude_out_of_range_fails(self):
        """Test latitude outside valid range fails."""
        with pytest.raises(ValidationError) as exc_info:
            BookingLocationRequest(latitude=-90.1, longitude=0.0)
        assert "latitude" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            BookingLocationRequest(latitude=90.1, longitude=0.0)
        assert "latitude" in str(exc_info.value)

    def test_longitude_out_of_range_fails(self):
        """Test longitude outside valid range fails."""
        with pytest.raises(ValidationError) as exc_info:
            BookingLocationRequest(latitude=0.0, longitude=-180.1)
        assert "longitude" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            BookingLocationRequest(latitude=0.0, longitude=180.1)
        assert "longitude" in str(exc_info.value)


class TestCreateBookingRequest:
    """Tests for CreateBookingRequest schema."""

    def test_valid_booking_request(self):
        """Test valid booking request."""
        request = CreateBookingRequest(
            host_id="550e8400-e29b-41d4-a716-446655440000",
            scheduled_start=datetime(2026, 2, 1, 14, 0, tzinfo=UTC),
            duration_minutes=60,
        )
        assert request.host_id == "550e8400-e29b-41d4-a716-446655440000"
        assert request.duration_minutes == 60
        assert request.dance_style_id is None
        assert request.location is None
        assert request.client_notes is None

    def test_valid_booking_with_all_fields(self):
        """Test valid booking request with all optional fields."""
        request = CreateBookingRequest(
            host_id="550e8400-e29b-41d4-a716-446655440000",
            dance_style_id="660e8400-e29b-41d4-a716-446655440001",
            scheduled_start=datetime(2026, 2, 1, 14, 0, tzinfo=UTC),
            duration_minutes=90,
            location=BookingLocationRequest(
                latitude=40.7128,
                longitude=-74.0060,
                location_name="Dance Studio",
            ),
            client_notes="Looking forward to the session!",
        )
        assert request.dance_style_id == "660e8400-e29b-41d4-a716-446655440001"
        assert request.location is not None
        assert request.location.location_name == "Dance Studio"
        assert request.client_notes == "Looking forward to the session!"

    def test_duration_minimum_30_minutes(self):
        """Test duration minimum of 30 minutes."""
        request = CreateBookingRequest(
            host_id="test-id",
            scheduled_start=datetime(2026, 2, 1, 14, 0, tzinfo=UTC),
            duration_minutes=30,
        )
        assert request.duration_minutes == 30

    def test_duration_maximum_240_minutes(self):
        """Test duration maximum of 240 minutes (4 hours)."""
        request = CreateBookingRequest(
            host_id="test-id",
            scheduled_start=datetime(2026, 2, 1, 14, 0, tzinfo=UTC),
            duration_minutes=240,
        )
        assert request.duration_minutes == 240

    def test_duration_below_minimum_fails(self):
        """Test duration below 30 minutes fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            CreateBookingRequest(
                host_id="test-id",
                scheduled_start=datetime(2026, 2, 1, 14, 0, tzinfo=UTC),
                duration_minutes=29,
            )
        error_msg = str(exc_info.value)
        assert "duration_minutes" in error_msg or "30" in error_msg

    def test_duration_above_maximum_fails(self):
        """Test duration above 240 minutes fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            CreateBookingRequest(
                host_id="test-id",
                scheduled_start=datetime(2026, 2, 1, 14, 0, tzinfo=UTC),
                duration_minutes=241,
            )
        error_msg = str(exc_info.value)
        assert "duration_minutes" in error_msg or "240" in error_msg

    def test_missing_host_id_fails(self):
        """Test missing host_id fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            CreateBookingRequest(
                scheduled_start=datetime(2026, 2, 1, 14, 0, tzinfo=UTC),
                duration_minutes=60,
            )
        assert "host_id" in str(exc_info.value)

    def test_missing_scheduled_start_fails(self):
        """Test missing scheduled_start fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            CreateBookingRequest(
                host_id="test-id",
                duration_minutes=60,
            )
        assert "scheduled_start" in str(exc_info.value)


class TestCancelBookingRequest:
    """Tests for CancelBookingRequest schema."""

    def test_cancel_with_reason(self):
        """Test cancel request with reason."""
        request = CancelBookingRequest(reason="Schedule conflict")
        assert request.reason == "Schedule conflict"

    def test_cancel_without_reason(self):
        """Test cancel request without reason (optional)."""
        request = CancelBookingRequest()
        assert request.reason is None


class TestUserSummaryResponse:
    """Tests for UserSummaryResponse schema."""

    def test_valid_user_summary(self):
        """Test valid user summary response."""
        response = UserSummaryResponse(
            id="550e8400-e29b-41d4-a716-446655440000",
            first_name="John",
            last_name="Doe",
        )
        assert response.id == "550e8400-e29b-41d4-a716-446655440000"
        assert response.first_name == "John"
        assert response.last_name == "Doe"


class TestDanceStyleSummaryResponse:
    """Tests for DanceStyleSummaryResponse schema."""

    def test_valid_dance_style_summary(self):
        """Test valid dance style summary response."""
        response = DanceStyleSummaryResponse(
            id="550e8400-e29b-41d4-a716-446655440000",
            name="Salsa",
        )
        assert response.id == "550e8400-e29b-41d4-a716-446655440000"
        assert response.name == "Salsa"


class TestBookingResponse:
    """Tests for BookingResponse schema."""

    def test_valid_booking_response(self):
        """Test valid booking response with required fields."""
        now = datetime.now(UTC)
        response = BookingResponse(
            id="550e8400-e29b-41d4-a716-446655440000",
            client_id="client-uuid",
            host_id="host-uuid",
            host_profile_id="profile-uuid",
            dance_style_id=None,
            status=BookingStatus.PENDING,
            scheduled_start=now,
            scheduled_end=now,
            actual_start=None,
            actual_end=None,
            duration_minutes=60,
            latitude=None,
            longitude=None,
            location_name=None,
            location_notes=None,
            hourly_rate_cents=5000,
            amount_cents=5000,
            platform_fee_cents=750,
            host_payout_cents=4250,
            client_notes=None,
            host_notes=None,
            cancellation_reason=None,
            cancelled_by_id=None,
            cancelled_at=None,
            created_at=now,
            updated_at=now,
        )
        assert response.id == "550e8400-e29b-41d4-a716-446655440000"
        assert response.status == BookingStatus.PENDING
        assert response.duration_minutes == 60
        assert response.amount_cents == 5000

    def test_booking_response_with_all_statuses(self):
        """Test booking response accepts all status values."""
        now = datetime.now(UTC)
        base_data = {
            "id": "test-id",
            "client_id": "client-uuid",
            "host_id": "host-uuid",
            "host_profile_id": "profile-uuid",
            "dance_style_id": None,
            "scheduled_start": now,
            "scheduled_end": now,
            "actual_start": None,
            "actual_end": None,
            "duration_minutes": 60,
            "latitude": None,
            "longitude": None,
            "location_name": None,
            "location_notes": None,
            "hourly_rate_cents": 5000,
            "amount_cents": 5000,
            "platform_fee_cents": 750,
            "host_payout_cents": 4250,
            "client_notes": None,
            "host_notes": None,
            "cancellation_reason": None,
            "cancelled_by_id": None,
            "cancelled_at": None,
            "created_at": now,
            "updated_at": now,
        }

        for status in BookingStatus:
            response = BookingResponse(**{**base_data, "status": status})
            assert response.status == status


class TestBookingWithDetailsResponse:
    """Tests for BookingWithDetailsResponse schema."""

    def test_booking_with_details_includes_relations(self):
        """Test booking with details includes client, host, and dance style."""
        now = datetime.now(UTC)
        response = BookingWithDetailsResponse(
            id="550e8400-e29b-41d4-a716-446655440000",
            client_id="client-uuid",
            host_id="host-uuid",
            host_profile_id="profile-uuid",
            dance_style_id="style-uuid",
            status=BookingStatus.CONFIRMED,
            scheduled_start=now,
            scheduled_end=now,
            actual_start=None,
            actual_end=None,
            duration_minutes=60,
            latitude=40.7128,
            longitude=-74.0060,
            location_name="Dance Studio",
            location_notes="Ring the bell",
            hourly_rate_cents=5000,
            amount_cents=5000,
            platform_fee_cents=750,
            host_payout_cents=4250,
            client_notes="First session",
            host_notes=None,
            cancellation_reason=None,
            cancelled_by_id=None,
            cancelled_at=None,
            created_at=now,
            updated_at=now,
            client=UserSummaryResponse(
                id="client-uuid", first_name="Jane", last_name="Doe"
            ),
            host=UserSummaryResponse(
                id="host-uuid", first_name="John", last_name="Smith"
            ),
            dance_style=DanceStyleSummaryResponse(id="style-uuid", name="Salsa"),
        )
        assert response.client is not None
        assert response.client.first_name == "Jane"
        assert response.host is not None
        assert response.host.first_name == "John"
        assert response.dance_style is not None
        assert response.dance_style.name == "Salsa"


class TestBookingListResponse:
    """Tests for BookingListResponse schema."""

    def test_valid_booking_list_response(self):
        """Test valid booking list response."""
        response = BookingListResponse(
            items=[],
            total=0,
            page=1,
            page_size=20,
            total_pages=0,
        )
        assert response.items == []
        assert response.total == 0
        assert response.page == 1
        assert response.page_size == 20

    def test_booking_list_with_items(self):
        """Test booking list with booking items."""
        now = datetime.now(UTC)
        booking = BookingWithDetailsResponse(
            id="test-id",
            client_id="client-uuid",
            host_id="host-uuid",
            host_profile_id="profile-uuid",
            dance_style_id=None,
            status=BookingStatus.PENDING,
            scheduled_start=now,
            scheduled_end=now,
            actual_start=None,
            actual_end=None,
            duration_minutes=60,
            latitude=None,
            longitude=None,
            location_name=None,
            location_notes=None,
            hourly_rate_cents=5000,
            amount_cents=5000,
            platform_fee_cents=750,
            host_payout_cents=4250,
            client_notes=None,
            host_notes=None,
            cancellation_reason=None,
            cancelled_by_id=None,
            cancelled_at=None,
            created_at=now,
            updated_at=now,
            client=None,
            host=None,
            dance_style=None,
        )
        response = BookingListResponse(
            items=[booking],
            total=1,
            page=1,
            page_size=20,
            total_pages=1,
        )
        assert len(response.items) == 1
        assert response.total == 1


class TestAvailabilitySlot:
    """Tests for AvailabilitySlot schema."""

    def test_valid_slot(self):
        """Test valid availability slot."""
        slot = AvailabilitySlot(
            start_time=time(9, 0),
            end_time=time(17, 0),
        )
        assert slot.start_time == time(9, 0)
        assert slot.end_time == time(17, 0)

    def test_slot_with_minutes(self):
        """Test slot with minute precision."""
        slot = AvailabilitySlot(
            start_time=time(9, 30),
            end_time=time(12, 45),
        )
        assert slot.start_time == time(9, 30)
        assert slot.end_time == time(12, 45)


class TestAvailabilitySlotWithDate:
    """Tests for AvailabilitySlotWithDate schema."""

    def test_valid_slot_with_date(self):
        """Test valid availability slot with date."""
        slot = AvailabilitySlotWithDate(
            slot_date=date(2026, 2, 1),
            start_time=time(9, 0),
            end_time=time(17, 0),
        )
        assert slot.slot_date == date(2026, 2, 1)
        assert slot.start_time == time(9, 0)
        assert slot.end_time == time(17, 0)


class TestRecurringAvailabilityRequest:
    """Tests for RecurringAvailabilityRequest schema."""

    def test_valid_recurring_request(self):
        """Test valid recurring availability request."""
        request = RecurringAvailabilityRequest(
            day_of_week=DayOfWeek.MONDAY,
            start_time=time(9, 0),
            end_time=time(17, 0),
        )
        assert request.day_of_week == DayOfWeek.MONDAY
        assert request.start_time == time(9, 0)
        assert request.end_time == time(17, 0)

    def test_all_days_of_week(self):
        """Test all days of week are accepted."""
        for day in DayOfWeek:
            request = RecurringAvailabilityRequest(
                day_of_week=day,
                start_time=time(9, 0),
                end_time=time(17, 0),
            )
            assert request.day_of_week == day

    def test_end_time_before_start_fails(self):
        """Test that end_time before start_time fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            RecurringAvailabilityRequest(
                day_of_week=DayOfWeek.MONDAY,
                start_time=time(17, 0),
                end_time=time(9, 0),
            )
        assert "end_time" in str(exc_info.value)

    def test_end_time_equal_start_fails(self):
        """Test that end_time equal to start_time fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            RecurringAvailabilityRequest(
                day_of_week=DayOfWeek.MONDAY,
                start_time=time(9, 0),
                end_time=time(9, 0),
            )
        assert "end_time" in str(exc_info.value)


class TestRecurringAvailabilityResponse:
    """Tests for RecurringAvailabilityResponse schema."""

    def test_valid_response(self):
        """Test valid recurring availability response."""
        response = RecurringAvailabilityResponse(
            id="test-uuid",
            day_of_week=DayOfWeek.TUESDAY,
            start_time=time(10, 0),
            end_time=time(18, 0),
            is_active=True,
        )
        assert response.id == "test-uuid"
        assert response.day_of_week == DayOfWeek.TUESDAY
        assert response.is_active is True


class TestAvailabilityOverrideRequest:
    """Tests for AvailabilityOverrideRequest schema."""

    def test_valid_available_override(self):
        """Test valid available override request."""
        request = AvailabilityOverrideRequest(
            override_date=date(2026, 2, 15),
            override_type=AvailabilityOverrideType.AVAILABLE,
            start_time=time(9, 0),
            end_time=time(12, 0),
            all_day=False,
            reason="Special session",
        )
        assert request.override_date == date(2026, 2, 15)
        assert request.override_type == AvailabilityOverrideType.AVAILABLE
        assert request.start_time == time(9, 0)
        assert request.end_time == time(12, 0)
        assert request.all_day is False
        assert request.reason == "Special session"

    def test_valid_blocked_override(self):
        """Test valid blocked override request."""
        request = AvailabilityOverrideRequest(
            override_date=date(2026, 2, 20),
            override_type=AvailabilityOverrideType.BLOCKED,
            all_day=True,
            reason="Vacation day",
        )
        assert request.override_type == AvailabilityOverrideType.BLOCKED
        assert request.all_day is True
        assert request.start_time is None
        assert request.end_time is None

    def test_all_day_with_times_fails(self):
        """Test that all_day=True with end_time fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            AvailabilityOverrideRequest(
                override_date=date(2026, 2, 20),
                override_type=AvailabilityOverrideType.BLOCKED,
                start_time=time(9, 0),
                end_time=time(17, 0),
                all_day=True,
            )
        assert "end_time" in str(exc_info.value) or "all_day" in str(exc_info.value)

    def test_end_time_before_start_fails(self):
        """Test that end_time before start_time fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            AvailabilityOverrideRequest(
                override_date=date(2026, 2, 15),
                override_type=AvailabilityOverrideType.AVAILABLE,
                start_time=time(17, 0),
                end_time=time(9, 0),
                all_day=False,
            )
        assert "end_time" in str(exc_info.value)


class TestAvailabilityOverrideResponse:
    """Tests for AvailabilityOverrideResponse schema."""

    def test_valid_response(self):
        """Test valid availability override response."""
        response = AvailabilityOverrideResponse(
            id="test-uuid",
            override_date=date(2026, 2, 15),
            override_type=AvailabilityOverrideType.BLOCKED,
            start_time=time(9, 0),
            end_time=time(12, 0),
            all_day=False,
            reason="Dentist appointment",
        )
        assert response.id == "test-uuid"
        assert response.override_type == AvailabilityOverrideType.BLOCKED
        assert response.reason == "Dentist appointment"


class TestHostAvailabilityResponse:
    """Tests for HostAvailabilityResponse schema."""

    def test_empty_availability(self):
        """Test host availability response with no schedules."""
        response = HostAvailabilityResponse(
            host_profile_id="profile-uuid",
            recurring=[],
            overrides=[],
        )
        assert response.host_profile_id == "profile-uuid"
        assert response.recurring == []
        assert response.overrides == []

    def test_availability_with_schedules(self):
        """Test host availability response with schedules."""
        recurring = RecurringAvailabilityResponse(
            id="recurring-uuid",
            day_of_week=DayOfWeek.MONDAY,
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_active=True,
        )
        override = AvailabilityOverrideResponse(
            id="override-uuid",
            override_date=date(2026, 2, 15),
            override_type=AvailabilityOverrideType.BLOCKED,
            start_time=None,
            end_time=None,
            all_day=True,
            reason="Holiday",
        )
        response = HostAvailabilityResponse(
            host_profile_id="profile-uuid",
            recurring=[recurring],
            overrides=[override],
        )
        assert len(response.recurring) == 1
        assert len(response.overrides) == 1


class TestAvailabilityForDateResponse:
    """Tests for AvailabilityForDateResponse schema."""

    def test_no_slots_available(self):
        """Test availability response with no slots."""
        response = AvailabilityForDateResponse(
            availability_date=date(2026, 2, 15),
            slots=[],
        )
        assert response.availability_date == date(2026, 2, 15)
        assert response.slots == []

    def test_multiple_slots(self):
        """Test availability response with multiple slots."""
        slots = [
            AvailabilitySlot(start_time=time(9, 0), end_time=time(12, 0)),
            AvailabilitySlot(start_time=time(14, 0), end_time=time(17, 0)),
        ]
        response = AvailabilityForDateResponse(
            availability_date=date(2026, 2, 15),
            slots=slots,
        )
        assert len(response.slots) == 2


class TestAvailabilityForDateRangeResponse:
    """Tests for AvailabilityForDateRangeResponse schema."""

    def test_valid_date_range_response(self):
        """Test valid date range availability response."""
        response = AvailabilityForDateRangeResponse(
            host_profile_id="profile-uuid",
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 7),
            availability=[],
        )
        assert response.host_profile_id == "profile-uuid"
        assert response.start_date == date(2026, 2, 1)
        assert response.end_date == date(2026, 2, 7)

    def test_date_range_with_availability(self):
        """Test date range response with availability data."""
        day1 = AvailabilityForDateResponse(
            availability_date=date(2026, 2, 1),
            slots=[AvailabilitySlot(start_time=time(9, 0), end_time=time(17, 0))],
        )
        day2 = AvailabilityForDateResponse(
            availability_date=date(2026, 2, 2),
            slots=[],
        )
        response = AvailabilityForDateRangeResponse(
            host_profile_id="profile-uuid",
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 7),
            availability=[day1, day2],
        )
        assert len(response.availability) == 2
        assert len(response.availability[0].slots) == 1
        assert len(response.availability[1].slots) == 0


class TestBookingSchemaValidation:
    """Tests specifically for duration validation (requirement from T038)."""

    def test_booking_schema_duration_validation_30_minutes(self):
        """Test duration validation accepts minimum 30 minutes."""
        request = CreateBookingRequest(
            host_id="test-id",
            scheduled_start=datetime(2026, 2, 1, 14, 0, tzinfo=UTC),
            duration_minutes=30,
        )
        assert request.duration_minutes == 30

    def test_booking_schema_duration_validation_60_minutes(self):
        """Test duration validation accepts 60 minutes."""
        request = CreateBookingRequest(
            host_id="test-id",
            scheduled_start=datetime(2026, 2, 1, 14, 0, tzinfo=UTC),
            duration_minutes=60,
        )
        assert request.duration_minutes == 60

    def test_booking_schema_duration_validation_90_minutes(self):
        """Test duration validation accepts 90 minutes."""
        request = CreateBookingRequest(
            host_id="test-id",
            scheduled_start=datetime(2026, 2, 1, 14, 0, tzinfo=UTC),
            duration_minutes=90,
        )
        assert request.duration_minutes == 90

    def test_booking_schema_duration_validation_120_minutes(self):
        """Test duration validation accepts 120 minutes."""
        request = CreateBookingRequest(
            host_id="test-id",
            scheduled_start=datetime(2026, 2, 1, 14, 0, tzinfo=UTC),
            duration_minutes=120,
        )
        assert request.duration_minutes == 120

    def test_booking_schema_duration_validation_180_minutes(self):
        """Test duration validation accepts 180 minutes."""
        request = CreateBookingRequest(
            host_id="test-id",
            scheduled_start=datetime(2026, 2, 1, 14, 0, tzinfo=UTC),
            duration_minutes=180,
        )
        assert request.duration_minutes == 180

    def test_booking_schema_duration_validation_240_minutes(self):
        """Test duration validation accepts maximum 240 minutes."""
        request = CreateBookingRequest(
            host_id="test-id",
            scheduled_start=datetime(2026, 2, 1, 14, 0, tzinfo=UTC),
            duration_minutes=240,
        )
        assert request.duration_minutes == 240

    def test_booking_schema_duration_validation_rejects_29_minutes(self):
        """Test duration validation rejects 29 minutes (below minimum)."""
        with pytest.raises(ValidationError):
            CreateBookingRequest(
                host_id="test-id",
                scheduled_start=datetime(2026, 2, 1, 14, 0, tzinfo=UTC),
                duration_minutes=29,
            )

    def test_booking_schema_duration_validation_rejects_241_minutes(self):
        """Test duration validation rejects 241 minutes (above maximum)."""
        with pytest.raises(ValidationError):
            CreateBookingRequest(
                host_id="test-id",
                scheduled_start=datetime(2026, 2, 1, 14, 0, tzinfo=UTC),
                duration_minutes=241,
            )

    def test_booking_schema_duration_validation_rejects_zero(self):
        """Test duration validation rejects 0 minutes."""
        with pytest.raises(ValidationError):
            CreateBookingRequest(
                host_id="test-id",
                scheduled_start=datetime(2026, 2, 1, 14, 0, tzinfo=UTC),
                duration_minutes=0,
            )

    def test_booking_schema_duration_validation_rejects_negative(self):
        """Test duration validation rejects negative duration."""
        with pytest.raises(ValidationError):
            CreateBookingRequest(
                host_id="test-id",
                scheduled_start=datetime(2026, 2, 1, 14, 0, tzinfo=UTC),
                duration_minutes=-60,
            )
