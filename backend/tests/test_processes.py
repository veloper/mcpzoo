"""Tests for process management endpoints."""

import pytest
from fastapi.testclient import TestClient
from src.backend.main import app


client = TestClient(app)


@pytest.fixture
def auth_headers():
    """Get authentication headers for tests."""
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "test-password-change-me"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_get_processes(auth_headers):
    """Test getting current processes."""
    response = client.get("/api/processes", headers=auth_headers)
    assert response.status_code == 200
    processes = response.json()
    assert isinstance(processes, list)
    # Should return list of process objects
    if processes:
        process = processes[0]
        assert "pid" in process
        assert "name" in process
        assert "command" in process
        assert "state" in process


def test_get_process_tree(auth_headers):
    """Test getting process tree."""
    response = client.get("/api/processes/tree", headers=auth_headers)
    assert response.status_code == 200
    processes = response.json()
    assert isinstance(processes, list)
    # Should return list of process objects (same as get_processes)
    if processes:
        process = processes[0]
        assert "pid" in process
        assert "name" in process
        assert "command" in process
        assert "state" in process


def test_get_processes_without_auth():
    """Test getting processes without authentication."""
    response = client.get("/api/processes")
    assert response.status_code == 403


def test_get_process_tree_without_auth():
    """Test getting process tree without authentication."""
    response = client.get("/api/processes/tree")
    assert response.status_code == 403


def test_processes_return_consistent_data():
    """Test that both endpoints return the same data structure."""
    auth_headers = {"Authorization": f"Bearer {client.post('/api/auth/login', json={'username': 'admin', 'password': 'test-password-change-me'}).json()['access_token']}"}

    response1 = client.get("/api/processes", headers=auth_headers)
    response2 = client.get("/api/processes/tree", headers=auth_headers)

    assert response1.status_code == 200
    assert response2.status_code == 200

    processes1 = response1.json()
    processes2 = response2.json()

    # Both should return the same data
    assert processes1 == processes2