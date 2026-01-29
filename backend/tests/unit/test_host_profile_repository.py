"""Unit tests for HostProfileRepository."""

import inspect
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dance_style import DanceStyle, DanceStyleCategory
from app.models.host_dance_style import HostDanceStyle
from app.models.host_profile import HostProfile, VerificationStatus
from app.models.user import User, UserType
from app.repositories.host_profile import HostProfileRepository


@pytest.fixture
def mock_session():
    """Create a mock async session."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def host_profile_repository(mock_session):
    """Create a HostProfileRepository with a mock session."""
    return HostProfileRepository(mock_session)


@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    return User(
        id=uuid.uuid4(),
        email="host@example.com",
        password_hash="$argon2id$v=19$m=65536,t=3,p=4$...",
        first_name="Host",
        last_name="User",
        user_type=UserType.HOST,
        email_verified=True,
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_host_profile(sample_user):
    """Create a sample host profile for testing."""
    return HostProfile(
        id=uuid.uuid4(),
        user_id=str(sample_user.id),
        bio="I love dancing!",
        headline="Professional Dance Host",
        hourly_rate_cents=5000,
        rating_average=Decimal("4.75"),
        total_reviews=10,
        total_sessions=25,
        verification_status=VerificationStatus.VERIFIED,
        location=None,  # Set in specific tests
        stripe_account_id=None,
        stripe_onboarding_complete=False,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_dance_style():
    """Create a sample dance style for testing."""
    return DanceStyle(
        id=uuid.uuid4(),
        name="Salsa",
        slug="salsa",
        category=DanceStyleCategory.LATIN,
        description="A popular Latin dance",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_host_dance_style(sample_host_profile, sample_dance_style):
    """Create a sample host dance style junction for testing."""
    return HostDanceStyle(
        id=uuid.uuid4(),
        host_profile_id=str(sample_host_profile.id),
        dance_style_id=str(sample_dance_style.id),
        skill_level=4,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


class TestHostProfileRepositoryCreate:
    """Tests for HostProfileRepository.create() method."""

    async def test_create_host_profile_success(
        self, host_profile_repository, mock_session
    ):
        """Test successful host profile creation."""
        user_id = uuid.uuid4()

        result = await host_profile_repository.create(
            user_id=user_id,
            bio="Test bio",
            headline="Test headline",
            hourly_rate_cents=6000,
        )

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        assert result.user_id == str(user_id)
        assert result.bio == "Test bio"
        assert result.headline == "Test headline"
        assert result.hourly_rate_cents == 6000

    async def test_create_host_profile_with_defaults(
        self, host_profile_repository, mock_session
    ):
        """Test creating a host profile with default values."""
        user_id = uuid.uuid4()

        result = await host_profile_repository.create(user_id=user_id)

        assert result.hourly_rate_cents == 5000  # Default
        assert result.bio is None
        assert result.headline is None
        assert result.location is None

    async def test_create_host_profile_with_location(
        self, host_profile_repository, mock_session
    ):
        """Test creating a host profile with location."""
        user_id = uuid.uuid4()

        with (
            patch("app.repositories.host_profile.ST_SetSRID") as mock_srid,
            patch("app.repositories.host_profile.ST_MakePoint") as mock_point,
        ):
            mock_point.return_value = MagicMock()
            mock_srid.return_value = "POINT(-74.0 40.7)"

            result = await host_profile_repository.create(
                user_id=user_id,
                latitude=40.7,
                longitude=-74.0,
            )

            mock_point.assert_called_once_with(-74.0, 40.7)
            mock_srid.assert_called_once()
            assert result is not None


class TestHostProfileRepositoryGetById:
    """Tests for HostProfileRepository.get_by_id() method."""

    async def test_get_by_id_found(
        self, host_profile_repository, mock_session, sample_host_profile
    ):
        """Test getting a host profile by ID when it exists."""
        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = (
            sample_host_profile
        )
        mock_session.execute.return_value = mock_result

        result = await host_profile_repository.get_by_id(sample_host_profile.id)

        assert result == sample_host_profile
        mock_session.execute.assert_called_once()

    async def test_get_by_id_not_found(self, host_profile_repository, mock_session):
        """Test getting a host profile by ID when it doesn't exist."""
        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await host_profile_repository.get_by_id(uuid.uuid4())

        assert result is None


