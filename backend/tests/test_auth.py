"""Tests for authentication endpoints."""

import pytest
from fastapi.testclient import TestClient
from src.backend.main import app

client = TestClient(app)


def test_health_check():
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_login_success():
    """Test successful login."""
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "test-password-change-me"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login_failure():
    """Test failed login with wrong password."""
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "wrong"},
    )
    assert response.status_code == 401


def test_login_missing_fields():
    """Test login with missing username."""
    response = client.post(
        "/api/auth/login",
        json={"password": "test-password-change-me"},
    )
    assert response.status_code in [400, 422]


def test_verify_token():
    """Test token verification."""
    # First login
    login_response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "test-password-change-me"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Then verify
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/auth/verify", headers=headers)
    assert response.status_code == 200
    assert "username" in response.json()


def test_verify_invalid_token():
    """Test verification with invalid token."""
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/api/auth/verify", headers=headers)
    assert response.status_code in [401, 403]


def test_protected_endpoint_without_token():
    """Test accessing protected endpoint without token."""
    response = client.get("/api/servers")
    assert response.status_code == 403


def test_auth_workflow():
    """Test complete auth workflow."""
    # Login
    login_response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "test-password-change-me"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Verify
    headers = {"Authorization": f"Bearer {token}"}
    verify_response = client.get("/api/auth/verify", headers=headers)
    assert verify_response.status_code == 200
    
    # Access protected endpoint
    servers_response = client.get("/api/servers", headers=headers)
    assert servers_response.status_code == 200
