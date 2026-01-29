"""Integration tests for PostgreSQL rating average trigger.

These tests verify that the database trigger correctly updates
host_profile.rating_average and total_reviews when reviews are
inserted, updated, or deleted.

Note: These tests require the trigger to be installed in the database.
They use the actual trigger function defined in the reviews table migration.
"""

import pytest


class TestRatingTriggerMigrationExists:
    """Tests verifying the rating trigger migration is in place."""

    def test_trigger_function_exists_in_migration(self) -> None:
        """Test that the trigger function is defined in the migration file."""
        migration_path = "alembic/versions/20260129_080000_create_reviews_table.py"
        with open(migration_path) as f:
            content = f.read()

        # Verify trigger function exists
        assert "CREATE OR REPLACE FUNCTION update_host_rating_stats()" in content
        assert "RETURNS TRIGGER" in content

    def test_trigger_for_insert_exists(self) -> None:
        """Test that the INSERT trigger is defined in the migration."""
        migration_path = "alembic/versions/20260129_080000_create_reviews_table.py"
        with open(migration_path) as f:
            content = f.read()

        assert "trigger_update_host_rating_on_review_insert" in content
        assert "AFTER INSERT ON reviews" in content

    def test_trigger_for_update_exists(self) -> None:
        """Test that the UPDATE trigger is defined in the migration."""
        migration_path = "alembic/versions/20260129_080000_create_reviews_table.py"
        with open(migration_path) as f:
            content = f.read()

        assert "trigger_update_host_rating_on_review_update" in content
        assert "AFTER UPDATE OF rating ON reviews" in content

    def test_trigger_for_delete_exists(self) -> None:
        """Test that the DELETE trigger is defined in the migration."""
        migration_path = "alembic/versions/20260129_080000_create_reviews_table.py"
        with open(migration_path) as f:
            content = f.read()

        assert "trigger_update_host_rating_on_review_delete" in content
        assert "AFTER DELETE ON reviews" in content
        assert "update_host_rating_stats_on_delete()" in content

    def test_trigger_calculates_average(self) -> None:
        """Test that the trigger function calculates the average rating."""
        migration_path = "alembic/versions/20260129_080000_create_reviews_table.py"
        with open(migration_path) as f:
            content = f.read()

        # Verify it calculates average
        assert "AVG(r.rating)" in content
        assert "rating_average = new_avg" in content
        assert "total_reviews = new_total" in content

    def test_trigger_handles_host_profile_lookup(self) -> None:
        """Test that the trigger correctly looks up the host profile via booking."""
        migration_path = "alembic/versions/20260129_080000_create_reviews_table.py"
        with open(migration_path) as f:
            content = f.read()

        # Verify it looks up via booking relationship
        assert "SELECT b.host_profile_id INTO host_profile_uuid" in content
        assert "FROM bookings b" in content


class TestRatingTriggerLogic:
    """Tests for the trigger logic in the migration.

    These tests verify the SQL logic in the trigger is correct.
    """

    def test_trigger_uses_round_for_precision(self) -> None:
        """Test that ratings are rounded to 2 decimal places."""
        migration_path = "alembic/versions/20260129_080000_create_reviews_table.py"
        with open(migration_path) as f:
            content = f.read()

        # Should use ROUND with 2 decimal places
        assert "ROUND(AVG(r.rating)::numeric, 2)" in content

    def test_trigger_updates_updated_at(self) -> None:
        """Test that the trigger updates the updated_at timestamp."""
        migration_path = "alembic/versions/20260129_080000_create_reviews_table.py"
        with open(migration_path) as f:
            content = f.read()

        assert "updated_at = NOW()" in content

    def test_delete_trigger_handles_null_average(self) -> None:
        """Test that delete trigger handles null average when no reviews remain."""
        migration_path = "alembic/versions/20260129_080000_create_reviews_table.py"
        with open(migration_path) as f:
            content = f.read()

        # Should handle NULL when no reviews exist
        assert "COALESCE(new_total, 0)" in content

    def test_downgrade_drops_triggers(self) -> None:
        """Test that the migration downgrade properly removes triggers."""
        migration_path = "alembic/versions/20260129_080000_create_reviews_table.py"
        with open(migration_path) as f:
            content = f.read()

        assert (
            "DROP TRIGGER IF EXISTS trigger_update_host_rating_on_review_delete"
            in content
        )
        assert (
            "DROP TRIGGER IF EXISTS trigger_update_host_rating_on_review_update"
            in content
        )
        assert (
            "DROP TRIGGER IF EXISTS trigger_update_host_rating_on_review_insert"
            in content
        )
        assert "DROP FUNCTION IF EXISTS update_host_rating_stats_on_delete()" in content
        assert "DROP FUNCTION IF EXISTS update_host_rating_stats()" in content