class TestHostProfileRepositoryGetByUserId:
    """Tests for HostProfileRepository.get_by_user_id() method."""

    async def test_get_by_user_id_found(
        self, host_profile_repository, mock_session, sample_host_profile, sample_user
    ):
        """Test getting a host profile by user ID when it exists."""
        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = (
            sample_host_profile
        )
        mock_session.execute.return_value = mock_result

        result = await host_profile_repository.get_by_user_id(sample_user.id)

        assert result == sample_host_profile
        mock_session.execute.assert_called_once()

    async def test_get_by_user_id_not_found(
        self, host_profile_repository, mock_session
    ):
        """Test getting a host profile by user ID when it doesn't exist."""
        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await host_profile_repository.get_by_user_id(uuid.uuid4())

        assert result is None


class TestHostProfileRepositoryUpdate:
    """Tests for HostProfileRepository.update() method."""

    async def test_update_profile_success(
        self, host_profile_repository, mock_session, sample_host_profile
    ):
        """Test successful host profile update."""
        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = (
            sample_host_profile
        )
        mock_session.execute.return_value = mock_result

        result = await host_profile_repository.update(
            profile_id=sample_host_profile.id,
            bio="Updated bio",
            headline="Updated headline",
        )

        assert result.bio == "Updated bio"
        assert result.headline == "Updated headline"
        mock_session.flush.assert_called_once()

    async def test_update_profile_not_found(
        self, host_profile_repository, mock_session
    ):
        """Test update returns None when profile doesn't exist."""
        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await host_profile_repository.update(
            profile_id=uuid.uuid4(),
            bio="New bio",
        )

        assert result is None

    async def test_update_partial_fields(
        self, host_profile_repository, mock_session, sample_host_profile
    ):
        """Test updating only specific fields."""
        original_headline = sample_host_profile.headline
        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = (
            sample_host_profile
        )
        mock_session.execute.return_value = mock_result

        result = await host_profile_repository.update(
            profile_id=sample_host_profile.id,
            hourly_rate_cents=7500,
        )

        assert result.hourly_rate_cents == 7500
        assert result.headline == original_headline  # Unchanged


