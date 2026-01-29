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