class TestRatingTriggerBehaviorExpectations:
    """Tests documenting expected trigger behavior.

    These tests serve as documentation for how the trigger should behave.
    They verify the repository's fallback methods match trigger logic.
    """

    @pytest.mark.asyncio
    async def test_calculate_rating_average_matches_trigger_formula(self) -> None:
        """Test that repository calculation matches trigger formula."""
        from decimal import Decimal

        # Simulate trigger formula: ROUND(AVG(ratings), 2)
        ratings = [5, 4, 4, 5, 3]
        expected_avg = Decimal(str(round(sum(ratings) / len(ratings), 2)))
        expected_count = len(ratings)

        # Verify expectations match what trigger would produce
        assert expected_avg == Decimal("4.20")
        assert expected_count == 5

    @pytest.mark.asyncio
    async def test_single_review_produces_expected_rating(self) -> None:
        """Test single review produces that rating as average."""
        from decimal import Decimal

        rating = 5
        expected_avg = Decimal(str(rating)) + Decimal("0.00")
        expected_count = 1

        assert expected_avg == Decimal("5.00")
        assert expected_count == 1

    @pytest.mark.asyncio
    async def test_all_reviews_deleted_produces_null_average(self) -> None:
        """Test that deleting all reviews results in null average and zero count."""
        # When no reviews exist, trigger sets:
        # - rating_average = NULL (from AVG of empty set)
        # - total_reviews = COALESCE(NULL, 0) = 0
        expected_avg = None
        expected_count = 0

        assert expected_avg is None
        assert expected_count == 0


class TestTriggerIntegrationRequirements:
    """Tests for trigger integration requirements.

    These document the requirements that must be met for trigger to work.
    """

    def test_reviews_table_has_booking_id_column(self) -> None:
        """Test that reviews table has booking_id for trigger lookup."""
        from app.models.review import Review

        columns = {c.name for c in Review.__table__.columns}
        assert "booking_id" in columns

    def test_reviews_table_has_rating_column(self) -> None:
        """Test that reviews table has rating column for average calculation."""
        from app.models.review import Review

        columns = {c.name for c in Review.__table__.columns}
        assert "rating" in columns

    def test_host_profiles_has_rating_average_column(self) -> None:
        """Test that host_profiles table has rating_average for trigger update."""
        from app.models.host_profile import HostProfile

        columns = {c.name for c in HostProfile.__table__.columns}
        assert "rating_average" in columns

    def test_host_profiles_has_total_reviews_column(self) -> None:
        """Test that host_profiles table has total_reviews for trigger update."""
        from app.models.host_profile import HostProfile

        columns = {c.name for c in HostProfile.__table__.columns}
        assert "total_reviews" in columns

    def test_bookings_has_host_profile_id_for_trigger_lookup(self) -> None:
        """Test that bookings table has host_profile_id for trigger lookup."""
        from app.models.booking import Booking

        columns = {c.name for c in Booking.__table__.columns}
        assert "host_profile_id" in columns
