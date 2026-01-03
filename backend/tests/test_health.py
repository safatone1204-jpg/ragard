"""Tests for health check endpoint."""
from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient):
    """Test that health endpoint returns 200."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "checks" in data

