"""Pytest fixtures for Strictly Dancing backend tests."""
import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def app():
    """Create a test FastAPI application."""
    return create_app()


@pytest.fixture
def client(app):
    """Create a test client for the FastAPI application."""
    return TestClient(app)
