"""Tests for home endpoint."""

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


def test_home_endpoint(auth_headers):
    """Test home endpoint returns expected structure."""
    response = client.get("/home", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    # Check top-level structure
    assert "name" in data
    assert "version" in data
    assert "description" in data
    assert "summary" in data
    assert "servers" in data
    assert "processes" in data

    # Check summary structure
    summary = data["summary"]
    assert "total_servers" in summary
    assert "running_processes" in summary
    assert "total_processes" in summary

    # Check data types
    assert isinstance(data["name"], str)
    assert isinstance(data["version"], str)
    assert isinstance(data["description"], str)
    assert isinstance(summary["total_servers"], int)
    assert isinstance(summary["running_processes"], int)
    assert isinstance(summary["total_processes"], int)
    assert isinstance(data["servers"], list)
    assert isinstance(data["processes"], list)


def test_home_endpoint_with_servers(auth_headers):
    """Test home endpoint with servers in database."""
    # Create a test server
    server_data = {
        "id": "test-server-home",
        "name": "test-server-home",
        "transport": "stdio",
        "command": "python -m test",
        "arguments": [],
        "port": 8105,
        "tools": [],
        "envs": {},
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }

    # Create the server
    client.post("/api/servers", json=server_data, headers=auth_headers)

    # Get home data
    response = client.get("/home", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    # Should have at least one server
    assert data["summary"]["total_servers"] >= 1
    assert len(data["servers"]) >= 1

    # Check that our server is in the list
    server_names = [s["name"] for s in data["servers"]]
    assert "test-server-home" in server_names


def test_home_endpoint_with_processes(auth_headers):
    """Test home endpoint with processes in supervisor."""
    # Add a test process to the mock supervisor
    from src.backend.services.supervisor import get_supervisor_service
    from src.backend.supervisor import SupervisorProcessState
    mock_service = app.dependency_overrides[get_supervisor_service]()
    mock_service.add_process("test-process-home", state=SupervisorProcessState.RUNNING)

    # Get home data
    response = client.get("/home", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    # Should have at least one process
    assert data["summary"]["total_processes"] >= 1
    assert len(data["processes"]) >= 1

    # Check that our process is in the list
    process_names = [p["name"] for p in data["processes"]]
    assert "test-process-home" in process_names


def test_home_endpoint_without_auth():
    """Test home endpoint without authentication."""
    response = client.get("/home")
    assert response.status_code == 200  # Should be accessible without auth


def test_home_endpoint_structure_consistency(auth_headers):
    """Test that home endpoint returns consistent structure."""
    # Get home data multiple times
    responses = []
    for _ in range(3):
        response = client.get("/home", headers=auth_headers)
        assert response.status_code == 200
        responses.append(response.json())

    # All responses should have the same structure
    keys = set(responses[0].keys())
    for response in responses[1:]:
        assert set(response.keys()) == keys

    # Summary should have consistent structure
    summaries = [r["summary"] for r in responses]
    summary_keys = set(summaries[0].keys())
    for summary in summaries[1:]:
        assert set(summary.keys()) == summary_keys


def test_home_endpoint_empty_state(auth_headers):
    """Test home endpoint with no servers or processes."""
    # Clear any existing data from previous tests
    from src.backend.services.database import get_database_service
    test_db_service = app.dependency_overrides[get_database_service]()
    test_db_service.get_db().clear_all()

    # Clear supervisor processes
    from src.backend.services.supervisor import get_supervisor_service
    mock_service = app.dependency_overrides[get_supervisor_service]()
    mock_service.clear_all_processes()

    # Get home data with clean state
    response = client.get("/home")
    assert response.status_code == 200
    data = response.json()

    # Should have zero servers and processes initially
    assert data["summary"]["total_servers"] == 0
    assert data["summary"]["running_processes"] == 0
    assert data["summary"]["total_processes"] == 0
    assert len(data["servers"]) == 0
    assert len(data["processes"]) == 0


def test_home_endpoint_metadata(auth_headers):
    """Test that home endpoint returns correct metadata."""
    response = client.get("/home", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert data["name"] == "MCPZoo"
    assert data["version"] == "0.1.0"
    assert data["description"] == "MCP Server Management"