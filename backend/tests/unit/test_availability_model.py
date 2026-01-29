"""Unit tests for the Availability database models."""

from datetime import date, time

from app.models.availability import (
    AvailabilityOverride,
    AvailabilityOverrideType,
    DayOfWeek,
    RecurringAvailability,
)


class TestDayOfWeekEnum:
    """Tests for DayOfWeek enumeration."""

    def test_day_of_week_has_all_days(self) -> None:
        """Test that DayOfWeek enum has all 7 days."""
        assert len(DayOfWeek) == 7

    def test_day_of_week_values(self) -> None:
        """Test DayOfWeek enum values match expected days."""
        assert DayOfWeek.MONDAY.value == 0
        assert DayOfWeek.TUESDAY.value == 1
        assert DayOfWeek.WEDNESDAY.value == 2
        assert DayOfWeek.THURSDAY.value == 3
        assert DayOfWeek.FRIDAY.value == 4
        assert DayOfWeek.SATURDAY.value == 5
        assert DayOfWeek.SUNDAY.value == 6


class TestAvailabilityOverrideTypeEnum:
    """Tests for AvailabilityOverrideType enumeration."""

    def test_override_type_has_expected_values(self) -> None:
        """Test AvailabilityOverrideType enum has available and blocked."""
        assert AvailabilityOverrideType.AVAILABLE.value == "available"
        assert AvailabilityOverrideType.BLOCKED.value == "blocked"

    def test_override_type_is_string_enum(self) -> None:
        """Test that AvailabilityOverrideType is a string enum."""
        assert isinstance(AvailabilityOverrideType.AVAILABLE.value, str)
        assert isinstance(AvailabilityOverrideType.BLOCKED.value, str)


class TestRecurringAvailabilityModel:
    """Tests for RecurringAvailability model definition."""

    def test_recurring_availability_instantiation(self) -> None:
        """Test that RecurringAvailability can be instantiated with required fields."""
        availability = RecurringAvailability(
            host_profile_id="11111111-1111-1111-1111-111111111111",
            day_of_week=DayOfWeek.MONDAY,
            start_time=time(9, 0),
            end_time=time(17, 0),
        )

        assert availability.host_profile_id == "11111111-1111-1111-1111-111111111111"
        assert availability.day_of_week == DayOfWeek.MONDAY
        assert availability.start_time == time(9, 0)
        assert availability.end_time == time(17, 0)

    def test_recurring_availability_with_all_fields(self) -> None:
        """Test RecurringAvailability with all optional fields."""
        availability = RecurringAvailability(
            host_profile_id="11111111-1111-1111-1111-111111111111",
            day_of_week=DayOfWeek.SATURDAY,
            start_time=time(10, 0),
            end_time=time(18, 0),
            is_active=True,
        )

        assert availability.day_of_week == DayOfWeek.SATURDAY
        assert availability.start_time == time(10, 0)
        assert availability.end_time == time(18, 0)
        assert availability.is_active is True

    def test_recurring_availability_has_required_columns(self) -> None:
        """Test that RecurringAvailability model has all required columns."""
        columns = RecurringAvailability.__table__.columns.keys()

        required_columns = [
            "id",
            "host_profile_id",
            "day_of_week",
            "start_time",
            "end_time",
            "is_active",
            "created_at",
            "updated_at",
        ]

        for column in required_columns:
            assert column in columns, f"Missing column: {column}"

    def test_recurring_availability_tablename(self) -> None:
        """Test RecurringAvailability model has correct table name."""
        assert RecurringAvailability.__tablename__ == "recurring_availability"

    def test_recurring_availability_host_profile_fk(self) -> None:
        """Test RecurringAvailability has foreign key to host_profiles."""
        fk_columns = [
            fk.column.table.name for fk in RecurringAvailability.__table__.foreign_keys
        ]
        assert "host_profiles" in fk_columns

    def test_recurring_availability_day_of_week_is_indexed(self) -> None:
        """Test that day_of_week column is indexed for query performance."""
        indexes = RecurringAvailability.__table__.indexes
        index_columns = set()
        for idx in indexes:
            for col in idx.columns:
                index_columns.add(col.name)
        assert "day_of_week" in index_columns or any(
            "day_of_week" in str(idx) for idx in indexes
        )

    def test_recurring_availability_repr(self) -> None:
        """Test RecurringAvailability string representation."""
        availability = RecurringAvailability(
            id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            host_profile_id="11111111-1111-1111-1111-111111111111",
            day_of_week=DayOfWeek.FRIDAY,
            start_time=time(14, 0),
            end_time=time(20, 0),
        )

        repr_str = repr(availability)
        assert "RecurringAvailability" in repr_str
        assert "FRIDAY" in repr_str

    def test_recurring_availability_with_inactive_status(self) -> None:
        """Test RecurringAvailability can be set to inactive."""
        availability = RecurringAvailability(
            host_profile_id="11111111-1111-1111-1111-111111111111",
            day_of_week=DayOfWeek.TUESDAY,
            start_time=time(8, 0),
            end_time=time(12, 0),
            is_active=False,
        )

        assert availability.is_active is False


