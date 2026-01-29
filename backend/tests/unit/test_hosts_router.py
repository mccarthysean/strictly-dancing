"""Unit tests for hosts router endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import create_app
from app.models.dance_style import DanceStyleCategory
from app.models.host_profile import VerificationStatus


@pytest.fixture
def app():
    """Create a test FastAPI application."""
    return create_app()


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


def create_mock_user(
    user_id: str = "550e8400-e29b-41d4-a716-446655440000",
    first_name: str = "Test",
    last_name: str = "Host",
) -> MagicMock:
    """Create a mock user for testing."""
    mock_user = MagicMock()
    mock_user.id = user_id
    mock_user.first_name = first_name
    mock_user.last_name = last_name
    return mock_user


def create_mock_host_profile(
    profile_id: str = "660e8400-e29b-41d4-a716-446655440001",
    user_id: str = "550e8400-e29b-41d4-a716-446655440000",
    headline: str | None = "Experienced Salsa Instructor",
    hourly_rate_cents: int = 5000,
    rating_average: float | None = 4.5,
    total_reviews: int = 10,
    verification_status: VerificationStatus = VerificationStatus.VERIFIED,
    location: MagicMock | None = None,
    user: MagicMock | None = None,
) -> MagicMock:
    """Create a mock host profile for testing."""
    mock_profile = MagicMock()
    mock_profile.id = profile_id
    mock_profile.user_id = user_id
    mock_profile.headline = headline
    mock_profile.hourly_rate_cents = hourly_rate_cents
    mock_profile.rating_average = rating_average
    mock_profile.total_reviews = total_reviews
    mock_profile.verification_status = verification_status
    mock_profile.location = location
    mock_profile.user = user or create_mock_user(user_id)
    return mock_profile


class TestSearchHostsEndpoint:
    """Tests for GET /api/v1/hosts endpoint."""

    def test_search_hosts_endpoint_exists(self, client: TestClient) -> None:
        """Test that the search hosts endpoint exists and accepts GET."""
        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search.return_value = ([], 0)

            response = client.get("/api/v1/hosts")
            assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_search_hosts_returns_paginated_response(self, client: TestClient) -> None:
        """Test that search hosts returns a paginated response."""
        mock_profile = create_mock_host_profile()

        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search.return_value = ([mock_profile], 1)

            response = client.get("/api/v1/hosts")
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert "items" in data
            assert "total" in data
            assert "page" in data
            assert "page_size" in data
            assert "total_pages" in data

    def test_search_hosts_returns_host_data(self, client: TestClient) -> None:
        """Test that search hosts returns correct host profile data."""
        mock_profile = create_mock_host_profile(
            headline="Great Dancer",
            hourly_rate_cents=7500,
            rating_average=4.8,
            total_reviews=25,
        )

        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search.return_value = ([mock_profile], 1)

            response = client.get("/api/v1/hosts")
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert len(data["items"]) == 1
            host = data["items"][0]
            assert host["headline"] == "Great Dancer"
            assert host["hourly_rate_cents"] == 7500
            assert host["rating_average"] == 4.8
            assert host["total_reviews"] == 25
            assert host["first_name"] == "Test"
            assert host["last_name"] == "Host"

    def test_search_hosts_with_lat_lng_params(self, client: TestClient) -> None:
        """Test that search hosts accepts lat and lng query parameters."""
        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search.return_value = ([], 0)

            response = client.get("/api/v1/hosts?lat=40.7&lng=-74.0")
            assert response.status_code == status.HTTP_200_OK

            # Verify search was called with location params
            mock_host_repo.search.assert_called_once()
            call_kwargs = mock_host_repo.search.call_args.kwargs
            assert call_kwargs["latitude"] == 40.7
            assert call_kwargs["longitude"] == -74.0

    def test_search_hosts_with_radius_km_param(self, client: TestClient) -> None:
        """Test that search hosts accepts radius_km query parameter."""
        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search.return_value = ([], 0)

            response = client.get("/api/v1/hosts?lat=40.7&lng=-74.0&radius_km=25")
            assert response.status_code == status.HTTP_200_OK

            # Verify search was called with radius
            mock_host_repo.search.assert_called_once()
            call_kwargs = mock_host_repo.search.call_args.kwargs
            assert call_kwargs["radius_km"] == 25.0

    def test_search_hosts_with_styles_filter(self, client: TestClient) -> None:
        """Test that search hosts accepts styles[] query parameter."""
        style_id_1 = "770e8400-e29b-41d4-a716-446655440001"
        style_id_2 = "770e8400-e29b-41d4-a716-446655440002"

        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search.return_value = ([], 0)

            response = client.get(
                f"/api/v1/hosts?styles={style_id_1}&styles={style_id_2}"
            )
            assert response.status_code == status.HTTP_200_OK

            # Verify search was called with style_ids
            mock_host_repo.search.assert_called_once()
            call_kwargs = mock_host_repo.search.call_args.kwargs
            assert call_kwargs["style_ids"] is not None
            assert len(call_kwargs["style_ids"]) == 2

    def test_search_hosts_with_min_rating_filter(self, client: TestClient) -> None:
        """Test that search hosts accepts min_rating query parameter."""
        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search.return_value = ([], 0)

            response = client.get("/api/v1/hosts?min_rating=4.0")
            assert response.status_code == status.HTTP_200_OK

            # Verify search was called with min_rating
            mock_host_repo.search.assert_called_once()
            call_kwargs = mock_host_repo.search.call_args.kwargs
            assert call_kwargs["min_rating"] == 4.0

    def test_search_hosts_with_max_price_filter(self, client: TestClient) -> None:
        """Test that search hosts accepts max_price query parameter."""
        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search.return_value = ([], 0)

            response = client.get("/api/v1/hosts?max_price=10000")
            assert response.status_code == status.HTTP_200_OK

            # Verify search was called with max_price_cents
            mock_host_repo.search.assert_called_once()
            call_kwargs = mock_host_repo.search.call_args.kwargs
            assert call_kwargs["max_price_cents"] == 10000

    def test_search_hosts_pagination(self, client: TestClient) -> None:
        """Test that search hosts supports pagination parameters."""
        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search.return_value = ([], 0)

            response = client.get("/api/v1/hosts?page=2&page_size=10")
            assert response.status_code == status.HTTP_200_OK

            # Verify search was called with pagination
            mock_host_repo.search.assert_called_once()
            call_kwargs = mock_host_repo.search.call_args.kwargs
            assert call_kwargs["limit"] == 10
            assert call_kwargs["offset"] == 10  # page 2 with page_size 10

    def test_search_hosts_calculates_total_pages(self, client: TestClient) -> None:
        """Test that search hosts calculates total_pages correctly."""
        mock_profiles = [
            create_mock_host_profile(
                profile_id=f"660e8400-e29b-41d4-a716-44665544000{i}",
                user_id=f"550e8400-e29b-41d4-a716-44665544000{i}",
                user=create_mock_user(f"550e8400-e29b-41d4-a716-44665544000{i}"),
            )
            for i in range(5)
        ]

        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            # Return 5 profiles with total of 45 (to test pagination)
            mock_host_repo.search.return_value = (mock_profiles, 45)

            response = client.get("/api/v1/hosts?page_size=10")
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["total"] == 45
            assert data["page_size"] == 10
            assert data["total_pages"] == 5  # ceil(45/10) = 5

    def test_search_hosts_sort_by_distance(self, client: TestClient) -> None:
        """Test that search hosts can sort by distance."""
        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search.return_value = ([], 0)

            response = client.get("/api/v1/hosts?sort_by=distance")
            assert response.status_code == status.HTTP_200_OK

            # Verify search was called with order_by=distance
            mock_host_repo.search.assert_called_once()
            call_kwargs = mock_host_repo.search.call_args.kwargs
            assert call_kwargs["order_by"] == "distance"

    def test_search_hosts_sort_by_rating(self, client: TestClient) -> None:
        """Test that search hosts can sort by rating."""
        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search.return_value = ([], 0)

            response = client.get("/api/v1/hosts?sort_by=rating")
            assert response.status_code == status.HTTP_200_OK

            # Verify search was called with order_by=rating
            mock_host_repo.search.assert_called_once()
            call_kwargs = mock_host_repo.search.call_args.kwargs
            assert call_kwargs["order_by"] == "rating"

    def test_search_hosts_sort_by_price(self, client: TestClient) -> None:
        """Test that search hosts can sort by price."""
        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search.return_value = ([], 0)

            response = client.get("/api/v1/hosts?sort_by=price")
            assert response.status_code == status.HTTP_200_OK

            # Verify search was called with order_by=price
            mock_host_repo.search.assert_called_once()
            call_kwargs = mock_host_repo.search.call_args.kwargs
            assert call_kwargs["order_by"] == "price"

    def test_search_hosts_empty_results(self, client: TestClient) -> None:
        """Test that search hosts handles empty results correctly."""
        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search.return_value = ([], 0)

            response = client.get("/api/v1/hosts")
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["items"] == []
            assert data["total"] == 0
            assert data["total_pages"] == 1  # At least 1 page

    def test_search_hosts_validates_lat_range(self, client: TestClient) -> None:
        """Test that search hosts validates latitude range."""
        response = client.get("/api/v1/hosts?lat=91.0&lng=-74.0")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        response = client.get("/api/v1/hosts?lat=-91.0&lng=-74.0")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_search_hosts_validates_lng_range(self, client: TestClient) -> None:
        """Test that search hosts validates longitude range."""
        response = client.get("/api/v1/hosts?lat=40.7&lng=181.0")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        response = client.get("/api/v1/hosts?lat=40.7&lng=-181.0")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_search_hosts_validates_radius_range(self, client: TestClient) -> None:
        """Test that search hosts validates radius_km range."""
        response = client.get("/api/v1/hosts?radius_km=0.5")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        response = client.get("/api/v1/hosts?radius_km=501")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_search_hosts_validates_min_rating_range(self, client: TestClient) -> None:
        """Test that search hosts validates min_rating range."""
        response = client.get("/api/v1/hosts?min_rating=0.5")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        response = client.get("/api/v1/hosts?min_rating=5.5")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_search_hosts_validates_page_range(self, client: TestClient) -> None:
        """Test that search hosts validates page range."""
        response = client.get("/api/v1/hosts?page=0")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_search_hosts_validates_page_size_range(self, client: TestClient) -> None:
        """Test that search hosts validates page_size range."""
        response = client.get("/api/v1/hosts?page_size=0")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        response = client.get("/api/v1/hosts?page_size=101")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_search_hosts_default_values(self, client: TestClient) -> None:
        """Test that search hosts uses correct default values."""
        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search.return_value = ([], 0)

            response = client.get("/api/v1/hosts")
            assert response.status_code == status.HTTP_200_OK

            # Verify default values were used
            mock_host_repo.search.assert_called_once()
            call_kwargs = mock_host_repo.search.call_args.kwargs
            assert call_kwargs["latitude"] is None
            assert call_kwargs["longitude"] is None
            assert call_kwargs["radius_km"] is None  # Only set when lat/lng provided
            assert call_kwargs["style_ids"] is None
            assert call_kwargs["min_rating"] is None
            assert call_kwargs["max_price_cents"] is None
            assert call_kwargs["limit"] == 20  # default page_size
            assert call_kwargs["offset"] == 0  # page 1

    def test_search_hosts_multiple_profiles(self, client: TestClient) -> None:
        """Test that search hosts returns multiple profiles correctly."""
        mock_profiles = [
            create_mock_host_profile(
                profile_id="660e8400-e29b-41d4-a716-446655440001",
                user_id="550e8400-e29b-41d4-a716-446655440001",
                headline="Salsa Expert",
                user=create_mock_user(
                    "550e8400-e29b-41d4-a716-446655440001",
                    first_name="Alice",
                    last_name="Dancer",
                ),
            ),
            create_mock_host_profile(
                profile_id="660e8400-e29b-41d4-a716-446655440002",
                user_id="550e8400-e29b-41d4-a716-446655440002",
                headline="Bachata Pro",
                user=create_mock_user(
                    "550e8400-e29b-41d4-a716-446655440002",
                    first_name="Bob",
                    last_name="Teacher",
                ),
            ),
        ]

        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search.return_value = (mock_profiles, 2)

            response = client.get("/api/v1/hosts")
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert len(data["items"]) == 2
            assert data["items"][0]["first_name"] == "Alice"
            assert data["items"][0]["headline"] == "Salsa Expert"
            assert data["items"][1]["first_name"] == "Bob"
            assert data["items"][1]["headline"] == "Bachata Pro"


class TestGetHostProfileEndpoint:
    """Tests for GET /api/v1/hosts/{id} endpoint."""

    def test_get_host_profile_endpoint_exists(self, client: TestClient) -> None:
        """Test that the get host profile endpoint exists and accepts GET."""
        host_id = "660e8400-e29b-41d4-a716-446655440001"
        mock_profile = create_mock_host_profile(profile_id=host_id)
        # Add extra required fields
        mock_profile.bio = "Test bio"
        mock_profile.total_sessions = 0
        mock_profile.stripe_onboarding_complete = False
        mock_profile.created_at = "2026-01-01T00:00:00Z"
        mock_profile.updated_at = "2026-01-28T00:00:00Z"

        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_id.return_value = mock_profile
            mock_host_repo.get_dance_styles.return_value = []

            response = client.get(f"/api/v1/hosts/{host_id}")
            assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_get_host_profile_returns_200_on_success(self, client: TestClient) -> None:
        """Test that get host profile returns 200 with valid host ID."""
        host_id = "660e8400-e29b-41d4-a716-446655440001"
        mock_profile = create_mock_host_profile(profile_id=host_id)
        # Add extra required fields
        mock_profile.bio = "Test bio"
        mock_profile.total_sessions = 0
        mock_profile.stripe_onboarding_complete = False
        mock_profile.created_at = "2026-01-01T00:00:00Z"
        mock_profile.updated_at = "2026-01-28T00:00:00Z"

        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_id.return_value = mock_profile
            mock_host_repo.get_dance_styles.return_value = []

            response = client.get(f"/api/v1/hosts/{host_id}")
            assert response.status_code == status.HTTP_200_OK

    def test_get_host_profile_returns_full_profile(self, client: TestClient) -> None:
        """Test that get host profile returns full profile data."""
        host_id = "660e8400-e29b-41d4-a716-446655440001"
        mock_user = create_mock_user(first_name="John", last_name="Dancer")
        mock_profile = create_mock_host_profile(
            profile_id=host_id,
            headline="Expert Tango Instructor",
            hourly_rate_cents=7500,
            rating_average=4.9,
            total_reviews=50,
            verification_status=VerificationStatus.VERIFIED,
            user=mock_user,
        )
        # Add extra fields that the response needs
        mock_profile.bio = "10 years of dance experience"
        mock_profile.total_sessions = 200
        mock_profile.stripe_onboarding_complete = True
        mock_profile.created_at = "2026-01-01T00:00:00Z"
        mock_profile.updated_at = "2026-01-28T00:00:00Z"

        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_id.return_value = mock_profile
            mock_host_repo.get_dance_styles.return_value = []

            response = client.get(f"/api/v1/hosts/{host_id}")
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["id"] == host_id
            assert data["headline"] == "Expert Tango Instructor"
            assert data["hourly_rate_cents"] == 7500
            assert data["rating_average"] == 4.9
            assert data["total_reviews"] == 50
            assert data["first_name"] == "John"
            assert data["last_name"] == "Dancer"

    def test_get_host_profile_includes_dance_styles(self, client: TestClient) -> None:
        """Test that get host profile includes dance styles."""
        host_id = "660e8400-e29b-41d4-a716-446655440001"
        mock_profile = create_mock_host_profile(profile_id=host_id)
        mock_profile.bio = "Dance expert"
        mock_profile.total_sessions = 100
        mock_profile.stripe_onboarding_complete = True
        mock_profile.created_at = "2026-01-01T00:00:00Z"
        mock_profile.updated_at = "2026-01-28T00:00:00Z"

        # Create mock dance style
        mock_dance_style = MagicMock()
        mock_dance_style.id = "770e8400-e29b-41d4-a716-446655440001"
        mock_dance_style.name = "Salsa"
        mock_dance_style.slug = "salsa"
        mock_dance_style.category = DanceStyleCategory.LATIN  # Use proper enum
        mock_dance_style.description = "Popular Latin dance"

        mock_host_dance_style = MagicMock()
        mock_host_dance_style.dance_style_id = "770e8400-e29b-41d4-a716-446655440001"
        mock_host_dance_style.skill_level = 5
        mock_host_dance_style.dance_style = mock_dance_style

        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_id.return_value = mock_profile
            mock_host_repo.get_dance_styles.return_value = [mock_host_dance_style]

            response = client.get(f"/api/v1/hosts/{host_id}")
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert "dance_styles" in data
            assert len(data["dance_styles"]) == 1
            assert data["dance_styles"][0]["skill_level"] == 5
            assert data["dance_styles"][0]["dance_style"]["name"] == "Salsa"

    def test_get_host_profile_excludes_password_hash(self, client: TestClient) -> None:
        """Test that get host profile never exposes password_hash."""
        host_id = "660e8400-e29b-41d4-a716-446655440001"
        mock_user = create_mock_user()
        mock_user.password_hash = "super_secret_hash"
        mock_profile = create_mock_host_profile(profile_id=host_id, user=mock_user)
        mock_profile.bio = "Test bio"
        mock_profile.total_sessions = 0
        mock_profile.stripe_onboarding_complete = False
        mock_profile.created_at = "2026-01-01T00:00:00Z"
        mock_profile.updated_at = "2026-01-28T00:00:00Z"

        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_id.return_value = mock_profile
            mock_host_repo.get_dance_styles.return_value = []

            response = client.get(f"/api/v1/hosts/{host_id}")
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert "password_hash" not in data
            assert "password" not in data
            # Make sure user-related sensitive data isn't exposed
            response_str = response.text
            assert "super_secret_hash" not in response_str

    def test_get_host_profile_returns_404_for_nonexistent(
        self, client: TestClient
    ) -> None:
        """Test that get host profile returns 404 for non-existent host."""
        host_id = "660e8400-e29b-41d4-a716-446655440099"

        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_id.return_value = None

            response = client.get(f"/api/v1/hosts/{host_id}")
            assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_host_profile_returns_404_message(self, client: TestClient) -> None:
        """Test that get host profile returns appropriate error message for 404."""
        host_id = "660e8400-e29b-41d4-a716-446655440099"

        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_id.return_value = None

            response = client.get(f"/api/v1/hosts/{host_id}")
            assert response.status_code == status.HTTP_404_NOT_FOUND

            data = response.json()
            assert "detail" in data

    def test_get_host_profile_validates_uuid_format(self, client: TestClient) -> None:
        """Test that get host profile validates UUID format."""
        invalid_host_id = "not-a-valid-uuid"

        response = client.get(f"/api/v1/hosts/{invalid_host_id}")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_host_profile_returns_verification_status(
        self, client: TestClient
    ) -> None:
        """Test that get host profile returns verification status."""
        host_id = "660e8400-e29b-41d4-a716-446655440001"
        mock_profile = create_mock_host_profile(
            profile_id=host_id,
            verification_status=VerificationStatus.VERIFIED,
        )
        mock_profile.bio = "Bio"
        mock_profile.total_sessions = 10
        mock_profile.stripe_onboarding_complete = True
        mock_profile.created_at = "2026-01-01T00:00:00Z"
        mock_profile.updated_at = "2026-01-28T00:00:00Z"

        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_id.return_value = mock_profile
            mock_host_repo.get_dance_styles.return_value = []

            response = client.get(f"/api/v1/hosts/{host_id}")
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["verification_status"] == "verified"


class TestSearchHostsEdgeCases:
    """Additional edge case tests for search hosts endpoint."""

    def test_search_hosts_invalid_sort_by_defaults_to_distance(
        self, client: TestClient
    ) -> None:
        """Test that invalid sort_by value defaults to 'distance'."""
        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search.return_value = ([], 0)

            response = client.get("/api/v1/hosts?sort_by=invalid_field")
            assert response.status_code == status.HTTP_200_OK

            mock_host_repo.search.assert_called_once()
            call_kwargs = mock_host_repo.search.call_args.kwargs
            assert call_kwargs["order_by"] == "distance"

    def test_search_hosts_invalid_sort_order_defaults_to_asc(
        self, client: TestClient
    ) -> None:
        """Test that invalid sort_order value defaults to 'asc'."""
        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search.return_value = ([], 0)

            response = client.get("/api/v1/hosts?sort_order=invalid")
            assert response.status_code == status.HTTP_200_OK

    def test_search_hosts_sort_by_reviews_uses_rating(self, client: TestClient) -> None:
        """Test that sort_by=reviews maps to order_by=rating."""
        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search.return_value = ([], 0)

            response = client.get("/api/v1/hosts?sort_by=reviews")
            assert response.status_code == status.HTTP_200_OK

            mock_host_repo.search.assert_called_once()
            call_kwargs = mock_host_repo.search.call_args.kwargs
            assert call_kwargs["order_by"] == "rating"

    def test_search_hosts_verified_only_filters_profiles(
        self, client: TestClient
    ) -> None:
        """Test that verified_only=true filters out unverified hosts."""
        verified_profile = create_mock_host_profile(
            profile_id="660e8400-e29b-41d4-a716-446655440001",
            user_id="550e8400-e29b-41d4-a716-446655440001",
            verification_status=VerificationStatus.VERIFIED,
            user=create_mock_user("550e8400-e29b-41d4-a716-446655440001"),
        )
        unverified_profile = create_mock_host_profile(
            profile_id="660e8400-e29b-41d4-a716-446655440002",
            user_id="550e8400-e29b-41d4-a716-446655440002",
            verification_status=VerificationStatus.UNVERIFIED,  # Changed from NOT_SUBMITTED
            user=create_mock_user("550e8400-e29b-41d4-a716-446655440002"),
        )

        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search.return_value = (
                [verified_profile, unverified_profile],
                2,
            )

            response = client.get("/api/v1/hosts?verified_only=true")
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            # Only the verified profile should be returned
            assert len(data["items"]) == 1
            assert data["items"][0]["verification_status"] == "verified"

    def test_search_hosts_sort_order_desc_rating(self, client: TestClient) -> None:
        """Test that sort_order=desc reverses rating sort."""
        profile1 = create_mock_host_profile(
            profile_id="660e8400-e29b-41d4-a716-446655440001",
            user_id="550e8400-e29b-41d4-a716-446655440001",
            rating_average=3.0,
            user=create_mock_user("550e8400-e29b-41d4-a716-446655440001"),
        )
        profile2 = create_mock_host_profile(
            profile_id="660e8400-e29b-41d4-a716-446655440002",
            user_id="550e8400-e29b-41d4-a716-446655440002",
            rating_average=5.0,
            user=create_mock_user("550e8400-e29b-41d4-a716-446655440002"),
        )

        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search.return_value = ([profile1, profile2], 2)

            response = client.get("/api/v1/hosts?sort_by=rating&sort_order=desc")
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            # Should be sorted with highest rating first
            assert len(data["items"]) == 2
            assert data["items"][0]["rating_average"] == 5.0
            assert data["items"][1]["rating_average"] == 3.0

    def test_search_hosts_sort_order_desc_price(self, client: TestClient) -> None:
        """Test that sort_order=desc reverses price sort."""
        profile1 = create_mock_host_profile(
            profile_id="660e8400-e29b-41d4-a716-446655440001",
            user_id="550e8400-e29b-41d4-a716-446655440001",
            hourly_rate_cents=3000,
            user=create_mock_user("550e8400-e29b-41d4-a716-446655440001"),
        )
        profile2 = create_mock_host_profile(
            profile_id="660e8400-e29b-41d4-a716-446655440002",
            user_id="550e8400-e29b-41d4-a716-446655440002",
            hourly_rate_cents=8000,
            user=create_mock_user("550e8400-e29b-41d4-a716-446655440002"),
        )

        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search.return_value = ([profile1, profile2], 2)

            response = client.get("/api/v1/hosts?sort_by=price&sort_order=desc")
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            # Should be sorted with highest price first
            assert len(data["items"]) == 2
            assert data["items"][0]["hourly_rate_cents"] == 8000
            assert data["items"][1]["hourly_rate_cents"] == 3000

    def test_search_hosts_sort_order_desc_distance(self, client: TestClient) -> None:
        """Test that sort_order=desc reverses distance sort when lat/lng provided."""
        profile1 = create_mock_host_profile(
            profile_id="660e8400-e29b-41d4-a716-446655440001",
            user_id="550e8400-e29b-41d4-a716-446655440001",
            location=MagicMock(),
            user=create_mock_user("550e8400-e29b-41d4-a716-446655440001"),
        )
        profile2 = create_mock_host_profile(
            profile_id="660e8400-e29b-41d4-a716-446655440002",
            user_id="550e8400-e29b-41d4-a716-446655440002",
            location=MagicMock(),
            user=create_mock_user("550e8400-e29b-41d4-a716-446655440002"),
        )

        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search.return_value = ([profile1, profile2], 2)

            response = client.get(
                "/api/v1/hosts?lat=40.7&lng=-74.0&sort_by=distance&sort_order=desc"
            )
            assert response.status_code == status.HTTP_200_OK

    def test_search_hosts_no_location_has_null_distance(
        self, client: TestClient
    ) -> None:
        """Test that hosts without location have null distance_km."""
        profile = create_mock_host_profile(location=None)

        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search.return_value = ([profile], 1)

            response = client.get("/api/v1/hosts?lat=40.7&lng=-74.0")
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["items"][0]["distance_km"] is None


class TestGetHostAvailabilityEndpoint:
    """Tests for GET /api/v1/hosts/{host_id}/availability endpoint."""

    def test_get_availability_endpoint_exists(self, client: TestClient) -> None:
        """Test that the availability endpoint exists."""
        host_id = "660e8400-e29b-41d4-a716-446655440001"
        mock_profile = MagicMock()
        mock_profile.id = host_id

        with (
            patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class,
            patch("app.routers.hosts.AvailabilityRepository") as mock_avail_repo_class,
        ):
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_id.return_value = mock_profile

            mock_avail_repo = AsyncMock()
            mock_avail_repo_class.return_value = mock_avail_repo
            mock_avail_repo.get_bookings_for_date_range.return_value = []
            mock_avail_repo.get_availability_for_date.return_value = []

            response = client.get(f"/api/v1/hosts/{host_id}/availability")
            assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_get_availability_returns_200_for_valid_host(
        self, client: TestClient
    ) -> None:
        """Test that availability returns 200 for a valid host."""
        host_id = "660e8400-e29b-41d4-a716-446655440001"
        mock_profile = MagicMock()
        mock_profile.id = host_id

        with (
            patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class,
            patch("app.routers.hosts.AvailabilityRepository") as mock_avail_repo_class,
        ):
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_id.return_value = mock_profile

            mock_avail_repo = AsyncMock()
            mock_avail_repo_class.return_value = mock_avail_repo
            mock_avail_repo.get_bookings_for_date_range.return_value = []
            mock_avail_repo.get_availability_for_date.return_value = []

            response = client.get(f"/api/v1/hosts/{host_id}/availability")
            assert response.status_code == status.HTTP_200_OK

    def test_get_availability_returns_404_for_nonexistent_host(
        self, client: TestClient
    ) -> None:
        """Test that availability returns 404 for non-existent host."""
        host_id = "660e8400-e29b-41d4-a716-446655440099"

        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_id.return_value = None

            response = client.get(f"/api/v1/hosts/{host_id}/availability")
            assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_availability_returns_date_range_response(
        self, client: TestClient
    ) -> None:
        """Test that availability returns proper date range structure."""
        from datetime import time

        host_id = "660e8400-e29b-41d4-a716-446655440001"
        mock_profile = MagicMock()
        mock_profile.id = host_id

        with (
            patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class,
            patch("app.routers.hosts.AvailabilityRepository") as mock_avail_repo_class,
        ):
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_id.return_value = mock_profile

            mock_avail_repo = AsyncMock()
            mock_avail_repo_class.return_value = mock_avail_repo
            mock_avail_repo.get_bookings_for_date_range.return_value = []
            # Return some availability slots
            mock_avail_repo.get_availability_for_date.return_value = [
                (time(9, 0), time(12, 0)),
                (time(14, 0), time(17, 0)),
            ]

            response = client.get(f"/api/v1/hosts/{host_id}/availability")
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert "host_profile_id" in data
            assert "start_date" in data
            assert "end_date" in data
            assert "availability" in data
            assert isinstance(data["availability"], list)

    def test_get_availability_with_custom_date_range(self, client: TestClient) -> None:
        """Test that availability accepts custom start_date and end_date."""
        host_id = "660e8400-e29b-41d4-a716-446655440001"
        mock_profile = MagicMock()
        mock_profile.id = host_id

        with (
            patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class,
            patch("app.routers.hosts.AvailabilityRepository") as mock_avail_repo_class,
        ):
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_id.return_value = mock_profile

            mock_avail_repo = AsyncMock()
            mock_avail_repo_class.return_value = mock_avail_repo
            mock_avail_repo.get_bookings_for_date_range.return_value = []
            mock_avail_repo.get_availability_for_date.return_value = []

            response = client.get(
                f"/api/v1/hosts/{host_id}/availability?start_date=2026-02-01&end_date=2026-02-07"
            )
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["start_date"] == "2026-02-01"
            assert data["end_date"] == "2026-02-07"

    def test_get_availability_excludes_booked_slots(self, client: TestClient) -> None:
        """Test that availability excludes already booked time slots."""
        from datetime import datetime, time

        host_id = "660e8400-e29b-41d4-a716-446655440001"
        mock_profile = MagicMock()
        mock_profile.id = host_id

        # Create a mock booking
        mock_booking = MagicMock()
        mock_booking.scheduled_start = datetime(2026, 2, 1, 10, 0)
        mock_booking.scheduled_end = datetime(2026, 2, 1, 11, 0)

        with (
            patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class,
            patch("app.routers.hosts.AvailabilityRepository") as mock_avail_repo_class,
        ):
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_id.return_value = mock_profile

            mock_avail_repo = MagicMock()  # Use MagicMock for sync methods
            mock_avail_repo.get_bookings_for_date_range = AsyncMock(
                return_value=[mock_booking]
            )
            mock_avail_repo.get_availability_for_date = AsyncMock(
                return_value=[(time(9, 0), time(12, 0))]
            )
            # _subtract_time_range is a sync method, so use regular return_value
            mock_avail_repo._subtract_time_range = MagicMock(
                return_value=[(time(9, 0), time(10, 0)), (time(11, 0), time(12, 0))]
            )
            mock_avail_repo_class.return_value = mock_avail_repo

            response = client.get(
                f"/api/v1/hosts/{host_id}/availability?start_date=2026-02-01&end_date=2026-02-01"
            )
            assert response.status_code == status.HTTP_200_OK

    def test_get_availability_end_date_before_start_date_corrected(
        self, client: TestClient
    ) -> None:
        """Test that end_date before start_date is corrected to equal start_date."""
        host_id = "660e8400-e29b-41d4-a716-446655440001"
        mock_profile = MagicMock()
        mock_profile.id = host_id

        with (
            patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class,
            patch("app.routers.hosts.AvailabilityRepository") as mock_avail_repo_class,
        ):
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_id.return_value = mock_profile

            mock_avail_repo = AsyncMock()
            mock_avail_repo_class.return_value = mock_avail_repo
            mock_avail_repo.get_bookings_for_date_range.return_value = []
            mock_avail_repo.get_availability_for_date.return_value = []

            # end_date before start_date
            response = client.get(
                f"/api/v1/hosts/{host_id}/availability?start_date=2026-02-10&end_date=2026-02-05"
            )
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            # end_date should be corrected to match start_date
            assert data["start_date"] == "2026-02-10"
            assert data["end_date"] == "2026-02-10"


class TestGetHostReviewsEndpoint:
    """Tests for GET /api/v1/hosts/{host_id}/reviews endpoint."""

    def test_get_reviews_endpoint_exists(self, client: TestClient) -> None:
        """Test that the reviews endpoint exists."""
        host_id = "660e8400-e29b-41d4-a716-446655440001"
        mock_profile = MagicMock()
        mock_profile.id = host_id

        with (
            patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class,
            patch("app.routers.hosts.ReviewRepository") as mock_review_repo_class,
        ):
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_id.return_value = mock_profile

            mock_review_repo = AsyncMock()
            mock_review_repo_class.return_value = mock_review_repo
            mock_review_repo.get_for_host_profile.return_value = []
            mock_review_repo.count_for_host_profile.return_value = 0

            response = client.get(f"/api/v1/hosts/{host_id}/reviews")
            assert response.status_code != status.HTTP_405_METHOD_NOT_ALLOWED

    def test_get_reviews_returns_200_for_valid_host(self, client: TestClient) -> None:
        """Test that reviews returns 200 for a valid host."""
        host_id = "660e8400-e29b-41d4-a716-446655440001"
        mock_profile = MagicMock()
        mock_profile.id = host_id

        with (
            patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class,
            patch("app.routers.hosts.ReviewRepository") as mock_review_repo_class,
        ):
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_id.return_value = mock_profile

            mock_review_repo = AsyncMock()
            mock_review_repo_class.return_value = mock_review_repo
            mock_review_repo.get_for_host_profile.return_value = []
            mock_review_repo.count_for_host_profile.return_value = 0

            response = client.get(f"/api/v1/hosts/{host_id}/reviews")
            assert response.status_code == status.HTTP_200_OK

    def test_get_reviews_returns_404_for_nonexistent_host(
        self, client: TestClient
    ) -> None:
        """Test that reviews returns 404 for non-existent host."""
        host_id = "660e8400-e29b-41d4-a716-446655440099"

        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_id.return_value = None

            response = client.get(f"/api/v1/hosts/{host_id}/reviews")
            assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_reviews_returns_paginated_response(self, client: TestClient) -> None:
        """Test that reviews returns a paginated response."""
        from datetime import datetime

        host_id = "660e8400-e29b-41d4-a716-446655440001"
        mock_profile = MagicMock()
        mock_profile.id = host_id

        # Create mock review with reviewer
        mock_reviewer = MagicMock()
        mock_reviewer.id = "770e8400-e29b-41d4-a716-446655440001"
        mock_reviewer.first_name = "Alice"
        mock_reviewer.last_name = "Reviewer"

        mock_reviewee = MagicMock()
        mock_reviewee.id = "770e8400-e29b-41d4-a716-446655440002"
        mock_reviewee.first_name = "Bob"
        mock_reviewee.last_name = "Host"

        mock_review = MagicMock()
        mock_review.id = "880e8400-e29b-41d4-a716-446655440001"
        mock_review.booking_id = "990e8400-e29b-41d4-a716-446655440001"
        mock_review.reviewer_id = mock_reviewer.id
        mock_review.reviewee_id = mock_reviewee.id
        mock_review.rating = 5
        mock_review.comment = "Great experience!"
        mock_review.host_response = None
        mock_review.host_responded_at = None
        mock_review.created_at = datetime(2026, 1, 15)
        mock_review.updated_at = datetime(2026, 1, 15)
        mock_review.reviewer = mock_reviewer
        mock_review.reviewee = mock_reviewee

        with (
            patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class,
            patch("app.routers.hosts.ReviewRepository") as mock_review_repo_class,
        ):
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_id.return_value = mock_profile

            mock_review_repo = AsyncMock()
            mock_review_repo_class.return_value = mock_review_repo
            mock_review_repo.get_for_host_profile.return_value = [mock_review]
            mock_review_repo.count_for_host_profile.return_value = 1

            response = client.get(f"/api/v1/hosts/{host_id}/reviews")
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert "items" in data
            assert "next_cursor" in data
            assert "has_more" in data
            assert "total" in data
            assert len(data["items"]) == 1
            assert data["items"][0]["rating"] == 5

    def test_get_reviews_with_cursor_pagination(self, client: TestClient) -> None:
        """Test that reviews supports cursor-based pagination."""
        host_id = "660e8400-e29b-41d4-a716-446655440001"
        cursor = "880e8400-e29b-41d4-a716-446655440001"
        mock_profile = MagicMock()
        mock_profile.id = host_id

        with (
            patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class,
            patch("app.routers.hosts.ReviewRepository") as mock_review_repo_class,
        ):
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_id.return_value = mock_profile

            mock_review_repo = AsyncMock()
            mock_review_repo_class.return_value = mock_review_repo
            mock_review_repo.get_for_host_profile.return_value = []
            mock_review_repo.count_for_host_profile.return_value = 0

            response = client.get(f"/api/v1/hosts/{host_id}/reviews?cursor={cursor}")
            assert response.status_code == status.HTTP_200_OK

            # Verify cursor was passed to repository
            mock_review_repo.get_for_host_profile.assert_called_once()

    def test_get_reviews_invalid_cursor_returns_400(self, client: TestClient) -> None:
        """Test that an invalid cursor format returns 400."""
        host_id = "660e8400-e29b-41d4-a716-446655440001"
        mock_profile = MagicMock()
        mock_profile.id = host_id

        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_id.return_value = mock_profile

            response = client.get(
                f"/api/v1/hosts/{host_id}/reviews?cursor=not-a-valid-uuid"
            )
            assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_reviews_with_custom_limit(self, client: TestClient) -> None:
        """Test that reviews accepts custom limit parameter."""
        host_id = "660e8400-e29b-41d4-a716-446655440001"
        mock_profile = MagicMock()
        mock_profile.id = host_id

        with (
            patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class,
            patch("app.routers.hosts.ReviewRepository") as mock_review_repo_class,
        ):
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_id.return_value = mock_profile

            mock_review_repo = AsyncMock()
            mock_review_repo_class.return_value = mock_review_repo
            mock_review_repo.get_for_host_profile.return_value = []
            mock_review_repo.count_for_host_profile.return_value = 0

            response = client.get(f"/api/v1/hosts/{host_id}/reviews?limit=5")
            assert response.status_code == status.HTTP_200_OK

            # Verify limit + 1 was passed for checking has_more
            mock_review_repo.get_for_host_profile.assert_called_once()
            call_kwargs = mock_review_repo.get_for_host_profile.call_args.kwargs
            assert call_kwargs["limit"] == 6  # limit + 1

    def test_get_reviews_has_more_flag(self, client: TestClient) -> None:
        """Test that has_more is true when there are more reviews."""
        from datetime import datetime

        host_id = "660e8400-e29b-41d4-a716-446655440001"
        mock_profile = MagicMock()
        mock_profile.id = host_id

        # Create mock reviews (more than limit)
        def create_mock_review(idx: int):
            mock_reviewer = MagicMock()
            mock_reviewer.id = f"770e8400-e29b-41d4-a716-44665544000{idx}"
            mock_reviewer.first_name = f"User{idx}"
            mock_reviewer.last_name = "Test"

            mock_reviewee = MagicMock()
            mock_reviewee.id = "770e8400-e29b-41d4-a716-446655440002"
            mock_reviewee.first_name = "Host"
            mock_reviewee.last_name = "Test"

            mock_review = MagicMock()
            mock_review.id = f"880e8400-e29b-41d4-a716-44665544000{idx}"
            mock_review.booking_id = f"990e8400-e29b-41d4-a716-44665544000{idx}"
            mock_review.reviewer_id = mock_reviewer.id
            mock_review.reviewee_id = mock_reviewee.id
            mock_review.rating = 4
            mock_review.comment = f"Review {idx}"
            mock_review.host_response = None
            mock_review.host_responded_at = None
            mock_review.created_at = datetime(2026, 1, idx)
            mock_review.updated_at = datetime(2026, 1, idx)
            mock_review.reviewer = mock_reviewer
            mock_review.reviewee = mock_reviewee
            return mock_review

        mock_reviews = [create_mock_review(i) for i in range(1, 4)]  # 3 reviews

        with (
            patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class,
            patch("app.routers.hosts.ReviewRepository") as mock_review_repo_class,
        ):
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_id.return_value = mock_profile

            mock_review_repo = AsyncMock()
            mock_review_repo_class.return_value = mock_review_repo
            mock_review_repo.get_for_host_profile.return_value = mock_reviews
            mock_review_repo.count_for_host_profile.return_value = 3

            response = client.get(f"/api/v1/hosts/{host_id}/reviews?limit=2")
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["has_more"] is True
            assert len(data["items"]) == 2  # Only 2, not 3
            assert data["next_cursor"] is not None

    def test_get_reviews_without_reviewer(self, client: TestClient) -> None:
        """Test that reviews handles cases where reviewer is None."""
        from datetime import datetime

        host_id = "660e8400-e29b-41d4-a716-446655440001"
        mock_profile = MagicMock()
        mock_profile.id = host_id

        mock_review = MagicMock()
        mock_review.id = "880e8400-e29b-41d4-a716-446655440001"
        mock_review.booking_id = "990e8400-e29b-41d4-a716-446655440001"
        mock_review.reviewer_id = "770e8400-e29b-41d4-a716-446655440001"
        mock_review.reviewee_id = "770e8400-e29b-41d4-a716-446655440002"
        mock_review.rating = 5
        mock_review.comment = "Great!"
        mock_review.host_response = "Thanks!"
        mock_review.host_responded_at = datetime(2026, 1, 16)
        mock_review.created_at = datetime(2026, 1, 15)
        mock_review.updated_at = datetime(2026, 1, 15)
        mock_review.reviewer = None  # Deleted user
        mock_review.reviewee = None  # Deleted user

        with (
            patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class,
            patch("app.routers.hosts.ReviewRepository") as mock_review_repo_class,
        ):
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_id.return_value = mock_profile

            mock_review_repo = AsyncMock()
            mock_review_repo_class.return_value = mock_review_repo
            mock_review_repo.get_for_host_profile.return_value = [mock_review]
            mock_review_repo.count_for_host_profile.return_value = 1

            response = client.get(f"/api/v1/hosts/{host_id}/reviews")
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["items"][0]["reviewer"] is None
            assert data["items"][0]["reviewee"] is None


class TestStripeOnboardingEndpoint:
    """Tests for POST /api/v1/hosts/stripe/onboard endpoint."""

    @pytest.fixture
    def auth_app(self, app):
        """Create app with authentication mocked."""
        from app.core.deps import get_current_user

        mock_user = MagicMock()
        mock_user.id = "550e8400-e29b-41d4-a716-446655440000"
        mock_user.email = "host@example.com"
        mock_user.is_active = True

        async def override_get_current_user():
            return mock_user

        app.dependency_overrides[get_current_user] = override_get_current_user
        yield app, mock_user
        app.dependency_overrides.clear()

    def test_stripe_onboard_requires_authentication(self, client: TestClient) -> None:
        """Test that Stripe onboarding requires authentication."""
        response = client.post(
            "/api/v1/hosts/stripe/onboard",
            json={
                "refresh_url": "http://localhost:5175/stripe/refresh",
                "return_url": "http://localhost:5175/stripe/return",
            },
        )
        # Should return 401 without authentication
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_stripe_onboard_returns_404_for_non_host(self, auth_app) -> None:
        """Test that Stripe onboarding returns 404 if user is not a host."""
        app, _ = auth_app
        client = TestClient(app)

        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_user_id.return_value = None

            response = client.post(
                "/api/v1/hosts/stripe/onboard",
                json={
                    "refresh_url": "http://localhost:5175/stripe/refresh",
                    "return_url": "http://localhost:5175/stripe/return",
                },
            )
            assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_stripe_onboard_creates_new_account(self, auth_app) -> None:
        """Test that Stripe onboarding creates a new account if none exists."""
        app, mock_user = auth_app
        client = TestClient(app)

        mock_profile = MagicMock()
        mock_profile.id = "660e8400-e29b-41d4-a716-446655440001"
        mock_profile.stripe_account_id = None  # No Stripe account yet

        with (
            patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class,
            patch("app.routers.hosts.stripe_service") as mock_stripe_service,
        ):
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_user_id.return_value = mock_profile
            mock_host_repo.update.return_value = mock_profile

            mock_stripe_service.create_connect_account = AsyncMock(
                return_value="acct_test123"
            )
            mock_stripe_service.create_account_link = AsyncMock(
                return_value="https://connect.stripe.com/onboard/test"
            )

            response = client.post(
                "/api/v1/hosts/stripe/onboard",
                json={
                    "refresh_url": "http://localhost:5175/stripe/refresh",
                    "return_url": "http://localhost:5175/stripe/return",
                },
            )
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["account_id"] == "acct_test123"
            assert data["onboarding_url"] == "https://connect.stripe.com/onboard/test"

    def test_stripe_onboard_uses_existing_account(self, auth_app) -> None:
        """Test that Stripe onboarding uses existing account if present."""
        app, _ = auth_app
        client = TestClient(app)

        mock_profile = MagicMock()
        mock_profile.id = "660e8400-e29b-41d4-a716-446655440001"
        mock_profile.stripe_account_id = "acct_existing123"

        with (
            patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class,
            patch("app.routers.hosts.stripe_service") as mock_stripe_service,
        ):
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_user_id.return_value = mock_profile

            mock_stripe_service.create_account_link = AsyncMock(
                return_value="https://connect.stripe.com/onboard/existing"
            )
            mock_stripe_service.create_connect_account = AsyncMock()

            response = client.post(
                "/api/v1/hosts/stripe/onboard",
                json={
                    "refresh_url": "http://localhost:5175/stripe/refresh",
                    "return_url": "http://localhost:5175/stripe/return",
                },
            )
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["account_id"] == "acct_existing123"
            # create_connect_account should not be called
            mock_stripe_service.create_connect_account.assert_not_called()

    def test_stripe_onboard_handles_stripe_error(self, auth_app) -> None:
        """Test that Stripe onboarding handles Stripe API errors."""
        import stripe

        app, _ = auth_app
        client = TestClient(app)

        mock_profile = MagicMock()
        mock_profile.id = "660e8400-e29b-41d4-a716-446655440001"
        mock_profile.stripe_account_id = "acct_test123"

        with (
            patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class,
            patch("app.routers.hosts.stripe_service") as mock_stripe_service,
        ):
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_user_id.return_value = mock_profile

            mock_stripe_service.create_account_link = AsyncMock(
                side_effect=stripe.StripeError("Connection error")
            )

            response = client.post(
                "/api/v1/hosts/stripe/onboard",
                json={
                    "refresh_url": "http://localhost:5175/stripe/refresh",
                    "return_url": "http://localhost:5175/stripe/return",
                },
            )
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_stripe_onboard_handles_value_error(self, auth_app) -> None:
        """Test that Stripe onboarding handles ValueError from stripe service."""
        app, _ = auth_app
        client = TestClient(app)

        mock_profile = MagicMock()
        mock_profile.id = "660e8400-e29b-41d4-a716-446655440001"
        mock_profile.stripe_account_id = None

        with (
            patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class,
            patch("app.routers.hosts.stripe_service") as mock_stripe_service,
        ):
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_user_id.return_value = mock_profile

            mock_stripe_service.create_connect_account = AsyncMock(
                side_effect=ValueError("Stripe not configured")
            )

            response = client.post(
                "/api/v1/hosts/stripe/onboard",
                json={
                    "refresh_url": "http://localhost:5175/stripe/refresh",
                    "return_url": "http://localhost:5175/stripe/return",
                },
            )
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestStripeAccountStatusEndpoint:
    """Tests for GET /api/v1/hosts/stripe/status endpoint."""

    @pytest.fixture
    def auth_app(self, app):
        """Create app with authentication mocked."""
        from app.core.deps import get_current_user

        mock_user = MagicMock()
        mock_user.id = "550e8400-e29b-41d4-a716-446655440000"
        mock_user.email = "host@example.com"
        mock_user.is_active = True

        async def override_get_current_user():
            return mock_user

        app.dependency_overrides[get_current_user] = override_get_current_user
        yield app, mock_user
        app.dependency_overrides.clear()

    def test_stripe_status_requires_authentication(self, client: TestClient) -> None:
        """Test that Stripe status requires authentication."""
        response = client.get("/api/v1/hosts/stripe/status")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_stripe_status_returns_404_for_non_host(self, auth_app) -> None:
        """Test that Stripe status returns 404 if user is not a host."""
        app, _ = auth_app
        client = TestClient(app)

        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_user_id.return_value = None

            response = client.get("/api/v1/hosts/stripe/status")
            assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_stripe_status_returns_not_created_if_no_account(self, auth_app) -> None:
        """Test that Stripe status returns NOT_CREATED if no Stripe account."""
        app, _ = auth_app
        client = TestClient(app)

        mock_profile = MagicMock()
        mock_profile.id = "660e8400-e29b-41d4-a716-446655440001"
        mock_profile.stripe_account_id = None

        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_user_id.return_value = mock_profile

            response = client.get("/api/v1/hosts/stripe/status")
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["status"] == "not_created"
            assert data["charges_enabled"] is False
            assert data["payouts_enabled"] is False

    def test_stripe_status_returns_account_status(self, auth_app) -> None:
        """Test that Stripe status returns full account status."""
        from app.services.stripe import StripeAccountStatus

        app, _ = auth_app
        client = TestClient(app)

        mock_profile = MagicMock()
        mock_profile.id = "660e8400-e29b-41d4-a716-446655440001"
        mock_profile.stripe_account_id = "acct_test123"
        mock_profile.stripe_onboarding_complete = False

        mock_account_status = MagicMock()
        mock_account_status.account_id = "acct_test123"
        mock_account_status.status = StripeAccountStatus.PENDING
        mock_account_status.charges_enabled = False
        mock_account_status.payouts_enabled = False
        mock_account_status.details_submitted = True
        mock_account_status.requirements_due = ["verification.document"]

        with (
            patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class,
            patch("app.routers.hosts.stripe_service") as mock_stripe_service,
        ):
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_user_id.return_value = mock_profile

            mock_stripe_service.get_account_status = AsyncMock(
                return_value=mock_account_status
            )

            response = client.get("/api/v1/hosts/stripe/status")
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["account_id"] == "acct_test123"
            assert data["charges_enabled"] is False

    def test_stripe_status_updates_onboarding_complete(self, auth_app) -> None:
        """Test that Stripe status updates onboarding_complete when charges enabled."""
        from app.services.stripe import StripeAccountStatus

        app, _ = auth_app
        client = TestClient(app)

        mock_profile = MagicMock()
        mock_profile.id = "660e8400-e29b-41d4-a716-446655440001"
        mock_profile.stripe_account_id = "acct_test123"
        mock_profile.stripe_onboarding_complete = False

        mock_account_status = MagicMock()
        mock_account_status.account_id = "acct_test123"
        mock_account_status.status = (
            StripeAccountStatus.ACTIVE
        )  # Use ACTIVE instead of COMPLETE
        mock_account_status.charges_enabled = True
        mock_account_status.payouts_enabled = True
        mock_account_status.details_submitted = True
        mock_account_status.requirements_due = []

        with (
            patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class,
            patch("app.routers.hosts.stripe_service") as mock_stripe_service,
        ):
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_user_id.return_value = mock_profile
            mock_host_repo.update.return_value = mock_profile

            mock_stripe_service.get_account_status = AsyncMock(
                return_value=mock_account_status
            )

            response = client.get("/api/v1/hosts/stripe/status")
            assert response.status_code == status.HTTP_200_OK

            # Verify update was called to set onboarding_complete
            mock_host_repo.update.assert_called_once()

    def test_stripe_status_handles_stripe_error(self, auth_app) -> None:
        """Test that Stripe status handles Stripe API errors."""
        import stripe

        app, _ = auth_app
        client = TestClient(app)

        mock_profile = MagicMock()
        mock_profile.id = "660e8400-e29b-41d4-a716-446655440001"
        mock_profile.stripe_account_id = "acct_test123"

        with (
            patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class,
            patch("app.routers.hosts.stripe_service") as mock_stripe_service,
        ):
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_user_id.return_value = mock_profile

            mock_stripe_service.get_account_status = AsyncMock(
                side_effect=stripe.StripeError("API Error")
            )

            response = client.get("/api/v1/hosts/stripe/status")
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_stripe_status_handles_value_error(self, auth_app) -> None:
        """Test that Stripe status handles ValueError."""
        app, _ = auth_app
        client = TestClient(app)

        mock_profile = MagicMock()
        mock_profile.id = "660e8400-e29b-41d4-a716-446655440001"
        mock_profile.stripe_account_id = "acct_test123"

        with (
            patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class,
            patch("app.routers.hosts.stripe_service") as mock_stripe_service,
        ):
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_user_id.return_value = mock_profile

            mock_stripe_service.get_account_status = AsyncMock(
                side_effect=ValueError("Invalid account")
            )

            response = client.get("/api/v1/hosts/stripe/status")
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestVerificationEndpoints:
    """Tests for verification endpoints."""

    @pytest.fixture
    def auth_app(self, app):
        """Create app with authentication mocked."""
        from app.core.deps import get_current_user

        mock_user = MagicMock()
        mock_user.id = "550e8400-e29b-41d4-a716-446655440000"
        mock_user.email = "host@example.com"
        mock_user.is_active = True

        async def override_get_current_user():
            return mock_user

        app.dependency_overrides[get_current_user] = override_get_current_user
        yield app, mock_user
        app.dependency_overrides.clear()

    def test_submit_verification_requires_authentication(
        self, client: TestClient
    ) -> None:
        """Test that submit verification requires authentication."""
        response = client.post(
            "/api/v1/hosts/verification/submit",
            json={
                "document_type": "passport",
                "document_url": "https://example.com/doc.jpg",
            },
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_submit_verification_returns_404_for_non_host(self, auth_app) -> None:
        """Test that submit verification returns 404 if user is not a host."""
        app, _ = auth_app
        client = TestClient(app)

        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_user_id.return_value = None

            response = client.post(
                "/api/v1/hosts/verification/submit",
                json={
                    "document_type": "passport",
                    "document_url": "https://example.com/doc.jpg",
                },
            )
            assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_submit_verification_success(self, auth_app) -> None:
        """Test successful verification submission."""
        app, _ = auth_app
        client = TestClient(app)

        mock_profile = MagicMock()
        mock_profile.id = "660e8400-e29b-41d4-a716-446655440001"

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.document_id = "770e8400-e29b-41d4-a716-446655440001"

        with (
            patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class,
            patch(
                "app.routers.hosts.get_verification_service"
            ) as mock_get_verification,
        ):
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_user_id.return_value = mock_profile

            mock_verification_service = MagicMock()
            mock_verification_service.submit_verification = AsyncMock(
                return_value=mock_result
            )
            mock_get_verification.return_value = mock_verification_service

            response = client.post(
                "/api/v1/hosts/verification/submit",
                json={
                    "document_type": "passport",
                    "document_url": "https://example.com/doc.jpg",
                    "document_number": "AB123456",
                    "notes": "Front side of passport",
                },
            )
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["success"] is True
            assert data["document_id"] is not None

    def test_submit_verification_failure(self, auth_app) -> None:
        """Test verification submission failure (already verified or pending)."""
        app, _ = auth_app
        client = TestClient(app)

        mock_profile = MagicMock()
        mock_profile.id = "660e8400-e29b-41d4-a716-446655440001"

        mock_result = MagicMock()
        mock_result.success = False
        mock_result.error_message = "Verification already pending"

        with (
            patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class,
            patch(
                "app.routers.hosts.get_verification_service"
            ) as mock_get_verification,
        ):
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_user_id.return_value = mock_profile

            mock_verification_service = MagicMock()
            mock_verification_service.submit_verification = AsyncMock(
                return_value=mock_result
            )
            mock_get_verification.return_value = mock_verification_service

            response = client.post(
                "/api/v1/hosts/verification/submit",
                json={
                    "document_type": "passport",
                    "document_url": "https://example.com/doc.jpg",
                },
            )
            assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_verification_status_requires_authentication(
        self, client: TestClient
    ) -> None:
        """Test that get verification status requires authentication."""
        response = client.get("/api/v1/hosts/verification/status")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_verification_status_returns_404_for_non_host(self, auth_app) -> None:
        """Test that get verification status returns 404 if user is not a host."""
        app, _ = auth_app
        client = TestClient(app)

        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_user_id.return_value = None

            response = client.get("/api/v1/hosts/verification/status")
            assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_verification_status_success(self, auth_app) -> None:
        """Test successful verification status retrieval."""
        from datetime import datetime

        app, _ = auth_app
        client = TestClient(app)

        mock_profile = MagicMock()
        mock_profile.id = "660e8400-e29b-41d4-a716-446655440001"

        mock_document = MagicMock()
        mock_document.id = "770e8400-e29b-41d4-a716-446655440001"
        mock_document.document_type = "passport"
        mock_document.document_url = "https://example.com/doc.jpg"
        mock_document.document_number = "AB123456"
        mock_document.notes = "Front side"
        mock_document.reviewer_notes = None
        mock_document.reviewed_at = None
        mock_document.created_at = datetime(2026, 1, 15)

        mock_status_result = MagicMock()
        mock_status_result.status = VerificationStatus.PENDING
        mock_status_result.can_submit = False
        mock_status_result.rejection_reason = None
        mock_status_result.documents = [mock_document]

        with (
            patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class,
            patch(
                "app.routers.hosts.get_verification_service"
            ) as mock_get_verification,
        ):
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_user_id.return_value = mock_profile

            mock_verification_service = MagicMock()
            mock_verification_service.get_verification_status = AsyncMock(
                return_value=mock_status_result
            )
            mock_get_verification.return_value = mock_verification_service

            response = client.get("/api/v1/hosts/verification/status")
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["status"] == "pending"
            assert data["can_submit"] is False
            assert len(data["documents"]) == 1

    def test_get_verification_status_returns_404_when_none(self, auth_app) -> None:
        """Test get verification status returns 404 when service returns None."""
        app, _ = auth_app
        client = TestClient(app)

        mock_profile = MagicMock()
        mock_profile.id = "660e8400-e29b-41d4-a716-446655440001"

        with (
            patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class,
            patch(
                "app.routers.hosts.get_verification_service"
            ) as mock_get_verification,
        ):
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.get_by_user_id.return_value = mock_profile

            mock_verification_service = MagicMock()
            mock_verification_service.get_verification_status = AsyncMock(
                return_value=None
            )
            mock_get_verification.return_value = mock_verification_service

            response = client.get("/api/v1/hosts/verification/status")
            assert response.status_code == status.HTTP_404_NOT_FOUND


class TestCalculateDistanceKm:
    """Tests for the _calculate_distance_km helper function."""

    def test_calculate_distance_returns_none(self) -> None:
        """Test that _calculate_distance_km currently returns None."""
        from app.routers.hosts import _calculate_distance_km

        mock_profile = MagicMock()
        mock_profile.location = MagicMock()

        result = _calculate_distance_km(40.7, -74.0, mock_profile)
        # Currently returns None as per implementation
        assert result is None


class TestSearchHostsCursor:
    """Tests for cursor-based pagination on GET /api/v1/hosts/search endpoint."""

    def test_search_cursor_endpoint_exists(self, client: TestClient) -> None:
        """Test that the cursor-based search endpoint exists."""
        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search_with_cursor.return_value = ([], 0, None, False)

            response = client.get("/api/v1/hosts/search")
            assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_search_cursor_returns_200(self, client: TestClient) -> None:
        """Test that cursor search returns 200 OK."""
        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search_with_cursor.return_value = ([], 0, None, False)

            response = client.get("/api/v1/hosts/search")
            assert response.status_code == status.HTTP_200_OK

    def test_search_cursor_response_structure(self, client: TestClient) -> None:
        """Test that cursor response has correct fields."""
        mock_profile = create_mock_host_profile()

        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search_with_cursor.return_value = (
                [mock_profile],
                1,
                "next-cursor-id",
                True,
            )

            response = client.get("/api/v1/hosts/search")
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert "items" in data
            assert "next_cursor" in data
            assert "has_more" in data
            assert "total" in data
            # Should NOT have offset-based pagination fields
            assert "page" not in data
            assert "page_size" not in data
            assert "total_pages" not in data

    def test_search_cursor_accepts_cursor_parameter(self, client: TestClient) -> None:
        """Test that cursor parameter is accepted."""
        cursor_id = "660e8400-e29b-41d4-a716-446655440001"

        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search_with_cursor.return_value = ([], 0, None, False)

            response = client.get(f"/api/v1/hosts/search?cursor={cursor_id}")
            assert response.status_code == status.HTTP_200_OK

            # Verify cursor was passed to repository
            call_kwargs = mock_host_repo.search_with_cursor.call_args.kwargs
            assert str(call_kwargs["cursor"]) == cursor_id

    def test_search_cursor_invalid_cursor_returns_400(self, client: TestClient) -> None:
        """Test that invalid cursor format returns 400."""
        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo

            response = client.get("/api/v1/hosts/search?cursor=not-a-uuid")
            assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_search_cursor_returns_next_cursor(self, client: TestClient) -> None:
        """Test that next_cursor is returned when there are more results."""
        mock_profile = create_mock_host_profile()
        next_cursor_id = "660e8400-e29b-41d4-a716-446655440002"

        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search_with_cursor.return_value = (
                [mock_profile],
                10,
                next_cursor_id,
                True,
            )

            response = client.get("/api/v1/hosts/search?limit=1")
            data = response.json()

            assert data["next_cursor"] == next_cursor_id
            assert data["has_more"] is True

    def test_search_cursor_null_when_no_more(self, client: TestClient) -> None:
        """Test that next_cursor is null when no more results."""
        mock_profile = create_mock_host_profile()

        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search_with_cursor.return_value = (
                [mock_profile],
                1,
                None,
                False,
            )

            response = client.get("/api/v1/hosts/search")
            data = response.json()

            assert data["next_cursor"] is None
            assert data["has_more"] is False

    def test_search_cursor_accepts_limit_parameter(self, client: TestClient) -> None:
        """Test that limit parameter is accepted."""
        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search_with_cursor.return_value = ([], 0, None, False)

            response = client.get("/api/v1/hosts/search?limit=50")
            assert response.status_code == status.HTTP_200_OK

            call_kwargs = mock_host_repo.search_with_cursor.call_args.kwargs
            assert call_kwargs["limit"] == 50

    def test_search_cursor_with_all_filters(self, client: TestClient) -> None:
        """Test cursor search with all filter parameters."""
        mock_profile = create_mock_host_profile()

        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search_with_cursor.return_value = (
                [mock_profile],
                1,
                None,
                False,
            )

            response = client.get(
                "/api/v1/hosts/search?lat=40.7&lng=-74.0&radius_km=25"
                "&min_rating=4.0&max_price=10000&q=salsa&limit=10"
            )
            assert response.status_code == status.HTTP_200_OK

            call_kwargs = mock_host_repo.search_with_cursor.call_args.kwargs
            assert call_kwargs["latitude"] == 40.7
            assert call_kwargs["longitude"] == -74.0
            assert call_kwargs["radius_km"] == 25.0
            assert call_kwargs["min_rating"] == 4.0
            assert call_kwargs["max_price_cents"] == 10000
            assert call_kwargs["query"] == "salsa"
            assert call_kwargs["limit"] == 10

    def test_search_cursor_sort_by_relevance(self, client: TestClient) -> None:
        """Test that sort_by=relevance is supported."""
        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search_with_cursor.return_value = ([], 0, None, False)

            response = client.get("/api/v1/hosts/search?q=salsa&sort_by=relevance")
            assert response.status_code == status.HTTP_200_OK

            call_kwargs = mock_host_repo.search_with_cursor.call_args.kwargs
            assert call_kwargs["order_by"] == "relevance"

    def test_search_cursor_returns_total_count(self, client: TestClient) -> None:
        """Test that total count is returned."""
        mock_profile = create_mock_host_profile()

        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search_with_cursor.return_value = (
                [mock_profile],
                42,
                None,
                False,
            )

            response = client.get("/api/v1/hosts/search")
            data = response.json()

            assert data["total"] == 42


class TestFuzzySearchHosts:
    """Tests for fuzzy text search on hosts endpoint using pg_trgm."""

    def test_search_hosts_accepts_q_parameter(self, client: TestClient) -> None:
        """Test that search hosts accepts the q query parameter."""
        mock_profile = create_mock_host_profile()

        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search.return_value = ([mock_profile], 1)

            response = client.get("/api/v1/hosts?q=salsa")
            assert response.status_code == status.HTTP_200_OK

            # Verify that search was called with query parameter
            mock_host_repo.search.assert_called_once()
            call_kwargs = mock_host_repo.search.call_args.kwargs
            assert call_kwargs["query"] == "salsa"

    def test_search_hosts_passes_query_to_repository(self, client: TestClient) -> None:
        """Test that the q parameter is passed to the repository search method."""
        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search.return_value = ([], 0)

            client.get("/api/v1/hosts?q=john%20dancer")

            mock_host_repo.search.assert_called_once()
            call_kwargs = mock_host_repo.search.call_args.kwargs
            assert call_kwargs["query"] == "john dancer"

    def test_search_hosts_q_parameter_with_max_length(self, client: TestClient) -> None:
        """Test that q parameter respects max_length of 200 characters."""
        long_query = "a" * 201  # Over 200 characters

        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search.return_value = ([], 0)

            response = client.get(f"/api/v1/hosts?q={long_query}")
            # FastAPI should reject queries over 200 chars
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_search_hosts_empty_query_is_allowed(self, client: TestClient) -> None:
        """Test that an empty q parameter is allowed and works."""
        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search.return_value = ([], 0)

            response = client.get("/api/v1/hosts?q=")
            assert response.status_code == status.HTTP_200_OK

            # Empty query should be passed as empty string
            call_kwargs = mock_host_repo.search.call_args.kwargs
            assert call_kwargs["query"] == ""

    def test_search_hosts_q_defaults_to_none(self, client: TestClient) -> None:
        """Test that q parameter defaults to None when not provided."""
        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search.return_value = ([], 0)

            client.get("/api/v1/hosts")

            mock_host_repo.search.assert_called_once()
            call_kwargs = mock_host_repo.search.call_args.kwargs
            assert call_kwargs["query"] is None

    def test_search_hosts_sort_by_relevance(self, client: TestClient) -> None:
        """Test that sort_by=relevance is accepted and passed to repository."""
        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search.return_value = ([], 0)

            response = client.get("/api/v1/hosts?q=salsa&sort_by=relevance")
            assert response.status_code == status.HTTP_200_OK

            mock_host_repo.search.assert_called_once()
            call_kwargs = mock_host_repo.search.call_args.kwargs
            assert call_kwargs["order_by"] == "relevance"

    def test_search_hosts_with_query_defaults_to_relevance_sort(
        self, client: TestClient
    ) -> None:
        """Test that when q is provided with invalid sort_by, defaults to relevance."""
        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search.return_value = ([], 0)

            response = client.get("/api/v1/hosts?q=dancer&sort_by=invalid")
            assert response.status_code == status.HTTP_200_OK

            mock_host_repo.search.assert_called_once()
            call_kwargs = mock_host_repo.search.call_args.kwargs
            assert call_kwargs["order_by"] == "relevance"

    def test_search_hosts_without_query_defaults_to_distance_sort(
        self, client: TestClient
    ) -> None:
        """Test that without q, invalid sort_by defaults to distance."""
        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search.return_value = ([], 0)

            response = client.get("/api/v1/hosts?sort_by=invalid")
            assert response.status_code == status.HTTP_200_OK

            mock_host_repo.search.assert_called_once()
            call_kwargs = mock_host_repo.search.call_args.kwargs
            assert call_kwargs["order_by"] == "distance"

    def test_search_hosts_q_combined_with_location(self, client: TestClient) -> None:
        """Test that q parameter can be combined with location filters."""
        mock_profile = create_mock_host_profile()

        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search.return_value = ([mock_profile], 1)

            response = client.get(
                "/api/v1/hosts?q=salsa&lat=40.7&lng=-74.0&radius_km=25"
            )
            assert response.status_code == status.HTTP_200_OK

            mock_host_repo.search.assert_called_once()
            call_kwargs = mock_host_repo.search.call_args.kwargs
            assert call_kwargs["query"] == "salsa"
            assert call_kwargs["latitude"] == 40.7
            assert call_kwargs["longitude"] == -74.0
            assert call_kwargs["radius_km"] == 25.0

    def test_search_hosts_q_combined_with_filters(self, client: TestClient) -> None:
        """Test that q parameter can be combined with other filters."""
        mock_profile = create_mock_host_profile()

        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search.return_value = ([mock_profile], 1)

            response = client.get(
                "/api/v1/hosts?q=tango&min_rating=4.0&max_price=10000"
            )
            assert response.status_code == status.HTTP_200_OK

            mock_host_repo.search.assert_called_once()
            call_kwargs = mock_host_repo.search.call_args.kwargs
            assert call_kwargs["query"] == "tango"
            assert call_kwargs["min_rating"] == 4.0
            assert call_kwargs["max_price_cents"] == 10000

    def test_search_hosts_q_with_special_characters(self, client: TestClient) -> None:
        """Test that q parameter handles special characters gracefully."""
        mock_profile = create_mock_host_profile()

        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search.return_value = ([mock_profile], 1)

            # URL encode special characters
            response = client.get("/api/v1/hosts?q=john%27s%20dance")
            assert response.status_code == status.HTTP_200_OK

            mock_host_repo.search.assert_called_once()
            call_kwargs = mock_host_repo.search.call_args.kwargs
            assert call_kwargs["query"] == "john's dance"

    def test_search_hosts_returns_results_for_fuzzy_query(
        self, client: TestClient
    ) -> None:
        """Test that search returns matching profiles for a query."""
        mock_profile = create_mock_host_profile(
            headline="Professional Salsa Instructor"
        )

        with patch("app.routers.hosts.HostProfileRepository") as mock_host_repo_class:
            mock_host_repo = AsyncMock()
            mock_host_repo_class.return_value = mock_host_repo
            mock_host_repo.search.return_value = ([mock_profile], 1)

            response = client.get("/api/v1/hosts?q=salsa")
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert len(data["items"]) == 1
            assert data["items"][0]["headline"] == "Professional Salsa Instructor"
            assert data["total"] == 1