class TestHostProfileRepositoryAddDanceStyle:
    """Tests for HostProfileRepository.add_dance_style() method."""

    async def test_add_dance_style_success(
        self, host_profile_repository, mock_session, sample_host_profile
    ):
        """Test adding a dance style to a profile."""
        # Mock get_by_id to return profile
        mock_profile_result = MagicMock()
        mock_profile_result.unique.return_value.scalar_one_or_none.return_value = (
            sample_host_profile
        )

        # Mock _get_host_dance_style to return None (new style)
        mock_style_result = MagicMock()
        mock_style_result.scalar_one_or_none.return_value = None

        mock_session.execute.side_effect = [mock_profile_result, mock_style_result]

        dance_style_id = uuid.uuid4()
        result = await host_profile_repository.add_dance_style(
            profile_id=sample_host_profile.id,
            dance_style_id=dance_style_id,
            skill_level=4,
        )

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        assert result is not None
        assert result.skill_level == 4

    async def test_add_dance_style_updates_existing(
        self,
        host_profile_repository,
        mock_session,
        sample_host_profile,
        sample_host_dance_style,
    ):
        """Test adding an existing dance style updates the skill level."""
        # Mock get_by_id to return profile
        mock_profile_result = MagicMock()
        mock_profile_result.unique.return_value.scalar_one_or_none.return_value = (
            sample_host_profile
        )

        # Mock _get_host_dance_style to return existing
        mock_style_result = MagicMock()
        mock_style_result.scalar_one_or_none.return_value = sample_host_dance_style

        mock_session.execute.side_effect = [mock_profile_result, mock_style_result]

        result = await host_profile_repository.add_dance_style(
            profile_id=sample_host_profile.id,
            dance_style_id=uuid.UUID(sample_host_dance_style.dance_style_id),
            skill_level=5,
        )

        assert result.skill_level == 5
        mock_session.add.assert_not_called()  # Should update, not add

    async def test_add_dance_style_invalid_skill_level_low(
        self, host_profile_repository, mock_session
    ):
        """Test add_dance_style raises error for skill level below 1."""
        with pytest.raises(ValueError, match="skill_level must be between 1 and 5"):
            await host_profile_repository.add_dance_style(
                profile_id=uuid.uuid4(),
                dance_style_id=uuid.uuid4(),
                skill_level=0,
            )

    async def test_add_dance_style_invalid_skill_level_high(
        self, host_profile_repository, mock_session
    ):
        """Test add_dance_style raises error for skill level above 5."""
        with pytest.raises(ValueError, match="skill_level must be between 1 and 5"):
            await host_profile_repository.add_dance_style(
                profile_id=uuid.uuid4(),
                dance_style_id=uuid.uuid4(),
                skill_level=6,
            )

    async def test_add_dance_style_profile_not_found(
        self, host_profile_repository, mock_session
    ):
        """Test add_dance_style returns None when profile doesn't exist."""
        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await host_profile_repository.add_dance_style(
            profile_id=uuid.uuid4(),
            dance_style_id=uuid.uuid4(),
            skill_level=3,
        )

        assert result is None


class TestHostProfileRepositoryRemoveDanceStyle:
    """Tests for HostProfileRepository.remove_dance_style() method."""

    async def test_remove_dance_style_success(
        self, host_profile_repository, mock_session, sample_host_dance_style
    ):
        """Test removing a dance style from a profile."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_host_dance_style
        mock_session.execute.return_value = mock_result

        result = await host_profile_repository.remove_dance_style(
            profile_id=uuid.UUID(sample_host_dance_style.host_profile_id),
            dance_style_id=uuid.UUID(sample_host_dance_style.dance_style_id),
        )

        assert result is True
        mock_session.delete.assert_called_once_with(sample_host_dance_style)
        mock_session.flush.assert_called_once()

    async def test_remove_dance_style_not_found(
        self, host_profile_repository, mock_session
    ):
        """Test remove_dance_style returns False when not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await host_profile_repository.remove_dance_style(
            profile_id=uuid.uuid4(),
            dance_style_id=uuid.uuid4(),
        )

        assert result is False
        mock_session.delete.assert_not_called()


class TestHostProfileRepositoryGetDanceStyles:
    """Tests for HostProfileRepository.get_dance_styles() method."""

    async def test_get_dance_styles_success(
        self, host_profile_repository, mock_session, sample_host_dance_style
    ):
        """Test getting dance styles for a profile."""
        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.all.return_value = [
            sample_host_dance_style
        ]
        mock_session.execute.return_value = mock_result

        result = await host_profile_repository.get_dance_styles(uuid.uuid4())

        assert len(result) == 1
        assert result[0] == sample_host_dance_style

    async def test_get_dance_styles_empty(self, host_profile_repository, mock_session):
        """Test getting dance styles for a profile with none."""
        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await host_profile_repository.get_dance_styles(uuid.uuid4())

        assert len(result) == 0


