"""Strictly Dancing FastAPI Application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Strictly Dancing API",
        description="Global dance host marketplace API",
        version="0.1.0",
    )

    # CORS middleware will be configured in T002
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5175"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy", "service": "strictly-dancing-api"}

    return app


app = create_app()
