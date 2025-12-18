# Phase 038: Tests and Verification

## Objective

Implement tests and provide comprehensive verification checklist for the entire backend implementation.

## Prerequisites

- All phases 030-037 completed
- Backend application functional

## Steps

### 3.1: Create Tests

Create `backend/tests/test_auth.py`:

```python
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_check():
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_login_success():
    """Test successful login."""
    # Note: use actual credentials from .env
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "changeme123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_failure():
    """Test failed login."""
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "wrong"},
    )
    assert response.status_code == 401
```

Create `backend/tests/test_servers.py`:

```python
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


@pytest.fixture
def auth_token():
    """Get authentication token for tests."""
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "changeme123"},
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
        "name": "test-server",
        "transport": "http",
        "url": "http://localhost:8100",
        "port": 8100,
        "supervisor_conf": {
            "name": "mcp_test",
            "command": "python -m test",
        },
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }
    response = client.post(
        "/api/servers",
        json=server_data,
        headers=headers
    )
    assert response.status_code == 201
    assert response.json()["name"] == "test-server"
```

Create `backend/tests/test_processes.py`:

```python
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


@pytest.fixture
def auth_token():
    """Get authentication token for tests."""
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "changeme123"},
    )
    return response.json()["access_token"]


def test_list_processes(auth_token):
    """Test listing processes."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.get("/api/processes", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), dict)
```

---

## Verification Checklist

### Phase 030: Settings and Models
- [ ] `backend/src/backend/settings.py` exists
- [ ] Settings loads APP_USERNAME and APP_PASSWORD from .env
- [ ] Settings fails if required fields missing
- [ ] `backend/src/backend/models.py` exists
- [ ] All Pydantic models validate correctly

### Phase 031: Authentication
- [ ] `backend/src/backend/auth.py` exists
- [ ] `backend/src/backend/routers/auth.py` exists
- [ ] JWT token creation works
- [ ] Token verification works
- [ ] User authentication works against configured credentials
- [ ] `/api/auth/login` endpoint exists
- [ ] `/api/auth/logout` endpoint exists
- [ ] `/api/auth/verify` endpoint exists

### Phase 032: Database Wrapper
- [ ] `backend/src/backend/tinydb.py` exists
- [ ] Database initializes without errors
- [ ] Server insert operation works
- [ ] Server retrieve operation works
- [ ] Server update operation works
- [ ] Server delete operation works
- [ ] Database file created at configured path

### Phase 033: Supervisor API
- [ ] `backend/src/backend/supervisor_api.py` exists
- [ ] SupervisorAPI class initializes
- [ ] supervisorctl status command works
- [ ] supervisorctl start/stop commands work

### Phase 034: Sync and Deployment
- [ ] `backend/src/backend/sync_processes.py` exists
- [ ] Sync function creates server directories
- [ ] .mise.toml generation works
- [ ] Supervisord config generation works

### Phase 035: Server Routes
- [ ] `backend/src/backend/routers/servers.py` exists
- [ ] GET /api/servers endpoint works
- [ ] POST /api/servers endpoint works
- [ ] GET /api/servers/{id} endpoint works
- [ ] PUT /api/servers/{id} endpoint works
- [ ] DELETE /api/servers/{id} endpoint works
- [ ] GET /api/servers/{id}/logs endpoint works
- [ ] POST /api/servers/sync endpoint works
- [ ] All endpoints require authentication

### Phase 036: Process Routes
- [ ] `backend/src/backend/routers/processes.py` exists
- [ ] GET /api/processes endpoint works
- [ ] POST /api/processes/{name}/start endpoint works
- [ ] POST /api/processes/{name}/stop endpoint works
- [ ] GET /api/processes/{name}/status endpoint works
- [ ] All endpoints require authentication

### Phase 037: Main App and Utilities
- [ ] `backend/src/backend/utils/shell.py` exists
- [ ] `backend/src/backend/utils/logging.py` exists
- [ ] `backend/src/backend/routers/__init__.py` exists
- [ ] `backend/src/backend/utils/__init__.py` exists
- [ ] `backend/src/backend/main.py` exists
- [ ] `uvicorn backend.main:app` runs without errors
- [ ] GET /health endpoint returns `{"status": "healthy"}`
- [ ] GET /home endpoint returns metadata

### Phase 038: Tests
- [ ] `backend/tests/test_auth.py` exists
- [ ] `backend/tests/test_servers.py` exists
- [ ] `backend/tests/test_processes.py` exists
- [ ] Tests run without errors
- [ ] Health check test passes
- [ ] Authentication tests pass

## Summary

All core backend components are now implemented:
- Configuration and models
- JWT authentication with rolling window
- TinyDB database wrapper
- Supervisor process control API
- Server configuration sync and deployment
- RESTful API endpoints with authentication
- Logging and utilities
- Comprehensive test suite

## Next Steps

Once all verification checks pass, proceed to:
1. Phase 100: Frontend Implementation
2. Phase 200: Container Configuration
3. Phase 300: Integration and Docs
