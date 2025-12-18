"""Pytest configuration for backend tests."""

import os
import pytest

# Set test environment BEFORE importing anything from backend
os.environ['APP_ENV'] = 'test'

from src.backend.environment import set_env
from fastapi.testclient import TestClient
from src.backend.main import app
from src.backend.services.database import get_database_service
from src.backend.services.supervisord import get_supervisord_service
from src.backend.services.processes import get_processes_service
from tests.test_services import InMemoryDatabaseService, MockSupervisordService, MockProcessesService

# Ensure test environment is set
set_env('test')


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Session-scoped setup to ensure test environment is active."""
    os.environ['APP_ENV'] = 'test'
    set_env('test')
    yield


@pytest.fixture(scope="session", autouse=True)
def override_dependencies():
    """Override dependencies for all tests."""
    test_db_service = InMemoryDatabaseService()
    test_supervisord_service = MockSupervisordService()
    test_processes_service = MockProcessesService()
    
    # Override dependencies for entire session
    app.dependency_overrides[get_database_service] = lambda: test_db_service
    app.dependency_overrides[get_supervisord_service] = lambda: test_supervisord_service
    app.dependency_overrides[get_processes_service] = lambda: test_processes_service
    
    yield
    
    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    """Provide a TestClient for all tests."""
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """Provide authentication headers for a test user."""
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "test-password-change-me"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def authenticated_client(client, auth_headers):
    """Provide a TestClient with pre-configured authentication."""
    client.headers = auth_headers
    return client
