"""Tests for health endpoint."""


def test_health_endpoint_returns_200(client):
    """Test that the health endpoint returns HTTP 200 status."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_endpoint_returns_json(client):
    """Test that the health endpoint returns valid JSON with expected structure."""
    response = client.get("/health")
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"
    assert "service" in data
    assert data["service"] == "strictly-dancing-api"