class TestHostProfileRepositoryGetNearby:
    """Tests for HostProfileRepository.get_nearby() method."""

    async def test_get_nearby_returns_profiles_with_distance(
        self, host_profile_repository, mock_session, sample_host_profile
    ):
        """Test get_nearby returns profiles with distance."""
        mock_row = MagicMock()
        mock_row.HostProfile = sample_host_profile
        mock_row.distance_km = 5.5

        mock_result = MagicMock()
        mock_result.unique.return_value.all.return_value = [mock_row]
        mock_session.execute.return_value = mock_result

        result = await host_profile_repository.get_nearby(
            latitude=40.7,
            longitude=-74.0,
            radius_km=10.0,
        )

        assert len(result) == 1
        profile, distance = result[0]
        assert profile == sample_host_profile
        assert distance == 5.5

    async def test_get_nearby_empty_results(
        self, host_profile_repository, mock_session
    ):
        """Test get_nearby returns empty list when no profiles nearby."""
        mock_result = MagicMock()
        mock_result.unique.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await host_profile_repository.get_nearby(
            latitude=40.7,
            longitude=-74.0,
            radius_km=1.0,
        )

        assert len(result) == 0

    async def test_get_nearby_respects_limit(
        self, host_profile_repository, mock_session
    ):
        """Test get_nearby respects limit parameter."""
        mock_result = MagicMock()
        mock_result.unique.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        await host_profile_repository.get_nearby(
            latitude=40.7,
            longitude=-74.0,
            radius_km=10.0,
            limit=5,
        )

        mock_session.execute.assert_called_once()


class TestHostProfileRepositorySearch:
    """Tests for HostProfileRepository.search() method."""

    async def test_search_returns_profiles_and_count(
        self, host_profile_repository, mock_session, sample_host_profile
    ):
        """Test search returns profiles list and total count."""
        # Mock count query
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        # Mock main query
        mock_profiles_result = MagicMock()
        mock_profiles_result.unique.return_value.scalars.return_value.all.return_value = [
            sample_host_profile
        ]

        mock_session.execute.side_effect = [mock_count_result, mock_profiles_result]

        profiles, count = await host_profile_repository.search()

        assert len(profiles) == 1
        assert count == 1

    async def test_search_with_location_filter(
        self, host_profile_repository, mock_session
    ):
        """Test search with location filter."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_profiles_result = MagicMock()
        mock_profiles_result.unique.return_value.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [mock_count_result, mock_profiles_result]

        profiles, count = await host_profile_repository.search(
            latitude=40.7,
            longitude=-74.0,
            radius_km=10.0,
        )

        assert len(profiles) == 0
        assert count == 0

    async def test_search_with_style_filter(
        self, host_profile_repository, mock_session
    ):
        """Test search with dance style filter."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_profiles_result = MagicMock()
        mock_profiles_result.unique.return_value.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [mock_count_result, mock_profiles_result]

        style_ids = [uuid.uuid4(), uuid.uuid4()]
        profiles, count = await host_profile_repository.search(style_ids=style_ids)

        assert mock_session.execute.call_count == 2

    async def test_search_with_rating_filter(
        self, host_profile_repository, mock_session
    ):
        """Test search with minimum rating filter."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_profiles_result = MagicMock()
        mock_profiles_result.unique.return_value.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [mock_count_result, mock_profiles_result]

        profiles, count = await host_profile_repository.search(min_rating=4.5)

        assert mock_session.execute.call_count == 2

    async def test_search_with_price_filter(
        self, host_profile_repository, mock_session
    ):
        """Test search with maximum price filter."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_profiles_result = MagicMock()
        mock_profiles_result.unique.return_value.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [mock_count_result, mock_profiles_result]

        profiles, count = await host_profile_repository.search(max_price_cents=5000)

        assert mock_session.execute.call_count == 2

    async def test_search_order_by_rating(self, host_profile_repository, mock_session):
        """Test search ordered by rating."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_profiles_result = MagicMock()
        mock_profiles_result.unique.return_value.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [mock_count_result, mock_profiles_result]

        await host_profile_repository.search(order_by="rating")

        assert mock_session.execute.call_count == 2

    async def test_search_order_by_price(self, host_profile_repository, mock_session):
        """Test search ordered by price."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_profiles_result = MagicMock()
        mock_profiles_result.unique.return_value.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [mock_count_result, mock_profiles_result]

        await host_profile_repository.search(order_by="price")

        assert mock_session.execute.call_count == 2


