"""Pytest configuration for backend tests."""

import os

import pytest

from fastapi.testclient import TestClient
from src.backend.environment import set_env
from src.backend.main import app
from src.backend.services.database import get_database_service
from src.backend.services.mise import get_mise_service
from src.backend.services.port_manager import PortManagerService, get_port_manager_service
from src.backend.services.processes import get_processes_service
from src.backend.services.supervisor import get_supervisor_service
from src.backend.services.sync import get_sync_service
from tests.test_services import InMemoryDatabaseService, MockMiseService, MockProcessesService, MockSupervisordService, MockSyncService


# Set test environment BEFORE importing anything from backend
os.environ['APP_ENV'] = 'test'


# Ensure test environment is set
set_env('test')


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Session-scoped setup to ensure test environment is active."""
    # Import here to avoid issues with caching
    from src.backend.settings import clear_settings_cache

    # Clear any cached settings
    clear_settings_cache()

    os.environ['APP_ENV'] = 'test'
    os.environ['APP_USERNAME'] = 'admin'
    os.environ['APP_PASSWORD'] = 'test-password-change-me'
    set_env('test')
    yield


@pytest.fixture(scope="session", autouse=True)
def override_dependencies():
    """Override dependencies for all tests."""
    test_db_service = InMemoryDatabaseService()
    test_supervisord_service = MockSupervisordService()
    test_processes_service = MockProcessesService()
    test_sync_service = MockSyncService()
    test_mise_service = MockMiseService()

    # Create PortManagerService with proper initialization (no logger dependency)
    test_port_manager_service = PortManagerService(
        db_service=test_db_service
    )

    # Override dependencies for entire session
    app.dependency_overrides[get_database_service] = lambda: test_db_service
    app.dependency_overrides[get_supervisor_service] = lambda: test_supervisord_service
    app.dependency_overrides[get_processes_service] = lambda: test_processes_service
    app.dependency_overrides[get_port_manager_service] = lambda: test_port_manager_service
    app.dependency_overrides[get_mise_service] = lambda: test_mise_service
    app.dependency_overrides[get_sync_service] = lambda: test_sync_service

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
