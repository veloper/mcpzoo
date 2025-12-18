"""Integration tests for deployment and configuration journeys."""

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


class TestServerConfigurationJourney:
    """Journey: Complex server configuration with tools and environment variables."""

    def test_configure_python_server(self, auth_token):
        """
        Journey: Configure a Python-based MCP server with specific dependencies.
        
        Steps:
        1. Create server with Python tool requirement
        2. Define environment variables
        3. Set up supervisord configuration with logging
        4. Verify all configuration is saved
        5. Sync to prepare deployment
        """
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        server = {
            "id": 200,
            "name": "python-mcp-server",
            "transport": "stdio",
            "command": "python -m mcp.server",
            "arguments": ["--host", "127.0.0.1"],
            "port": 8200,
            "supervisor_conf": {
                "name": "python-mcp-server",
                "command": "python -m mcp.server --host 127.0.0.1",
                "directory": "/app/servers/python-mcp-server",
                "autostart": True,
                "autorestart": "unexpected",
                "startsecs": 2,
                "startretries": 3,
                "stopsignal": "TERM",
                "stopwaitsecs": 10,
                "stdout_logfile": "/app/servers/python-mcp-server/stdout.log",
                "stdout_logfile_maxbytes": 10_000_000,
                "stdout_logfile_backups": 5,
                "stderr_logfile": "/app/servers/python-mcp-server/stderr.log",
                "stderr_logfile_maxbytes": 10_000_000,
                "stderr_logfile_backups": 5,
            },
            "tools": [
                {"name": "python", "version": "3.11"},
                {"name": "pip", "version": None},
            ],
            "envs": {
                "PYTHONUNBUFFERED": "1",
                "LOG_LEVEL": "INFO",
                "MCP_SERVER_NAME": "python-mcp-server",
                "MCP_SERVER_HOST": "127.0.0.1",
            },
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        
        # Step 1: Create server
        create_response = client.post("/api/servers", json=server, headers=headers)
        assert create_response.status_code == 201
        created = create_response.json()
        server_id = created["id"]
        
        # Step 2 & 3: Verify configuration
        assert created["transport"] == "stdio"
        assert created["supervisor_conf"]["directory"] == "/app/servers/python-mcp-server"
        assert len(created["tools"]) == 2
        assert len(created["envs"]) == 4
        
        # Step 4: Verify all configuration is saved
        get_response = client.get(f"/api/servers/{server_id}", headers=headers)
        assert get_response.status_code == 200
        retrieved = get_response.json()
        assert retrieved["supervisor_conf"]["stdout_logfile_maxbytes"] == 10_000_000
        assert retrieved["supervisor_conf"]["stdout_logfile_backups"] == 5
        
        # Step 5: Sync to prepare deployment
        sync_response = client.post("/api/servers/sync", headers=headers)
        assert sync_response.status_code == 200

    def test_configure_node_server(self, auth_token):
        """
        Journey: Configure a Node.js-based MCP server.
        
        Steps:
        1. Create server with Node.js tool requirement
        2. Define npm environment variables
        3. Configure for HTTP transport
        4. Verify configuration
        5. Sync deployment
        """
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        server = {
            "id": 201,
            "name": "node-mcp-server",
            "transport": "http",
            "url": "http://localhost:8201",
            "arguments": [],
            "port": 8201,
            "supervisor_conf": {
                "name": "node-mcp-server",
                "command": "node /app/servers/node-mcp-server/index.js",
                "directory": "/app/servers/node-mcp-server",
                "autostart": True,
                "autorestart": "unexpected",
            },
            "tools": [
                {"name": "node", "version": "18"},
                {"name": "npm", "version": None},
            ],
            "envs": {
                "NODE_ENV": "production",
                "PORT": "8201",
                "LOG_FORMAT": "json",
            },
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        
        # Step 1: Create server
        create_response = client.post("/api/servers", json=server, headers=headers)
        assert create_response.status_code == 201
        server_id = create_response.json()["id"]
        
        # Step 2: Verify environment variables
        get_response = client.get(f"/api/servers/{server_id}", headers=headers)
        assert get_response.status_code == 200
        retrieved = get_response.json()
        assert retrieved["envs"]["NODE_ENV"] == "production"
        assert retrieved["envs"]["PORT"] == "8201"
        
        # Step 3: Verify HTTP transport
        assert retrieved["transport"] == "http"
        assert retrieved["url"] == "http://localhost:8201"
        
        # Step 4: Sync
        sync_response = client.post("/api/servers/sync", headers=headers)
        assert sync_response.status_code == 200


class TestServerErrorHandlingJourney:
    """Journey: Error handling and edge cases."""

    def test_invalid_server_creation(self, auth_token):
        """
        Journey: Attempt to create server with invalid data.
        
        Expected: Server creation may succeed with defaults or fail with validation error.
        """
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Minimal server (API may use defaults)
        minimal_server = {
            "id": 300,
            "name": "minimal-server",
            # Missing some optional fields
        }
        
        response = client.post("/api/servers", json=minimal_server, headers=headers)
        # API may create with defaults or reject - either is acceptable
        assert response.status_code in [201, 400, 422]

    def test_duplicate_server_id(self, auth_token):
        """
        Journey: Attempt to create server with duplicate ID.
        
        Expected: Creation fails or overwrites (depending on implementation).
        """
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        server = {
            "id": 301,
            "name": "duplicate-test-1",
            "transport": "stdio",
            "command": "python -m test",
            "arguments": [],
            "port": 8301,
            "supervisor_conf": {"command": "python -m test"},
            "tools": [],
            "envs": {},
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        
        # Create first
        response1 = client.post("/api/servers", json=server, headers=headers)
        assert response1.status_code == 201
        
        # Try to create with same ID (may succeed with update behavior)
        server["name"] = "duplicate-test-2"
        response2 = client.post("/api/servers", json=server, headers=headers)
        # Should either fail or update existing
        assert response2.status_code in [201, 409]

    def test_get_nonexistent_server(self, auth_token):
        """
        Journey: Attempt to retrieve non-existent server.
        
        Expected: 404 Not Found.
        """
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = client.get("/api/servers/999999", headers=headers)
        assert response.status_code == 404

    def test_update_nonexistent_server(self, auth_token):
        """
        Journey: Attempt to update non-existent server.
        
        Expected: 404 Not Found.
        """
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        server = {
            "id": 999999,
            "name": "nonexistent",
            "transport": "stdio",
            "command": "python -m test",
            "arguments": [],
            "port": 9999,
            "supervisor_conf": {"command": "python -m test"},
            "tools": [],
            "envs": {},
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        
        response = client.put("/api/servers/999999", json=server, headers=headers)
        assert response.status_code == 404

    def test_delete_nonexistent_server(self, auth_token):
        """
        Journey: Attempt to delete non-existent server.
        
        Expected: 404 Not Found.
        """
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = client.delete("/api/servers/999999", headers=headers)
        assert response.status_code == 404


class TestConcurrentOperationsJourney:
    """Journey: Handling multiple concurrent operations."""

    def test_create_and_list_operations(self, auth_token):
        """
        Journey: Perform create and list operations in sequence.
        
        Steps:
        1. List servers (initial count)
        2. Create server
        3. List servers (count increased)
        4. Create another server
        5. List servers (count increased again)
        """
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Step 1: Initial list
        list1 = client.get("/api/servers", headers=headers)
        assert list1.status_code == 200
        count1 = len(list1.json())
        
        # Step 2: Create first
        server1 = {
            "id": 400,
            "name": "concurrent-1",
            "transport": "stdio",
            "command": "python -m test",
            "arguments": [],
            "port": 8400,
            "supervisor_conf": {"command": "python -m test"},
            "tools": [],
            "envs": {},
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        create1 = client.post("/api/servers", json=server1, headers=headers)
        assert create1.status_code == 201
        
        # Step 3: List again
        list2 = client.get("/api/servers", headers=headers)
        assert list2.status_code == 200
        count2 = len(list2.json())
        assert count2 == count1 + 1
        
        # Step 4: Create second
        server2 = {
            "id": 401,
            "name": "concurrent-2",
            "transport": "stdio",
            "command": "python -m test",
            "arguments": [],
            "port": 8401,
            "supervisor_conf": {"command": "python -m test"},
            "tools": [],
            "envs": {},
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        create2 = client.post("/api/servers", json=server2, headers=headers)
        assert create2.status_code == 201
        
        # Step 5: List again
        list3 = client.get("/api/servers", headers=headers)
        assert list3.status_code == 200
        count3 = len(list3.json())
        assert count3 == count2 + 1

    def test_update_while_syncing(self, auth_token):
        """
        Journey: Update server configuration and sync.
        
        Steps:
        1. Create server
        2. Update configuration
        3. Sync changes
        4. Verify latest configuration is synced
        """
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Step 1: Create
        server = {
            "id": 402,
            "name": "sync-update-test",
            "transport": "stdio",
            "command": "v1",
            "arguments": [],
            "port": 8402,
            "supervisor_conf": {"command": "v1"},
            "tools": [],
            "envs": {"VERSION": "1"},
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        create = client.post("/api/servers", json=server, headers=headers)
        assert create.status_code == 201
        server_id = create.json()["id"]
        
        # Step 2: Update
        get = client.get(f"/api/servers/{server_id}", headers=headers)
        current = get.json()
        current["command"] = "v2"
        current["envs"]["VERSION"] = "2"
        current["supervisor_conf"]["command"] = "v2"
        
        update = client.put(f"/api/servers/{server_id}", json=current, headers=headers)
        assert update.status_code == 200
        
        # Step 3: Sync
        sync = client.post("/api/servers/sync", headers=headers)
        assert sync.status_code == 200
        
        # Step 4: Verify
        verify = client.get(f"/api/servers/{server_id}", headers=headers)
        assert verify.status_code == 200
        assert verify.json()["command"] == "v2"
        assert verify.json()["envs"]["VERSION"] == "2"


class TestDataPersistenceJourney:
    """Journey: Verify data persists across operations."""

    def test_server_persistence(self, auth_token):
        """
        Journey: Verify server data persists after creation.
        
        Steps:
        1. Create server with specific details
        2. Retrieve immediately
        3. List all servers
        4. Retrieve again
        5. Verify details remain consistent
        """
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        server_data = {
            "id": 500,
            "name": "persistence-test",
            "transport": "stdio",
            "command": "python -m persistent",
            "arguments": ["arg1", "arg2"],
            "port": 8500,
            "supervisor_conf": {
                "command": "python -m persistent arg1 arg2",
                "directory": "/app/servers/persistent",
            },
            "tools": [
                {"name": "python", "version": "3.11"},
            ],
            "envs": {
                "PERSISTENT": "true",
                "DATA": "important",
            },
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        
        # Step 1: Create
        create = client.post("/api/servers", json=server_data, headers=headers)
        assert create.status_code == 201
        created = create.json()
        server_id = created["id"]
        
        # Step 2: Retrieve immediately
        get1 = client.get(f"/api/servers/{server_id}", headers=headers)
        assert get1.status_code == 200
        retrieved1 = get1.json()
        
        # Step 3: List all servers
        list_servers = client.get("/api/servers", headers=headers)
        assert list_servers.status_code == 200
        found_in_list = any(s["id"] == server_id for s in list_servers.json())
        assert found_in_list
        
        # Step 4: Retrieve again
        get2 = client.get(f"/api/servers/{server_id}", headers=headers)
        assert get2.status_code == 200
        retrieved2 = get2.json()
        
        # Step 5: Verify consistency
        assert retrieved1["name"] == retrieved2["name"] == server_data["name"]
        assert retrieved1["command"] == retrieved2["command"] == server_data["command"]
        assert retrieved1["arguments"] == retrieved2["arguments"] == server_data["arguments"]
        assert retrieved1["envs"]["PERSISTENT"] == retrieved2["envs"]["PERSISTENT"] == "true"
        assert retrieved1["tools"][0]["name"] == retrieved2["tools"][0]["name"] == "python"