class TestAvailabilityOverrideModel:
    """Tests for AvailabilityOverride model definition."""

    def test_availability_override_instantiation_available(self) -> None:
        """Test AvailabilityOverride can be instantiated for available time."""
        override = AvailabilityOverride(
            host_profile_id="11111111-1111-1111-1111-111111111111",
            override_date=date(2026, 2, 15),
            override_type=AvailabilityOverrideType.AVAILABLE,
            start_time=time(10, 0),
            end_time=time(14, 0),
        )

        assert override.host_profile_id == "11111111-1111-1111-1111-111111111111"
        assert override.override_date == date(2026, 2, 15)
        assert override.override_type == AvailabilityOverrideType.AVAILABLE
        assert override.start_time == time(10, 0)
        assert override.end_time == time(14, 0)

    def test_availability_override_instantiation_blocked(self) -> None:
        """Test AvailabilityOverride can be instantiated for blocked time."""
        override = AvailabilityOverride(
            host_profile_id="11111111-1111-1111-1111-111111111111",
            override_date=date(2026, 3, 25),
            override_type=AvailabilityOverrideType.BLOCKED,
            start_time=time(0, 0),
            end_time=time(23, 59),
            reason="Vacation day",
        )

        assert override.override_type == AvailabilityOverrideType.BLOCKED
        assert override.reason == "Vacation day"

    def test_availability_override_with_all_day_block(self) -> None:
        """Test AvailabilityOverride for full day block (no start/end time)."""
        override = AvailabilityOverride(
            host_profile_id="11111111-1111-1111-1111-111111111111",
            override_date=date(2026, 12, 25),
            override_type=AvailabilityOverrideType.BLOCKED,
            all_day=True,
            reason="Christmas Day - unavailable",
        )

        assert override.all_day is True
        assert override.reason == "Christmas Day - unavailable"

    def test_availability_override_has_required_columns(self) -> None:
        """Test that AvailabilityOverride model has all required columns."""
        columns = AvailabilityOverride.__table__.columns.keys()

        required_columns = [
            "id",
            "host_profile_id",
            "override_date",
            "override_type",
            "start_time",
            "end_time",
            "all_day",
            "reason",
            "created_at",
            "updated_at",
        ]

        for column in required_columns:
            assert column in columns, f"Missing column: {column}"

    def test_availability_override_tablename(self) -> None:
        """Test AvailabilityOverride model has correct table name."""
        assert AvailabilityOverride.__tablename__ == "availability_overrides"

    def test_availability_override_host_profile_fk(self) -> None:
        """Test AvailabilityOverride has foreign key to host_profiles."""
        fk_columns = [
            fk.column.table.name for fk in AvailabilityOverride.__table__.foreign_keys
        ]
        assert "host_profiles" in fk_columns

    def test_availability_override_date_is_indexed(self) -> None:
        """Test that override_date column is indexed for query performance."""
        indexes = AvailabilityOverride.__table__.indexes
        index_columns = set()
        for idx in indexes:
            for col in idx.columns:
                index_columns.add(col.name)
        assert "override_date" in index_columns

    def test_availability_override_repr(self) -> None:
        """Test AvailabilityOverride string representation."""
        override = AvailabilityOverride(
            id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            host_profile_id="11111111-1111-1111-1111-111111111111",
            override_date=date(2026, 7, 4),
            override_type=AvailabilityOverrideType.BLOCKED,
            all_day=True,
        )

        repr_str = repr(override)
        assert "AvailabilityOverride" in repr_str
        assert "2026-07-04" in repr_str

    def test_availability_override_partial_day_block(self) -> None:
        """Test AvailabilityOverride for partial day block."""
        override = AvailabilityOverride(
            host_profile_id="11111111-1111-1111-1111-111111111111",
            override_date=date(2026, 4, 15),
            override_type=AvailabilityOverrideType.BLOCKED,
            start_time=time(9, 0),
            end_time=time(12, 0),
            all_day=False,
            reason="Doctor appointment",
        )

        assert override.all_day is False
        assert override.start_time == time(9, 0)
        assert override.end_time == time(12, 0)
        assert override.reason == "Doctor appointment"

    def test_availability_override_one_time_available_slot(self) -> None:
        """Test AvailabilityOverride for adding one-time available slot."""
        override = AvailabilityOverride(
            host_profile_id="11111111-1111-1111-1111-111111111111",
            override_date=date(2026, 5, 1),
            override_type=AvailabilityOverrideType.AVAILABLE,
            start_time=time(18, 0),
            end_time=time(22, 0),
            all_day=False,
            reason="Special evening availability for May Day",
        )

        assert override.override_type == AvailabilityOverrideType.AVAILABLE
        assert override.start_time == time(18, 0)
        assert override.end_time == time(22, 0)