class TestHostProfileRepositoryGetAllDanceStyles:
    """Tests for HostProfileRepository.get_all_dance_styles() method."""

    async def test_get_all_dance_styles_success(
        self, host_profile_repository, mock_session, sample_dance_style
    ):
        """Test getting all dance styles."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_dance_style]
        mock_session.execute.return_value = mock_result

        result = await host_profile_repository.get_all_dance_styles()

        assert len(result) == 1
        assert result[0] == sample_dance_style

    async def test_get_all_dance_styles_empty(
        self, host_profile_repository, mock_session
    ):
        """Test getting all dance styles when none exist."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await host_profile_repository.get_all_dance_styles()

        assert len(result) == 0


class TestHostProfileRepositoryGetDanceStyleById:
    """Tests for HostProfileRepository.get_dance_style_by_id() method."""

    async def test_get_dance_style_by_id_found(
        self, host_profile_repository, mock_session, sample_dance_style
    ):
        """Test getting a dance style by ID when it exists."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_dance_style
        mock_session.execute.return_value = mock_result

        result = await host_profile_repository.get_dance_style_by_id(
            sample_dance_style.id
        )

        assert result == sample_dance_style

    async def test_get_dance_style_by_id_not_found(
        self, host_profile_repository, mock_session
    ):
        """Test getting a dance style by ID when it doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await host_profile_repository.get_dance_style_by_id(uuid.uuid4())

        assert result is None


class TestHostProfileRepositoryAsyncPatterns:
    """Tests to verify all methods use async patterns."""

    async def test_create_is_async(self, host_profile_repository):
        """Verify create method is async."""
        assert inspect.iscoroutinefunction(host_profile_repository.create)

    async def test_get_by_id_is_async(self, host_profile_repository):
        """Verify get_by_id method is async."""
        assert inspect.iscoroutinefunction(host_profile_repository.get_by_id)

    async def test_get_by_user_id_is_async(self, host_profile_repository):
        """Verify get_by_user_id method is async."""
        assert inspect.iscoroutinefunction(host_profile_repository.get_by_user_id)

    async def test_update_is_async(self, host_profile_repository):
        """Verify update method is async."""
        assert inspect.iscoroutinefunction(host_profile_repository.update)

    async def test_add_dance_style_is_async(self, host_profile_repository):
        """Verify add_dance_style method is async."""
        assert inspect.iscoroutinefunction(host_profile_repository.add_dance_style)

    async def test_remove_dance_style_is_async(self, host_profile_repository):
        """Verify remove_dance_style method is async."""
        assert inspect.iscoroutinefunction(host_profile_repository.remove_dance_style)

    async def test_get_nearby_is_async(self, host_profile_repository):
        """Verify get_nearby method is async."""
        assert inspect.iscoroutinefunction(host_profile_repository.get_nearby)

    async def test_search_is_async(self, host_profile_repository):
        """Verify search method is async."""
        assert inspect.iscoroutinefunction(host_profile_repository.search)

    async def test_get_all_dance_styles_is_async(self, host_profile_repository):
        """Verify get_all_dance_styles method is async."""
        assert inspect.iscoroutinefunction(host_profile_repository.get_all_dance_styles)

    async def test_get_dance_style_by_id_is_async(self, host_profile_repository):
        """Verify get_dance_style_by_id method is async."""
        assert inspect.iscoroutinefunction(
            host_profile_repository.get_dance_style_by_id
        )


