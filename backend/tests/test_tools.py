"""Tests for tools endpoints."""

import pytest
from fastapi.testclient import TestClient
from src.backend.main import app
from src.backend.services.mise import get_mise_service


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


def test_check_mise_tool_available(auth_headers):
    """Test checking an available tool."""
    response = client.get("/api/tools/mise/check/node", headers=auth_headers)
    assert response.status_code == 200
    result = response.json()
    assert result["available"] == True
    assert result["tool"] == "node"
    assert "latest_version" in result


def test_check_mise_tool_with_version(auth_headers):
    """Test checking a tool with specific version."""
    response = client.get("/api/tools/mise/check/python:3.12.3", headers=auth_headers)
    assert response.status_code == 200
    result = response.json()
    assert result["available"] == True
    assert result["tool"] == "python"
    assert result["version"] == "3.12.3"
    assert result["latest_version"] == "3.12.3"


def test_check_mise_tool_unavailable_version(auth_headers):
    """Test checking a tool with unavailable version."""
    response = client.get("/api/tools/mise/check/python:99.0.0", headers=auth_headers)
    assert response.status_code == 200
    result = response.json()
    assert result["available"] == False
    assert result["tool"] == "python"
    assert result["version"] == "99.0.0"
    assert "not found" in result["error"]


def test_check_mise_tool_not_found(auth_headers):
    """Test checking a non-existent tool."""
    response = client.get("/api/tools/mise/check/non-existent-tool", headers=auth_headers)
    assert response.status_code == 200
    result = response.json()
    assert result["available"] == False
    assert result["tool"] == "non-existent-tool"
    assert "Tool not found" in result["error"]


def test_check_mise_tool_unavailable(auth_headers):
    """Test checking a configured unavailable tool."""
    response = client.get("/api/tools/mise/check/unavailable-tool", headers=auth_headers)
    assert response.status_code == 200
    result = response.json()
    assert result["available"] == False
    assert result["tool"] == "unavailable-tool"
    assert "Tool not found" in result["error"]


def test_get_tool_versions_available(auth_headers):
    """Test getting versions for available tool."""
    response = client.get("/api/tools/mise/versions/node", headers=auth_headers)
    assert response.status_code == 200
    result = response.json()
    assert result["tool"] == "node"
    assert result["versions"] == ["20.12.0", "18.19.0", "16.20.2"]
    assert result["latest"] == "20.12.0"


def test_get_tool_versions_unavailable(auth_headers):
    """Test getting versions for unavailable tool."""
    response = client.get("/api/tools/mise/versions/unavailable-tool", headers=auth_headers)
    assert response.status_code == 200
    result = response.json()
    assert result["tool"] == "unavailable-tool"
    assert result["versions"] == []
    assert result["latest"] is None
    assert "Tool not found" in result["error"]


def test_get_tool_versions_not_found(auth_headers):
    """Test getting versions for non-existent tool."""
    response = client.get("/api/tools/mise/versions/non-existent-tool", headers=auth_headers)
    assert response.status_code == 200
    result = response.json()
    assert result["tool"] == "non-existent-tool"
    assert result["versions"] == []
    assert result["latest"] is None
    assert "Tool not found" in result["error"]


def test_tools_without_auth():
    """Test tools endpoints without authentication."""
    # Test check tool without auth - should work since no auth required
    response = client.get("/api/tools/mise/check/node")
    assert response.status_code == 200

    # Test get versions without auth - should work since no auth required
    response = client.get("/api/tools/mise/versions/node")
    assert response.status_code == 200


def test_check_mise_tool_various_tools(auth_headers):
    """Test checking various tools."""
    tools_to_test = ["python", "go", "rust"]
    for tool in tools_to_test:
        response = client.get(f"/api/tools/mise/check/{tool}", headers=auth_headers)
        assert response.status_code == 200
        result = response.json()
        assert result["available"] == True
        assert result["tool"] == tool
        assert "latest_version" in result
        assert len(result["latest_version"]) > 0