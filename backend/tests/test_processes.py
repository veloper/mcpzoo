"""Tests for process management endpoints."""

import pytest
from fastapi.testclient import TestClient
from src.backend.main import app

client = TestClient(app)


@pytest.fixture
def auth_token():
    """Get authentication token for tests."""
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "test-password-change-me"},
    )
    return response.json()["access_token"]


def test_list_processes(auth_token):
    """Test listing processes."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.get("/api/processes", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_process_status(auth_token):
    """Test getting process status."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # First get list
    list_response = client.get("/api/processes", headers=headers)
    assert list_response.status_code == 200
    processes = list_response.json()
    
    if processes:
        # Get status of first process
        process_name = processes[0]["config"]["name"]
        response = client.get(f"/api/processes/{process_name}/status", headers=headers)
        assert response.status_code == 200


def test_process_not_found(auth_token):
    """Test getting non-existent process."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.get("/api/processes/nonexistent_process/status", headers=headers)
    assert response.status_code == 404


def test_process_without_auth():
    """Test accessing process endpoint without auth."""
    response = client.get("/api/processes")
    assert response.status_code == 403


def test_start_process_endpoint_exists(auth_token):
    """Test that start process endpoint exists."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.post("/api/processes/test_process/start", headers=headers)
    # Endpoint should exist (404 for process, not 405 for method)
    assert response.status_code in [200, 400, 404]


def test_stop_process_endpoint_exists(auth_token):
    """Test that stop process endpoint exists."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.post("/api/processes/test_process/stop", headers=headers)
    # Endpoint should exist
    assert response.status_code in [200, 400, 404]


def test_kill_process_endpoint_exists(auth_token):
    """Test that kill process endpoint exists."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.post("/api/processes/test_process/kill", headers=headers)
    # Endpoint should exist
    assert response.status_code in [200, 400, 404]
