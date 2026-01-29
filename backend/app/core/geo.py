"""Geographic utility functions for PostGIS operations."""

import re
from typing import NamedTuple


class Coordinates(NamedTuple):
    """Represents a geographic coordinate pair."""

    latitude: float
    longitude: float


def extract_coordinates_from_geography(location: str | None) -> Coordinates | None:
    """Extract latitude and longitude from a PostGIS Geography/Geometry value.

    PostGIS stores Geography POINT values in WKB (Well-Known Binary) format
    when accessed as strings. However, when accessed through GeoAlchemy2
    with the proper type mapping, we may receive:
    - WKT (Well-Known Text): 'POINT(longitude latitude)'
    - EWKT: 'SRID=4326;POINT(longitude latitude)'
    - Hex WKB: A hex string like '0101000020E6100000...'

    This function handles all common formats.

    Note: PostGIS POINT format is POINT(longitude latitude), not (latitude longitude).

    Args:
        location: The PostGIS geography/geometry value as a string.

    Returns:
        Coordinates tuple with latitude and longitude, or None if extraction fails.

    Examples:
        >>> extract_coordinates_from_geography("POINT(-74.006 40.7128)")
        Coordinates(latitude=40.7128, longitude=-74.006)

        >>> extract_coordinates_from_geography("SRID=4326;POINT(-74.006 40.7128)")
        Coordinates(latitude=40.7128, longitude=-74.006)

        >>> extract_coordinates_from_geography(None)
        None
    """
    if location is None:
        return None

    # Handle string representations
    location_str = str(location)

    # Try to extract from WKT or EWKT format: POINT(longitude latitude)
    # Also handles SRID prefix: SRID=4326;POINT(...)
    wkt_pattern = r"POINT\s*\(\s*(-?\d+\.?\d*)\s+(-?\d+\.?\d*)\s*\)"
    match = re.search(wkt_pattern, location_str, re.IGNORECASE)

    if match:
        # PostGIS POINT is (longitude, latitude)
        longitude = float(match.group(1))
        latitude = float(match.group(2))
        return Coordinates(latitude=latitude, longitude=longitude)

    # If no WKT match, the value might be in WKB hex format
    # In that case, we need to use shapely or geoalchemy2 to parse it
    try:
        # Try to parse hex WKB using geoalchemy2's WKBElement
        from geoalchemy2 import WKBElement
        from geoalchemy2.shape import to_shape

        # Check if it looks like hex WKB (starts with 01 for little-endian)
        if location_str.startswith("01") and len(location_str) > 40:
            # Convert hex string to bytes
            wkb_bytes = bytes.fromhex(location_str)
            wkb_element = WKBElement(wkb_bytes, srid=4326)
            shape = to_shape(wkb_element)

            if shape.geom_type == "Point":
                # shapely Point: (x, y) = (longitude, latitude)
                return Coordinates(latitude=shape.y, longitude=shape.x)
    except (ImportError, ValueError, TypeError):
        # If geoalchemy2/shapely not available or parsing fails, return None
        pass

    return None


def create_point_wkt(latitude: float, longitude: float) -> str:
    """Create a WKT (Well-Known Text) POINT string from coordinates.

    The resulting string can be used with PostGIS functions like ST_GeomFromText
    or ST_GeographyFromText.

    Args:
        latitude: The latitude (-90 to 90).
        longitude: The longitude (-180 to 180).

    Returns:
        WKT string in format 'POINT(longitude latitude)'.

    Examples:
        >>> create_point_wkt(40.7128, -74.006)
        'POINT(-74.006 40.7128)'
    """
    # PostGIS POINT format is (longitude, latitude)
    return f"POINT({longitude} {latitude})"


def create_point_ewkt(latitude: float, longitude: float, srid: int = 4326) -> str:
    """Create an EWKT (Extended Well-Known Text) POINT string with SRID.

    The SRID (Spatial Reference System Identifier) 4326 corresponds to WGS84,
    which is the standard for GPS coordinates.

    Args:
        latitude: The latitude (-90 to 90).
        longitude: The longitude (-180 to 180).
        srid: The spatial reference system ID (default 4326 for WGS84).

    Returns:
        EWKT string in format 'SRID=4326;POINT(longitude latitude)'.

    Examples:
        >>> create_point_ewkt(40.7128, -74.006)
        'SRID=4326;POINT(-74.006 40.7128)'
    """
    return f"SRID={srid};{create_point_wkt(latitude, longitude)}"
