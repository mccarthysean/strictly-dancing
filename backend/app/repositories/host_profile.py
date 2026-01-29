"""Host profile repository for data access operations."""

from uuid import UUID

from geoalchemy2.functions import ST_Distance, ST_DWithin, ST_MakePoint, ST_SetSRID
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.dance_style import DanceStyle
from app.models.host_dance_style import HostDanceStyle
from app.models.host_profile import HostProfile


class HostProfileRepository:
    """Repository for HostProfile CRUD and query operations.

    Implements the repository pattern for host profile data access,
    providing an abstraction layer over SQLAlchemy operations.
    Includes geospatial queries using PostGIS.

    All methods use async patterns for non-blocking database access.

    Attributes:
        session: The async database session for executing queries.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session.

        Args:
            session: An async SQLAlchemy session.
        """
        self._session = session

    async def create(
        self,
        user_id: UUID,
        bio: str | None = None,
        headline: str | None = None,
        hourly_rate_cents: int = 5000,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> HostProfile:
        """Create a new host profile.

        Args:
            user_id: The UUID of the user becoming a host.
            bio: Optional biography text.
            headline: Optional short tagline.
            hourly_rate_cents: Hourly rate in cents (default $50.00).
            latitude: Optional latitude for location.
            longitude: Optional longitude for location.

        Returns:
            The newly created HostProfile instance.
        """
        # Create location from lat/lng if provided
        location = None
        if latitude is not None and longitude is not None:
            # PostGIS uses longitude, latitude order (x, y)
            location = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)

        profile = HostProfile(
            user_id=str(user_id),
            bio=bio,
            headline=headline,
            hourly_rate_cents=hourly_rate_cents,
            location=location,
        )
        self._session.add(profile)
        await self._session.flush()
        return profile

    async def get_by_id(self, profile_id: UUID) -> HostProfile | None:
        """Get a host profile by its UUID.

        Args:
            profile_id: The profile's unique identifier.

        Returns:
            The HostProfile if found, None otherwise.
        """
        stmt = (
            select(HostProfile)
            .options(joinedload(HostProfile.user))
            .where(HostProfile.id == str(profile_id))
        )
        result = await self._session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_by_user_id(self, user_id: UUID) -> HostProfile | None:
        """Get a host profile by user ID.

        Args:
            user_id: The user's unique identifier.

        Returns:
            The HostProfile if found, None otherwise.
        """
        stmt = (
            select(HostProfile)
            .options(joinedload(HostProfile.user))
            .where(HostProfile.user_id == str(user_id))
        )
        result = await self._session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def update(
        self,
        profile_id: UUID,
        bio: str | None = None,
        headline: str | None = None,
        hourly_rate_cents: int | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        _update_location: bool = False,
    ) -> HostProfile | None:
        """Update a host profile's information.

        Args:
            profile_id: The profile's unique identifier.
            bio: New biography text (if provided).
            headline: New headline (if provided).
            hourly_rate_cents: New hourly rate (if provided).
            latitude: New latitude (if provided with _update_location=True).
            longitude: New longitude (if provided with _update_location=True).
            _update_location: If True, update location even if None (to clear it).

        Returns:
            The updated HostProfile if found, None if profile doesn't exist.
        """
        profile = await self.get_by_id(profile_id)
        if profile is None:
            return None

        if bio is not None:
            profile.bio = bio
        if headline is not None:
            profile.headline = headline
        if hourly_rate_cents is not None:
            profile.hourly_rate_cents = hourly_rate_cents

        # Update location if explicitly requested
        if _update_location:
            if latitude is not None and longitude is not None:
                profile.location = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
            else:
                profile.location = None

        await self._session.flush()
        return profile

    async def add_dance_style(
        self,
        profile_id: UUID,
        dance_style_id: UUID,
        skill_level: int = 3,
    ) -> HostDanceStyle | None:
        """Add a dance style to a host profile.

        Args:
            profile_id: The host profile's unique identifier.
            dance_style_id: The dance style's unique identifier.
            skill_level: Skill level 1-5 (default 3).

        Returns:
            The created HostDanceStyle junction record, or None if profile
            doesn't exist.

        Raises:
            ValueError: If skill_level is not between 1 and 5.
        """
        if not 1 <= skill_level <= 5:
            raise ValueError("skill_level must be between 1 and 5")

        # Verify profile exists
        profile = await self.get_by_id(profile_id)
        if profile is None:
            return None

        # Check if the dance style already exists for this profile
        existing = await self._get_host_dance_style(profile_id, dance_style_id)
        if existing is not None:
            # Update skill level if already exists
            existing.skill_level = skill_level
            await self._session.flush()
            return existing

        # Create new junction record
        host_dance_style = HostDanceStyle(
            host_profile_id=str(profile_id),
            dance_style_id=str(dance_style_id),
            skill_level=skill_level,
        )
        self._session.add(host_dance_style)
        await self._session.flush()
        return host_dance_style

    async def remove_dance_style(
        self,
        profile_id: UUID,
        dance_style_id: UUID,
    ) -> bool:
        """Remove a dance style from a host profile.

        Args:
            profile_id: The host profile's unique identifier.
            dance_style_id: The dance style's unique identifier.

        Returns:
            True if the dance style was removed, False if it wasn't found.
        """
        host_dance_style = await self._get_host_dance_style(profile_id, dance_style_id)
        if host_dance_style is None:
            return False

        await self._session.delete(host_dance_style)
        await self._session.flush()
        return True

    async def _get_host_dance_style(
        self,
        profile_id: UUID,
        dance_style_id: UUID,
    ) -> HostDanceStyle | None:
        """Get a specific host-dance style junction record.

        Args:
            profile_id: The host profile's unique identifier.
            dance_style_id: The dance style's unique identifier.

        Returns:
            The HostDanceStyle if found, None otherwise.
        """
        stmt = select(HostDanceStyle).where(
            and_(
                HostDanceStyle.host_profile_id == str(profile_id),
                HostDanceStyle.dance_style_id == str(dance_style_id),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_dance_styles(self, profile_id: UUID) -> list[HostDanceStyle]:
        """Get all dance styles for a host profile.

        Args:
            profile_id: The host profile's unique identifier.

        Returns:
            List of HostDanceStyle records for the profile.
        """
        stmt = (
            select(HostDanceStyle)
            .options(joinedload(HostDanceStyle.dance_style))
            .where(HostDanceStyle.host_profile_id == str(profile_id))
            .order_by(HostDanceStyle.skill_level.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.unique().scalars().all())

    async def get_nearby(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 10.0,
        limit: int = 20,
        offset: int = 0,
    ) -> list[tuple[HostProfile, float]]:
        """Get host profiles within a radius of a point.

        Uses PostGIS ST_DWithin for efficient geospatial queries.
        ST_DWithin uses meters for geography types.

        Args:
            latitude: Center point latitude.
            longitude: Center point longitude.
            radius_km: Search radius in kilometers (default 10km).
            limit: Maximum number of results.
            offset: Number of results to skip (for pagination).

        Returns:
            List of tuples (HostProfile, distance_km) ordered by distance.
        """
        # Create point from coordinates
        point = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)

        # Convert km to meters for ST_DWithin
        radius_meters = radius_km * 1000

        # Calculate distance in meters, convert to km
        distance_expr = ST_Distance(HostProfile.location, point) / 1000

        stmt = (
            select(HostProfile, distance_expr.label("distance_km"))
            .options(joinedload(HostProfile.user))
            .where(
                and_(
                    HostProfile.location.isnot(None),
                    ST_DWithin(HostProfile.location, point, radius_meters),
                )
            )
            .order_by(distance_expr)
            .limit(limit)
            .offset(offset)
        )

        result = await self._session.execute(stmt)
        return [(row.HostProfile, row.distance_km) for row in result.unique().all()]

    async def search(
        self,
        latitude: float | None = None,
        longitude: float | None = None,
        radius_km: float | None = None,
        style_ids: list[UUID] | None = None,
        min_rating: float | None = None,
        max_price_cents: int | None = None,
        order_by: str = "distance",
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[HostProfile], int]:
        """Search host profiles with multiple filters.

        Args:
            latitude: Center point latitude for location search.
            longitude: Center point longitude for location search.
            radius_km: Search radius in kilometers.
            style_ids: Filter by dance style UUIDs (hosts must have at least one).
            min_rating: Minimum average rating.
            max_price_cents: Maximum hourly rate in cents.
            order_by: Sort order - "distance", "rating", or "price".
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            Tuple of (list of HostProfile, total_count).
        """
        conditions = []

        # Location filter
        point = None
        if latitude is not None and longitude is not None:
            point = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
            if radius_km is not None:
                radius_meters = radius_km * 1000
                conditions.append(HostProfile.location.isnot(None))
                conditions.append(
                    ST_DWithin(HostProfile.location, point, radius_meters)
                )

        # Dance style filter
        if style_ids:
            # Get profile IDs that have at least one of the requested styles
            style_subquery = (
                select(HostDanceStyle.host_profile_id)
                .where(
                    HostDanceStyle.dance_style_id.in_([str(sid) for sid in style_ids])
                )
                .distinct()
            )
            conditions.append(HostProfile.id.in_(style_subquery))

        # Rating filter
        if min_rating is not None:
            conditions.append(HostProfile.rating_average >= min_rating)

        # Price filter
        if max_price_cents is not None:
            conditions.append(HostProfile.hourly_rate_cents <= max_price_cents)

        # Build base query
        base_query = select(HostProfile).options(joinedload(HostProfile.user))

        if conditions:
            base_query = base_query.where(and_(*conditions))

        # Determine ordering
        if order_by == "distance" and point is not None:
            distance_expr = ST_Distance(HostProfile.location, point)
            base_query = base_query.order_by(distance_expr)
        elif order_by == "rating":
            base_query = base_query.order_by(
                HostProfile.rating_average.desc().nulls_last()
            )
        elif order_by == "price":
            base_query = base_query.order_by(HostProfile.hourly_rate_cents.asc())
        else:
            # Default to created_at
            base_query = base_query.order_by(HostProfile.created_at.desc())

        # Get total count
        count_query = select(func.count(HostProfile.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await self._session.execute(count_query)
        total_count = count_result.scalar() or 0

        # Apply pagination
        base_query = base_query.limit(limit).offset(offset)

        # Execute main query
        result = await self._session.execute(base_query)
        profiles = list(result.unique().scalars().all())

        return profiles, total_count

    async def get_all_dance_styles(self) -> list[DanceStyle]:
        """Get all available dance styles.

        Returns:
            List of all DanceStyle records ordered by category and name.
        """
        stmt = select(DanceStyle).order_by(DanceStyle.category, DanceStyle.name)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_dance_style_by_id(self, dance_style_id: UUID) -> DanceStyle | None:
        """Get a dance style by ID.

        Args:
            dance_style_id: The dance style's unique identifier.

        Returns:
            The DanceStyle if found, None otherwise.
        """
        stmt = select(DanceStyle).where(DanceStyle.id == str(dance_style_id))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
