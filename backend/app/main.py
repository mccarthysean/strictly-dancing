"""Strictly Dancing FastAPI Application."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.routers import auth_router, users_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager."""
    settings = get_settings()
    logger = get_logger(__name__)

    logger.info(
        "application_started",
        app_name=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
    )
    yield
    logger.info("application_shutdown")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    # Configure logging
    configure_logging()

    app = FastAPI(
        title=settings.app_name,
        description="Global dance host marketplace API",
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )

    # CORS middleware configured from settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    # Include routers
    app.include_router(auth_router)
    app.include_router(users_router)

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy", "service": "strictly-dancing-api"}

    return app


app = create_app()