class TestAvailabilityModelRelationships:
    """Tests for availability model relationships."""

    def test_recurring_availability_has_host_profile_relationship(self) -> None:
        """Test RecurringAvailability has relationship to HostProfile."""
        # Check that the relationship attribute exists on the mapper
        mapper_relationships = [
            r.key for r in RecurringAvailability.__mapper__.relationships
        ]
        assert "host_profile" in mapper_relationships

    def test_availability_override_has_host_profile_relationship(self) -> None:
        """Test AvailabilityOverride has relationship to HostProfile."""
        # Check that the relationship attribute exists on the mapper
        mapper_relationships = [
            r.key for r in AvailabilityOverride.__mapper__.relationships
        ]
        assert "host_profile" in mapper_relationships


class TestAvailabilityModelConstraints:
    """Tests for availability model constraints."""

    def test_recurring_availability_has_composite_index(self) -> None:
        """Test RecurringAvailability has composite index on host_profile_id + day_of_week."""
        indexes = list(RecurringAvailability.__table__.indexes)
        composite_found = False
        for idx in indexes:
            col_names = [col.name for col in idx.columns]
            if "host_profile_id" in col_names and "day_of_week" in col_names:
                composite_found = True
                break
        assert composite_found, (
            "Missing composite index on (host_profile_id, day_of_week)"
        )

    def test_availability_override_has_composite_index(self) -> None:
        """Test AvailabilityOverride has composite index on host_profile_id + override_date."""
        indexes = list(AvailabilityOverride.__table__.indexes)
        composite_found = False
        for idx in indexes:
            col_names = [col.name for col in idx.columns]
            if "host_profile_id" in col_names and "override_date" in col_names:
                composite_found = True
                break
        assert composite_found, (
            "Missing composite index on (host_profile_id, override_date)"
        )