class TestSearchWithFuzzyQuery:
    """Tests for search method with fuzzy text query parameter (pg_trgm)."""

    @pytest.fixture
    def host_profile_repository(self, mock_session):
        """Create repository with mock session."""
        from app.repositories.host_profile import HostProfileRepository

        return HostProfileRepository(mock_session)

    @pytest.fixture
    def mock_session(self):
        """Create mock async session."""
        session = MagicMock()
        session.execute = AsyncMock()
        session.flush = AsyncMock()
        session.add = MagicMock()
        return session

    async def test_search_accepts_query_parameter(
        self, host_profile_repository, mock_session
    ):
        """Test that search method accepts query parameter."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0
        mock_query_result = MagicMock()
        mock_query_result.unique.return_value.scalars.return_value.all.return_value = []

        mock_session.execute = AsyncMock(
            side_effect=[mock_count_result, mock_query_result]
        )

        # Should not raise an error
        profiles, count = await host_profile_repository.search(query="salsa")
        assert count == 0
        assert profiles == []

    async def test_search_with_empty_query(self, host_profile_repository, mock_session):
        """Test that search handles empty string query."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0
        mock_query_result = MagicMock()
        mock_query_result.unique.return_value.scalars.return_value.all.return_value = []

        mock_session.execute = AsyncMock(
            side_effect=[mock_count_result, mock_query_result]
        )

        # Empty query should not apply text search filters
        profiles, count = await host_profile_repository.search(query="")
        assert count == 0

    async def test_search_with_whitespace_only_query(
        self, host_profile_repository, mock_session
    ):
        """Test that search handles whitespace-only query."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0
        mock_query_result = MagicMock()
        mock_query_result.unique.return_value.scalars.return_value.all.return_value = []

        mock_session.execute = AsyncMock(
            side_effect=[mock_count_result, mock_query_result]
        )

        # Whitespace only should not apply text search filters
        profiles, count = await host_profile_repository.search(query="   ")
        assert count == 0

    async def test_search_query_combined_with_location(
        self, host_profile_repository, mock_session
    ):
        """Test that query can be combined with location filters."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0
        mock_query_result = MagicMock()
        mock_query_result.unique.return_value.scalars.return_value.all.return_value = []

        mock_session.execute = AsyncMock(
            side_effect=[mock_count_result, mock_query_result]
        )

        # Should not raise an error when combining query with location
        profiles, count = await host_profile_repository.search(
            query="dancer",
            latitude=40.7,
            longitude=-74.0,
            radius_km=10.0,
        )
        assert count == 0

    async def test_search_query_combined_with_filters(
        self, host_profile_repository, mock_session
    ):
        """Test that query can be combined with all other filters."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0
        mock_query_result = MagicMock()
        mock_query_result.unique.return_value.scalars.return_value.all.return_value = []

        mock_session.execute = AsyncMock(
            side_effect=[mock_count_result, mock_query_result]
        )

        # Should not raise an error when combining query with filters
        profiles, count = await host_profile_repository.search(
            query="tango",
            min_rating=4.0,
            max_price_cents=10000,
        )
        assert count == 0

    async def test_search_order_by_relevance(
        self, host_profile_repository, mock_session
    ):
        """Test that search can order by relevance."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0
        mock_query_result = MagicMock()
        mock_query_result.unique.return_value.scalars.return_value.all.return_value = []

        mock_session.execute = AsyncMock(
            side_effect=[mock_count_result, mock_query_result]
        )

        # Should not raise an error when ordering by relevance
        profiles, count = await host_profile_repository.search(
            query="salsa",
            order_by="relevance",
        )
        assert count == 0

    async def test_search_signature_includes_query(self, host_profile_repository):
        """Verify search method signature includes query parameter."""
        import inspect

        sig = inspect.signature(host_profile_repository.search)
        params = list(sig.parameters.keys())
        assert "query" in params

    async def test_search_query_default_is_none(self, host_profile_repository):
        """Verify query parameter defaults to None."""
        import inspect

        sig = inspect.signature(host_profile_repository.search)
        query_param = sig.parameters["query"]
        assert query_param.default is None
