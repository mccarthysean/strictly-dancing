"""Unit tests for geo utility functions."""

import pytest

from app.core.geo import (
    Coordinates,
    create_point_ewkt,
    create_point_wkt,
    extract_coordinates_from_geography,
)


class TestExtractCoordinatesFromGeography:
    """Tests for extract_coordinates_from_geography function."""

    def test_returns_none_for_none_input(self):
        """Should return None when input is None."""
        result = extract_coordinates_from_geography(None)
        assert result is None

    def test_extracts_from_wkt_format(self):
        """Should extract coordinates from WKT POINT format."""
        # WKT format: POINT(longitude latitude)
        wkt = "POINT(-74.006 40.7128)"
        result = extract_coordinates_from_geography(wkt)

        assert result is not None
        assert isinstance(result, Coordinates)
        assert result.latitude == pytest.approx(40.7128)
        assert result.longitude == pytest.approx(-74.006)

    def test_extracts_from_ewkt_format(self):
        """Should extract coordinates from EWKT POINT format with SRID."""
        # EWKT format: SRID=4326;POINT(longitude latitude)
        ewkt = "SRID=4326;POINT(-74.006 40.7128)"
        result = extract_coordinates_from_geography(ewkt)

        assert result is not None
        assert isinstance(result, Coordinates)
        assert result.latitude == pytest.approx(40.7128)
        assert result.longitude == pytest.approx(-74.006)

    def test_extracts_from_wkt_with_extra_spaces(self):
        """Should handle WKT with extra whitespace."""
        wkt = "POINT(  -74.006   40.7128  )"
        result = extract_coordinates_from_geography(wkt)

        assert result is not None
        assert result.latitude == pytest.approx(40.7128)
        assert result.longitude == pytest.approx(-74.006)

    def test_extracts_from_case_insensitive_wkt(self):
        """Should handle case variations in WKT."""
        wkt = "point(-74.006 40.7128)"
        result = extract_coordinates_from_geography(wkt)

        assert result is not None
        assert result.latitude == pytest.approx(40.7128)
        assert result.longitude == pytest.approx(-74.006)

    def test_handles_negative_coordinates(self):
        """Should correctly handle negative latitude and longitude."""
        # Southern hemisphere, Western hemisphere
        wkt = "POINT(-122.4194 -37.7749)"
        result = extract_coordinates_from_geography(wkt)

        assert result is not None
        assert result.latitude == pytest.approx(-37.7749)
        assert result.longitude == pytest.approx(-122.4194)

    def test_handles_positive_coordinates(self):
        """Should correctly handle positive latitude and longitude."""
        # Northern hemisphere, Eastern hemisphere
        wkt = "POINT(139.6917 35.6895)"
        result = extract_coordinates_from_geography(wkt)

        assert result is not None
        assert result.latitude == pytest.approx(35.6895)
        assert result.longitude == pytest.approx(139.6917)

    def test_handles_integer_coordinates(self):
        """Should handle integer coordinate values."""
        wkt = "POINT(-74 40)"
        result = extract_coordinates_from_geography(wkt)

        assert result is not None
        assert result.latitude == pytest.approx(40.0)
        assert result.longitude == pytest.approx(-74.0)

    def test_handles_zero_coordinates(self):
        """Should handle zero coordinates (Gulf of Guinea)."""
        wkt = "POINT(0 0)"
        result = extract_coordinates_from_geography(wkt)

        assert result is not None
        assert result.latitude == pytest.approx(0.0)
        assert result.longitude == pytest.approx(0.0)

    def test_returns_none_for_invalid_format(self):
        """Should return None for invalid format strings."""
        invalid_inputs = [
            "INVALID",
            "NOT A POINT",
            "POLYGON((0 0, 1 1, 1 0, 0 0))",
            "",
            "POINT()",
            "POINT(40.7128)",  # Only one coordinate
        ]

        for invalid_input in invalid_inputs:
            result = extract_coordinates_from_geography(invalid_input)
            assert result is None, f"Expected None for input: {invalid_input}"

    def test_handles_string_representation(self):
        """Should handle string representation from SQLAlchemy."""
        # Sometimes SQLAlchemy returns the value as a string
        wkt_str = "POINT(-74.006 40.7128)"
        result = extract_coordinates_from_geography(wkt_str)

        assert result is not None
        assert result.latitude == pytest.approx(40.7128)
        assert result.longitude == pytest.approx(-74.006)


class TestCreatePointWkt:
    """Tests for create_point_wkt function."""

    def test_creates_valid_wkt(self):
        """Should create valid WKT POINT string."""
        result = create_point_wkt(40.7128, -74.006)
        assert result == "POINT(-74.006 40.7128)"

    def test_handles_negative_coordinates(self):
        """Should handle negative coordinates."""
        result = create_point_wkt(-37.7749, -122.4194)
        assert result == "POINT(-122.4194 -37.7749)"

    def test_handles_zero_coordinates(self):
        """Should handle zero coordinates."""
        result = create_point_wkt(0, 0)
        assert result == "POINT(0 0)"

    def test_handles_high_precision_coordinates(self):
        """Should preserve high precision coordinates."""
        result = create_point_wkt(40.71284530, -74.00597110)
        assert "40.7128453" in result
        assert "-74.0059711" in result


class TestCreatePointEwkt:
    """Tests for create_point_ewkt function."""

    def test_creates_valid_ewkt_with_default_srid(self):
        """Should create valid EWKT with default SRID 4326."""
        result = create_point_ewkt(40.7128, -74.006)
        assert result == "SRID=4326;POINT(-74.006 40.7128)"

    def test_creates_valid_ewkt_with_custom_srid(self):
        """Should create valid EWKT with custom SRID."""
        result = create_point_ewkt(40.7128, -74.006, srid=3857)
        assert result == "SRID=3857;POINT(-74.006 40.7128)"

    def test_handles_negative_coordinates(self):
        """Should handle negative coordinates."""
        result = create_point_ewkt(-37.7749, -122.4194)
        assert result == "SRID=4326;POINT(-122.4194 -37.7749)"

    def test_round_trip_extraction(self):
        """Should be able to extract coordinates from created EWKT."""
        original_lat = 40.7128
        original_lng = -74.006

        ewkt = create_point_ewkt(original_lat, original_lng)
        coords = extract_coordinates_from_geography(ewkt)

        assert coords is not None
        assert coords.latitude == pytest.approx(original_lat)
        assert coords.longitude == pytest.approx(original_lng)


class TestCoordinatesNamedTuple:
    """Tests for the Coordinates named tuple."""

    def test_coordinates_fields(self):
        """Should have latitude and longitude fields."""
        coords = Coordinates(latitude=40.7128, longitude=-74.006)
        assert coords.latitude == 40.7128
        assert coords.longitude == -74.006

    def test_coordinates_unpacking(self):
        """Should support tuple unpacking."""
        coords = Coordinates(latitude=40.7128, longitude=-74.006)
        lat, lng = coords
        assert lat == 40.7128
        assert lng == -74.006

    def test_coordinates_indexing(self):
        """Should support indexing."""
        coords = Coordinates(latitude=40.7128, longitude=-74.006)
        assert coords[0] == 40.7128
        assert coords[1] == -74.006
