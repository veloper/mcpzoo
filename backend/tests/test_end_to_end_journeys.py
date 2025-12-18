"""
End-to-end integration test demonstrating complete MCPZoo workflows.

This test file showcases real-world usage scenarios and complete application journeys.
"""

import pytest
from fastapi.testclient import TestClient
from src.backend.main import app

client = TestClient(app)


@pytest.fixture
def authenticated_client():
    """Create an authenticated test client."""
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "test-password-change-me"},
    )
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    class AuthenticatedClient:
        def get(self, path):
            return client.get(path, headers=headers)
        
        def post(self, path, json=None):
            return client.post(path, json=json, headers=headers)
        
        def put(self, path, json=None):
            return client.put(path, json=json, headers=headers)
        
        def delete(self, path):
            return client.delete(path, headers=headers)
    
    return AuthenticatedClient()


class TestCompleteUserJourneys:
    """Real-world user journeys through the MCPZoo system."""

    def test_new_user_first_time_setup(self):
        """
        Scenario: A new user logs in for the first time and explores the system.
        
        Expected flow:
        1. Check system health
        2. Login with credentials
        3. View available servers
        4. View running processes
        5. Verify authentication works
        """
        # Step 1: System is healthy
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "healthy"
        
        # Step 2: User logs in
        login = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "test-password-change-me"}
        )
        assert login.status_code == 200
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 3: View available servers
        servers = client.get("/api/servers", headers=headers)
        assert servers.status_code == 200
        server_list = servers.json()
        assert isinstance(server_list, list)
        
        # Step 4: View running processes
        processes = client.get("/api/processes", headers=headers)
        assert processes.status_code == 200
        process_list = processes.json()
        assert isinstance(process_list, list)
        
        # Step 5: Verify authentication
        verify = client.get("/api/auth/verify", headers=headers)
        assert verify.status_code == 200
        assert verify.json()["username"] == "admin"

    def test_admin_deploys_python_mcp_server(self, authenticated_client):
        """
        Scenario: An admin user wants to deploy a Python MCP server.
        
        Expected flow:
        1. Create server configuration with Python requirements
        2. Configure supervisor settings
        3. Set up environment variables
        4. Deploy (sync) the server
        5. Verify deployment
        6. Check server is now available
        """
        # Step 1: Create server configuration
        python_server_config = {
            "id": 1001,
            "name": "python-mcp-llm",
            "transport": "stdio",
            "command": "python -m mcp.server.llm",
            "arguments": ["--host", "127.0.0.1", "--port", "8100"],
            "port": 8100,
            "supervisor_conf": {
                "name": "python-mcp-llm",
                "command": "python -m mcp.server.llm --host 127.0.0.1 --port 8100",
                "directory": "/app/servers/python-mcp-llm",
                "autostart": True,
                "autorestart": "unexpected",
                "startsecs": 3,
                "startretries": 3,
                "stopsignal": "TERM",
                "stopwaitsecs": 10,
                "stdout_logfile": "/app/servers/python-mcp-llm/stdout.log",
                "stdout_logfile_maxbytes": 10_000_000,
                "stdout_logfile_backups": 10,
                "stderr_logfile": "/app/servers/python-mcp-llm/stderr.log",
                "stderr_logfile_maxbytes": 10_000_000,
                "stderr_logfile_backups": 10,
                "redirect_stderr": False,
            },
            "tools": [
                {"name": "python", "version": "3.11"},
                {"name": "pip", "version": None},
            ],
            "envs": {
                "PYTHONUNBUFFERED": "1",
                "LOG_LEVEL": "INFO",
                "MCP_SERVER_HOST": "127.0.0.1",
                "MCP_SERVER_PORT": "8100",
            },
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        
        create = authenticated_client.post("/api/servers", python_server_config)
        assert create.status_code == 201
        server = create.json()
        server_id = server["id"]
        
        # Step 2: Verify configuration was saved
        get = authenticated_client.get(f"/api/servers/{server_id}")
        assert get.status_code == 200
        saved = get.json()
        assert saved["name"] == "python-mcp-llm"
        assert saved["transport"] == "stdio"
        assert saved["supervisor_conf"]["directory"] == "/app/servers/python-mcp-llm"
        
        # Step 3: Verify environment variables
        assert saved["envs"]["PYTHONUNBUFFERED"] == "1"
        assert saved["envs"]["LOG_LEVEL"] == "INFO"
        
        # Step 4: Deploy (sync)
        sync = authenticated_client.post("/api/servers/sync", None)
        assert sync.status_code == 200
        assert sync.json()["status"] == "success"
        
        # Step 5: Verify deployment
        verify = authenticated_client.get(f"/api/servers/{server_id}")
        assert verify.status_code == 200
        
        # Step 6: Verify server is in list
        servers = authenticated_client.get("/api/servers")
        assert servers.status_code == 200
        server_ids = [s["id"] for s in servers.json()]
        assert server_id in server_ids

    def test_admin_manages_multiple_servers_lifecycle(self, authenticated_client):
        """
        Scenario: An admin manages multiple MCP servers across their lifecycle.
        
        Expected flow:
        1. Create three different servers (Python, Node, Go)
        2. List all servers
        3. Verify all are present
        4. Update one server's configuration
        5. Sync all changes
        6. Delete one server
        7. Verify it's gone
        8. Final sync
        """
        servers_to_create = [
            {
                "id": 2001,
                "name": "mcp-python-tools",
                "transport": "stdio",
                "command": "python -m mcp.tools",
                "arguments": [],
                "port": 8100,
                "supervisor_conf": {"command": "python -m mcp.tools"},
                "tools": [{"name": "python", "version": "3.11"}],
                "envs": {"PYTHONUNBUFFERED": "1"},
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
            },
            {
                "id": 2002,
                "name": "mcp-node-api",
                "transport": "http",
                "url": "http://localhost:8101",
                "arguments": [],
                "port": 8101,
                "supervisor_conf": {"command": "node /app/servers/node-api/index.js"},
                "tools": [{"name": "node", "version": "18"}],
                "envs": {"NODE_ENV": "production"},
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
            },
            {
                "id": 2003,
                "name": "mcp-go-service",
                "transport": "stdio",
                "command": "go-mcp-service",
                "arguments": [],
                "port": 8102,
                "supervisor_conf": {"command": "go-mcp-service"},
                "tools": [{"name": "go", "version": "1.21"}],
                "envs": {"GO_ENV": "production"},
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
            },
        ]
        
        # Step 1: Create all servers
        created_ids = []
        for server_config in servers_to_create:
            create = authenticated_client.post("/api/servers", server_config)
            assert create.status_code == 201
            created_ids.append(create.json()["id"])
        
        # Step 2 & 3: List and verify all present
        servers = authenticated_client.get("/api/servers")
        assert servers.status_code == 200
        server_list = servers.json()
        for server_id in created_ids:
            assert any(s["id"] == server_id for s in server_list)
        
        # Step 4: Update one server
        python_server_id = created_ids[0]
        get = authenticated_client.get(f"/api/servers/{python_server_id}")
        server = get.json()
        server["envs"]["UPDATED"] = "true"
        update = authenticated_client.put(f"/api/servers/{python_server_id}", server)
        assert update.status_code == 200
        
        # Step 5: Sync all changes
        sync = authenticated_client.post("/api/servers/sync", None)
        assert sync.status_code == 200
        
        # Step 6: Delete one server
        delete = authenticated_client.delete(f"/api/servers/{created_ids[1]}")
        assert delete.status_code == 204
        
        # Step 7: Verify it's gone
        get = authenticated_client.get(f"/api/servers/{created_ids[1]}")
        assert get.status_code == 404
        
        # Step 8: Final sync
        final_sync = authenticated_client.post("/api/servers/sync", None)
        assert final_sync.status_code == 200

    def test_user_discovers_and_uses_api(self, authenticated_client):
        """
        Scenario: A user discovers what they can do with the API.
        
        Expected flow:
        1. Check what endpoints exist
        2. Get list of servers
        3. Create a new server
        4. Retrieve it by ID
        5. Update its configuration
        6. Get updated version
        7. List all to confirm
        8. Delete it
        9. Confirm deletion
        """
        # Step 1: Discover endpoints by trying basic operations
        
        # Step 2: Get list of servers
        list_response = authenticated_client.get("/api/servers")
        assert list_response.status_code == 200
        initial_count = len(list_response.json())
        
        # Step 3: Create a new server
        new_server = {
            "id": 3001,
            "name": "test-discovery-server",
            "transport": "stdio",
            "command": "echo 'test'",
            "arguments": [],
            "port": 8100,
            "supervisor_conf": {"command": "echo 'test'"},
            "tools": [],
            "envs": {"TEST": "true"},
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        create = authenticated_client.post("/api/servers", new_server)
        assert create.status_code == 201
        created = create.json()
        server_id = created["id"]
        
        # Step 4: Retrieve by ID
        get = authenticated_client.get(f"/api/servers/{server_id}")
        assert get.status_code == 200
        assert get.json()["name"] == "test-discovery-server"
        
        # Step 5: Update configuration
        to_update = get.json()
        to_update["envs"]["UPDATED"] = "yes"
        update = authenticated_client.put(f"/api/servers/{server_id}", to_update)
        assert update.status_code == 200
        
        # Step 6: Get updated version
        updated_get = authenticated_client.get(f"/api/servers/{server_id}")
        assert updated_get.status_code == 200
        assert updated_get.json()["envs"]["UPDATED"] == "yes"
        
        # Step 7: List all
        final_list = authenticated_client.get("/api/servers")
        assert final_list.status_code == 200
        assert len(final_list.json()) == initial_count + 1
        
        # Step 8: Delete it
        delete = authenticated_client.delete(f"/api/servers/{server_id}")
        assert delete.status_code == 204
        
        # Step 9: Confirm deletion
        final_get = authenticated_client.get(f"/api/servers/{server_id}")
        assert final_get.status_code == 404

    def test_operator_monitors_system(self, authenticated_client):
        """
        Scenario: An operator monitors the system and performs maintenance.
        
        Expected flow:
        1. Check system health
        2. Get list of running processes
        3. Get status of each process
        4. Create a new server for monitoring
        5. Sync new configuration
        6. Verify process list updates
        """
        # Step 1: Check health
        health = client.get("/health")
        assert health.status_code == 200
        
        # Step 2: Get process list
        processes = authenticated_client.get("/api/processes")
        assert processes.status_code == 200
        process_list = processes.json()
        
        # Step 3: Get status of first process if available
        if process_list:
            first_process = process_list[0]["config"]["name"]
            status = authenticated_client.get(f"/api/processes/{first_process}/status")
            assert status.status_code == 200
        
        # Step 4: Create monitoring server
        monitor_server = {
            "id": 4001,
            "name": "mcp-monitor",
            "transport": "stdio",
            "command": "python -m mcp.monitor",
            "arguments": [],
            "port": 8100,
            "supervisor_conf": {"command": "python -m mcp.monitor"},
            "tools": [],
            "envs": {"MONITORING": "true"},
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        create = authenticated_client.post("/api/servers", monitor_server)
        assert create.status_code == 201
        
        # Step 5: Sync new configuration
        sync = authenticated_client.post("/api/servers/sync", None)
        assert sync.status_code == 200
        
        # Step 6: Verify server is now available
        servers = authenticated_client.get("/api/servers")
        assert servers.status_code == 200
        monitor_id = create.json()["id"]
        assert any(s["id"] == monitor_id for s in servers.json())
