"""Integration tests for complete server lifecycle journeys."""

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


class TestServerLifecycleJourney:
    """Journey: Create, configure, deploy, and manage an MCP server."""

    def test_complete_server_setup_journey(self, auth_token):
        """
        Journey: A user wants to add a new MCP server.
        
        Steps:
        1. User logs in (already done via fixture)
        2. User checks existing servers
        3. User creates a new server with stdio transport
        4. User verifies the server was created
        5. User can retrieve server details
        6. User syncs servers to deploy
        7. User verifies sync was successful
        """
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Step 2: Check existing servers
        list_response = client.get("/api/servers", headers=headers)
        assert list_response.status_code == 200
        initial_count = len(list_response.json())
        
        # Step 3: Create new server
        new_server = {
            "id": 100,
            "name": "test-mcp-stdio",
            "transport": "stdio",
            "command": "python -m mcp_server",
            "arguments": ["--config", "config.json"],
            "port": 8100,
            "supervisor_conf": {
                "command": "python -m mcp_server --config config.json",
                "directory": "/app/servers/test-mcp-stdio",
                "autostart": True,
                "autorestart": "unexpected",
                "stdout_logfile": "/app/servers/test-mcp-stdio/stdout.log",
                "stderr_logfile": "/app/servers/test-mcp-stdio/stderr.log",
            },
            "tools": [
                {"name": "python", "version": "3.11"},
            ],
            "envs": {
                "PYTHONUNBUFFERED": "1",
                "LOG_LEVEL": "DEBUG",
            },
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        
        create_response = client.post(
            "/api/servers",
            json=new_server,
            headers=headers
        )
        assert create_response.status_code == 201
        created_server = create_response.json()
        server_id = created_server["id"]
        
        # Step 4: Verify server was created
        list_response = client.get("/api/servers", headers=headers)
        assert list_response.status_code == 200
        assert len(list_response.json()) == initial_count + 1
        
        # Step 5: Retrieve server details
        get_response = client.get(f"/api/servers/{server_id}", headers=headers)
        assert get_response.status_code == 200
        retrieved_server = get_response.json()
        assert retrieved_server["name"] == "test-mcp-stdio"
        assert retrieved_server["transport"] == "stdio"
        assert retrieved_server["command"] == "python -m mcp_server"
        
        # Step 6: Sync servers to deploy
        sync_response = client.post("/api/servers/sync", headers=headers)
        assert sync_response.status_code == 200
        assert sync_response.json()["status"] == "success"
        
        # Step 7: Verify sync was successful
        # Check that server still exists after sync
        final_get = client.get(f"/api/servers/{server_id}", headers=headers)
        assert final_get.status_code == 200

    def test_server_update_journey(self, auth_token):
        """
        Journey: A user wants to update an existing server configuration.
        
        Steps:
        1. Create a server
        2. Retrieve it
        3. Update server configuration
        4. Verify update was applied
        5. Sync to deploy changes
        """
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Step 1: Create initial server
        server = {
            "id": 101,
            "name": "update-test-server",
            "transport": "stdio",
            "command": "python -m old_server",
            "arguments": [],
            "port": 8101,
            "supervisor_conf": {
                "command": "python -m old_server",
            },
            "tools": [],
            "envs": {"VERSION": "1.0"},
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        create_response = client.post("/api/servers", json=server, headers=headers)
        assert create_response.status_code == 201
        server_id = create_response.json()["id"]
        
        # Step 2: Retrieve it
        get_response = client.get(f"/api/servers/{server_id}", headers=headers)
        assert get_response.status_code == 200
        original_server = get_response.json()
        
        # Step 3: Update server configuration
        updated_server = {
            **original_server,
            "command": "python -m new_server",
            "envs": {"VERSION": "2.0"},
        }
        updated_server["supervisor_conf"]["command"] = "python -m new_server"
        
        update_response = client.put(
            f"/api/servers/{server_id}",
            json=updated_server,
            headers=headers
        )
        assert update_response.status_code == 200
        
        # Step 4: Verify update was applied
        verify_response = client.get(f"/api/servers/{server_id}", headers=headers)
        assert verify_response.status_code == 200
        verified_server = verify_response.json()
        assert verified_server["command"] == "python -m new_server"
        assert verified_server["envs"]["VERSION"] == "2.0"
        
        # Step 5: Sync to deploy changes
        sync_response = client.post("/api/servers/sync", headers=headers)
        assert sync_response.status_code == 200

    def test_server_deletion_journey(self, auth_token):
        """
        Journey: A user wants to delete a server.
        
        Steps:
        1. Create a server
        2. Verify it exists
        3. Delete the server
        4. Verify it no longer exists
        5. Sync to update deployment
        """
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Step 1: Create a server
        server = {
            "id": 102,
            "name": "delete-test-server",
            "transport": "stdio",
            "command": "python -m test",
            "arguments": [],
            "port": 8102,
            "supervisor_conf": {"command": "python -m test"},
            "tools": [],
            "envs": {},
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        create_response = client.post("/api/servers", json=server, headers=headers)
        assert create_response.status_code == 201
        server_id = create_response.json()["id"]
        
        # Step 2: Verify it exists
        verify_response = client.get(f"/api/servers/{server_id}", headers=headers)
        assert verify_response.status_code == 200
        
        # Step 3: Delete the server
        delete_response = client.delete(f"/api/servers/{server_id}", headers=headers)
        assert delete_response.status_code == 204
        
        # Step 4: Verify it no longer exists
        not_found_response = client.get(f"/api/servers/{server_id}", headers=headers)
        assert not_found_response.status_code == 404
        
        # Step 5: Sync to update deployment
        sync_response = client.post("/api/servers/sync", headers=headers)
        assert sync_response.status_code == 200


class TestProcessManagementJourney:
    """Journey: Start, monitor, and stop MCP server processes."""

    def test_process_lifecycle_journey(self, auth_token):
        """
        Journey: A user wants to manage running processes.
        
        Steps:
        1. Check available processes
        2. Get status of a process (if available)
        3. Verify authentication is required
        """
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Step 1: Check available processes
        list_response = client.get("/api/processes", headers=headers)
        assert list_response.status_code == 200
        processes = list_response.json()
        assert isinstance(processes, list)
        
        # Step 2: Get status of a process (if any exist)
        if processes:
            process_name = processes[0]["config"]["name"]
            status_response = client.get(
                f"/api/processes/{process_name}/status",
                headers=headers
            )
            assert status_response.status_code == 200
    
    def test_unauthorized_process_access(self):
        """
        Journey: An unauthenticated user tries to access processes.
        
        Expected: Access denied without valid token.
        """
        response = client.get("/api/processes")
        assert response.status_code == 403


class TestAuthenticationJourney:
    """Journey: User authentication and authorization flows."""

    def test_full_auth_flow(self):
        """
        Journey: A user completes full authentication flow.
        
        Steps:
        1. Check health endpoint (public)
        2. Try to access protected endpoint (fails)
        3. Login with correct credentials
        4. Verify token works
        5. Access protected endpoint (succeeds)
        6. Logout or discard token
        """
        # Step 1: Check health (public)
        health_response = client.get("/health")
        assert health_response.status_code == 200
        assert health_response.json()["status"] == "healthy"
        
        # Step 2: Try to access protected endpoint (fails)
        protected_response = client.get("/api/servers")
        assert protected_response.status_code == 403
        
        # Step 3: Login with correct credentials
        login_response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "test-password-change-me"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        assert token is not None
        
        # Step 4: Verify token works
        headers = {"Authorization": f"Bearer {token}"}
        verify_response = client.get("/api/auth/verify", headers=headers)
        assert verify_response.status_code == 200
        assert verify_response.json()["username"] == "admin"
        
        # Step 5: Access protected endpoint (succeeds)
        servers_response = client.get("/api/servers", headers=headers)
        assert servers_response.status_code == 200
        
        # Step 6: Invalid token is rejected
        invalid_headers = {"Authorization": "Bearer invalid-token"}
        invalid_response = client.get("/api/servers", headers=invalid_headers)
        assert invalid_response.status_code in [401, 403]

    def test_login_with_wrong_password(self):
        """
        Journey: A user attempts to login with wrong password.
        
        Expected: Login fails, no token returned.
        """
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrong-password"}
        )
        assert response.status_code == 401

    def test_login_with_missing_fields(self):
        """
        Journey: A user submits incomplete login credentials.
        
        Expected: Request validation fails.
        """
        # Missing password
        response = client.post(
            "/api/auth/login",
            json={"username": "admin"}
        )
        assert response.status_code in [400, 422]
        
        # Missing username
        response = client.post(
            "/api/auth/login",
            json={"password": "test-password-change-me"}
        )
        assert response.status_code in [400, 422]


class TestMultiServerManagementJourney:
    """Journey: Managing multiple MCP servers together."""

    def test_multi_server_create_and_list(self, auth_token):
        """
        Journey: A user creates multiple servers and lists them.
        
        Steps:
        1. Create first server (HTTP transport)
        2. Create second server (SSE transport)
        3. List all servers
        4. Verify both servers are present
        """
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Step 1: Create first server (HTTP)
        server1 = {
            "id": 110,
            "name": "http-server",
            "transport": "http",
            "url": "http://localhost:8110",
            "arguments": [],
            "port": 8110,
            "supervisor_conf": {
                "command": "http-server-cli",
            },
            "tools": [{"name": "node", "version": "18"}],
            "envs": {},
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        create1_response = client.post("/api/servers", json=server1, headers=headers)
        assert create1_response.status_code == 201
        server1_id = create1_response.json()["id"]
        
        # Step 2: Create second server (SSE)
        server2 = {
            "id": 111,
            "name": "sse-server",
            "transport": "sse",
            "url": "http://localhost:8111",
            "arguments": [],
            "port": 8111,
            "supervisor_conf": {
                "command": "sse-server-cli",
            },
            "tools": [{"name": "python", "version": "3.11"}],
            "envs": {},
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        create2_response = client.post("/api/servers", json=server2, headers=headers)
        assert create2_response.status_code == 201
        server2_id = create2_response.json()["id"]
        
        # Step 3: List all servers
        list_response = client.get("/api/servers", headers=headers)
        assert list_response.status_code == 200
        servers = list_response.json()
        
        # Step 4: Verify both servers are present
        server_ids = [s["id"] for s in servers]
        assert server1_id in server_ids
        assert server2_id in server_ids
        assert len(servers) >= 2

    def test_bulk_sync_all_servers(self, auth_token):
        """
        Journey: A user syncs all server configurations to deployment.
        
        Steps:
        1. Create multiple servers
        2. Sync all servers
        3. Verify sync was successful
        4. Verify all servers still exist after sync
        """
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Step 1: Create multiple servers
        server_ids = []
        for i in range(3):
            server = {
                "id": 120 + i,
                "name": f"sync-test-server-{i}",
                "transport": "stdio",
                "command": f"python -m server{i}",
                "arguments": [],
                "port": 8120 + i,
                "supervisor_conf": {
                    "command": f"python -m server{i}",
                },
                "tools": [],
                "envs": {},
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
            }
            create_response = client.post("/api/servers", json=server, headers=headers)
            assert create_response.status_code == 201
            server_ids.append(create_response.json()["id"])
        
        # Step 2: Sync all servers
        sync_response = client.post("/api/servers/sync", headers=headers)
        assert sync_response.status_code == 200
        assert sync_response.json()["status"] == "success"
        
        # Step 3 & 4: Verify all servers still exist after sync
        for server_id in server_ids:
            get_response = client.get(f"/api/servers/{server_id}", headers=headers)
            assert get_response.status_code == 200
