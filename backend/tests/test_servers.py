"""Tests for server management endpoints."""

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


def test_list_servers(auth_token):
    """Test listing servers."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.get("/api/servers", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_server(auth_token):
    """Test creating a server."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    server_data = {
        "id": "test-server-create-999",
        "name": "test-server-create",
        "transport": "stdio",
        "command": "python -m test",
        "arguments": "[]",
        "port": 8100,
        "tools": "[]",
        "envs": "{}",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }
    response = client.post(
        "/api/servers",
        json=server_data,
        headers=headers
    )
    assert response.status_code == 201
    assert response.json()["name"] == "test-server-create"


def test_get_server(auth_token):
    """Test getting a specific server."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # First create
    server_data = {
        "id": "test-server-get-998",
        "name": "test-server-get",
        "transport": "stdio",
        "command": "python -m test",
        "arguments": "[]",
        "port": 8101,
        "tools": "[]",
        "envs": "{}",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }
    create_response = client.post("/api/servers", json=server_data, headers=headers)
    assert create_response.status_code == 201
    server_id = create_response.json()["id"]
    
    # Then get
    response = client.get(f"/api/servers/{server_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "test-server-get"


def test_update_server(auth_token):
    """Test updating a server."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Create
    server_data = {
        "id": "test-server-update-997",
        "name": "test-server-update",
        "transport": "stdio",
        "command": "python -m test",
        "arguments": "[]",
        "port": 8102,
        "tools": "[]",
        "envs": "{}",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }
    create_response = client.post("/api/servers", json=server_data, headers=headers)
    server_id = create_response.json()["id"]
    
    # Update
    update_data = {**server_data, "id": server_id, "name": "test-server-updated"}
    response = client.put(f"/api/servers/{server_id}", json=update_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "test-server-updated"


def test_delete_server(auth_token):
    """Test deleting a server."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Create
    server_data = {
        "id": "test-server-delete-996",
        "name": "test-server-delete",
        "transport": "stdio",
        "command": "python -m test",
        "arguments": "[]",
        "port": 8103,
        "tools": "[]",
        "envs": "{}",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }
    create_response = client.post("/api/servers", json=server_data, headers=headers)
    server_id = create_response.json()["id"]
    
    # Delete
    response = client.delete(f"/api/servers/{server_id}", headers=headers)
    assert response.status_code == 204
    
    # Verify deleted
    get_response = client.get(f"/api/servers/{server_id}", headers=headers)
    assert get_response.status_code == 404


def test_server_not_found(auth_token):
    """Test getting non-existent server."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.get("/api/servers/999999", headers=headers)
    assert response.status_code == 404


def test_sync_servers(auth_token):
    """Test syncing servers."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.post("/api/servers/sync", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
