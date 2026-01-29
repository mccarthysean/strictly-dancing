"""API routers package."""

from app.routers.auth import router as auth_router
from app.routers.bookings import router as bookings_router
from app.routers.hosts import router as hosts_router
from app.routers.users import router as users_router

__all__ = ["auth_router", "bookings_router", "hosts_router", "users_router"]
