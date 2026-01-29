"""API routers package."""

from app.routers.auth import router as auth_router
from app.routers.bookings import router as bookings_router
from app.routers.hosts import router as hosts_router
from app.routers.messaging import router as messaging_router
from app.routers.push import router as push_router
from app.routers.reviews import router as reviews_router
from app.routers.tasks import router as tasks_router
from app.routers.users import router as users_router
from app.routers.websocket import router as websocket_router

__all__ = [
    "auth_router",
    "bookings_router",
    "hosts_router",
    "messaging_router",
    "push_router",
    "reviews_router",
    "tasks_router",
    "users_router",
    "websocket_router",
]
