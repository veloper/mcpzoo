"""Test implementations of services."""

import uuid
import time
from typing import List

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from src.backend.services.database import DatabaseService
from src.backend.services.mise import MiseService
from src.backend.services.processes import ProcessesService
from src.backend.services.supervisor import SupervisorService
from src.backend.supervisor import SupervisorProcessState, SupervisorProcess, SupervisorGetStateResponse, SupervisorReadConfigResponse, SupervisorUpdateResponse


class InMemoryDatabaseService(DatabaseService):
    """In-memory database service for testing."""

    def __init__(self):
        """Initialize with in-memory SQLite."""
        # Create in-memory SQLite database
        engine = create_engine("sqlite:///:memory:", echo=False)
        SQLModel.metadata.create_all(engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        # Create a mock database instance that uses the in-memory session
        class InMemoryDatabase:
            def __init__(self, session_factory):
                self.SessionLocal = session_factory
                self.servers = {}
                self.sync_tasks = {}

            def get_session(self):
                return self.SessionLocal()

            def insert_server(self, server_data):
                server_id = server_data.get("id", str(uuid.uuid4()))
                self.servers[server_id] = server_data.copy()
                return server_id

            def get_server(self, server_id):
                return self.servers.get(server_id)

            def get_all_servers(self):
                return list(self.servers.values())

            def update_server(self, server_id, data):
                if server_id in self.servers:
                    self.servers[server_id].update(data)
                    return True
                return False

            def delete_server(self, server_id):
                if server_id in self.servers:
                    del self.servers[server_id]
                    return True
                return False

            def insert_sync_task(self, task_data):
                task_id = task_data.get("id", str(uuid.uuid4()))
                self.sync_tasks[task_id] = task_data.copy()
                return task_id

            def get_sync_task(self, task_id):
                return self.sync_tasks.get(task_id)

            def get_all_sync_tasks(self):
                return list(self.sync_tasks.values())

            def update_sync_task(self, task_id, data):
                if task_id in self.sync_tasks:
                    self.sync_tasks[task_id].update(data)
                    return True
                return False

            def delete_sync_task(self, task_id):
                if task_id in self.sync_tasks:
                    del self.sync_tasks[task_id]
                    return True
                return False

            def clear_all(self):
                """Clear all data from the in-memory database."""
                self.servers.clear()
                self.sync_tasks.clear()

        super().__init__(InMemoryDatabase(SessionLocal))
        self._id_counter = 0


class MockSupervisordService(SupervisorService):
    """Fully operational mock supervisor service for testing.

    This mock behaves like a real supervisor daemon in memory, supporting
    all FastAPI testing scenarios without external dependencies. It provides
    configurable state management for different test scenarios.
    """

    def __init__(self):
        """Initialize with configurable state."""
        self.processes = {}  # Dict[str, SupervisorProcess]
        self.groups = {}     # Dict[str, List[str]]
        self.supervisor_pid = 1234
        self.supervisor_state = "RUNNING"
        self.start_time = int(time.time())
        self.config_files = {}  # Dict[str, SupervisorProgramConfig]
        self.next_pid = 1000

    # Helper methods for test configuration
    def set_process_state(self, name: str, state: SupervisorProcessState, pid: int = None):
        """Set a process to a specific state."""
        if name in self.processes:
            process = self.processes[name]

            # Map enum to integer state codes
            state_map = {
                SupervisorProcessState.STOPPED: 0,
                SupervisorProcessState.STARTING: 10,
                SupervisorProcessState.RUNNING: 20,
                SupervisorProcessState.BACKOFF: 30,
                SupervisorProcessState.STOPPING: 40,
                SupervisorProcessState.EXITED: 100,
                SupervisorProcessState.FATAL: 200,
                SupervisorProcessState.UNKNOWN: 1000,
            }

            process.state = state_map[state]
            process.statename = state.value
            if pid is not None:
                process.pid = pid
            else:
                # Generate a new PID if not specified
                self.next_pid += 1
                process.pid = self.next_pid
            # Update timestamps based on state
            current_time = int(time.time())
            process.now = current_time
            if state == SupervisorProcessState.RUNNING:
                if process.start == 0:
                    process.start = current_time
                process.stop = 0
            elif state in [SupervisorProcessState.STOPPED, SupervisorProcessState.EXITED]:
                process.stop = current_time
                process.pid = 0
                process.exitstatus = 0 if state == SupervisorProcessState.EXITED else process.exitstatus
            elif state == SupervisorProcessState.FATAL:
                process.stop = current_time
                process.pid = 0
                process.exitstatus = 1
            # Update description
            if state == SupervisorProcessState.RUNNING:
                process.description = f"pid {process.pid}, uptime 0:00:00"
            else:
                process.description = f"Process {state.value.lower()}"

    def add_process(self, name: str, group: str = "default", state: SupervisorProcessState = SupervisorProcessState.STOPPED, pid: int = 0):
        """Add a new test process."""
        current_time = int(time.time())

        # Map enum to integer state codes
        state_map = {
            SupervisorProcessState.STOPPED: 0,
            SupervisorProcessState.STARTING: 10,
            SupervisorProcessState.RUNNING: 20,
            SupervisorProcessState.BACKOFF: 30,
            SupervisorProcessState.STOPPING: 40,
            SupervisorProcessState.EXITED: 100,
            SupervisorProcessState.FATAL: 200,
            SupervisorProcessState.UNKNOWN: 1000,
        }

        process = SupervisorProcess(
            name=name,
            group=group,
            statename=state.value,
            pid=pid,
            exitstatus=0,
            spawnerr="",
            now=current_time,
            start=current_time if state == SupervisorProcessState.RUNNING else 0,
            stop=0 if state == SupervisorProcessState.RUNNING else current_time,
            description=f"Process {state.value.lower()}",
            logfile=f"/var/log/supervisor/{name}.log",
            stdout_logfile=f"/var/log/supervisor/{name}_stdout.log",
            stderr_logfile=f"/var/log/supervisor/{name}_stderr.log",
            state=state_map[state]
        )
        self.processes[name] = process

        # Add to group
        if group not in self.groups:
            self.groups[group] = []
        if name not in self.groups[group]:
            self.groups[group].append(name)

    def clear_all_processes(self):
        """Reset all processes for clean test state."""
        self.processes.clear()
        self.groups.clear()
        self.next_pid = 1000

    # Standard SupervisorService methods
    def get_all_programs(self) -> List[SupervisorProcess]:
        """Return all configured processes."""
        return list(self.processes.values())

    def start_program(self, name: str) -> bool:
        """Start a specific program and return success status."""
        if name in self.processes:
            self.set_process_state(name, SupervisorProcessState.RUNNING)
            return True
        return False

    def stop_program(self, name: str) -> bool:
        """Stop a specific program and return success status."""
        if name in self.processes:
            self.set_process_state(name, SupervisorProcessState.STOPPED)
            return True
        return False

    def get_process_info(self, name: str) -> SupervisorProcess:
        """Get detailed info for a specific process by name."""
        if name in self.processes:
            return self.processes[name]
        # Raise exception for non-existent processes to match real supervisor behavior
        raise RuntimeError(f"Process {name} not found")

    def get_supervisord_pid(self) -> int:
        """Get the PID of supervisord itself."""
        return self.supervisor_pid

    def get_state(self) -> SupervisorGetStateResponse:
        """Get supervisord state information."""
        return SupervisorGetStateResponse(
            statecode=1,  # RUNNING
            statename="RUNNING"
        )

    def reread_config(self) -> SupervisorReadConfigResponse:
        """Reload supervisord configuration files."""
        # For mock, just return success with no changes
        return SupervisorReadConfigResponse(
            added_group_names=[],
            changed_group_names=[],
            removed_group_names=[]
        )

    def update(self) -> SupervisorUpdateResponse:
        """Update supervisord with any changes from the last reread."""
        return SupervisorUpdateResponse(
            added_group_names=[],
            changed_group_names=[],
            removed_group_names=[]
        )


class MockProcessesService(ProcessesService):
    """Mock processes service for testing."""

    def __init__(self):
        """Initialize with mock data."""
        self.processes = []

    def get_all_processes(self):
        """Return mock processes."""
        # Import Process model and ProcessState enum
        from src.backend.process import Process, ProcessState
        from datetime import datetime

        # Return mock process data that matches the expected API response
        return [
            Process(
                pid=1234,
                name="python",
                state=ProcessState.RUNNING,
                command="python -m test",
                create_time=datetime.fromtimestamp(int(time.time()) - 3600),
                memory_percent=10.5,
                cpu_percent=5.2,
                user="root"
            ),
            Process(
                pid=5678,
                name="node",
                state=ProcessState.RUNNING,
                command="node server.js",
                create_time=datetime.fromtimestamp(int(time.time()) - 7200),
                memory_percent=8.3,
                cpu_percent=2.1,
                user="root"
            )
        ]

    def get_process_tree(self):
        """Return mock process tree."""
        # Import Process model and ProcessState enum
        from src.backend.process import Process, ProcessState
        from datetime import datetime

        # Get processes and build tree structure
        processes = self.get_all_processes()

        return {
            "processes": processes,
            "tree": {
                "root": {
                    "children": [
                        {
                            "pid": 1234,
                            "name": "python",
                            "children": []
                        }
                    ]
                }
            }
        }


class MockSyncService:
    """Mock sync service for testing."""

    def __init__(self):
        """Initialize with mock data."""
        self.records = []

    def get_all_sync_records(self):
        """Return mock sync records."""
        return self.records

    def create_sync_record(self, record_data):
        """Create a new sync record."""
        record_id = f"mock-{len(self.records)}"
        record = {"id": record_id, **record_data}
        self.records.append(record)
        return record

    def clear_all_sync_records(self):
        """Clear all sync records."""
        self.records.clear()

    async def start_sync(self):
        """Start a new sync task."""
        task_id = len(self.records) + 1
        task = {
            "id": task_id,
            "status": "PENDING",
            "created_at": "2024-01-01T00:00:00",
            "log_file_path": f"/tmp/sync_{task_id}.log",
            "total_servers": 0,
            "progress": 0,
            "current_step": "Starting sync"
        }
        self.records.append(task)
        return task_id

    async def get_task(self, task_id: int):
        """Get a sync task by ID."""
        for record in self.records:
            if record["id"] == task_id:
                return record
        return None

    async def list_tasks(self, limit: int = 50, offset: int = 0):
        """List all sync tasks with pagination."""
        tasks = self.records[offset:offset + limit]
        return {
            "tasks": tasks,
            "total": len(self.records),
            "limit": limit,
            "offset": offset
        }

    async def get_task_logs(self, task_id: int, tail: int = 100):
        """Get logs for a sync task."""
        return f"Mock log for task {task_id}"

    async def clear_all_tasks(self):
        """Clear all sync tasks."""
        count = len(self.records)
        self.records.clear()
        return count


class MockMiseService(MiseService):
    """Mock mise service for testing."""

    def __init__(self):
        """Initialize with mock data."""
        self.tool_availability = {
            "node": {"available": True, "versions": ["20.12.0", "18.19.0", "16.20.2"], "latest": "20.12.0"},
            "python": {"available": True, "versions": ["3.12.3", "3.11.9", "3.10.15"], "latest": "3.12.3"},
            "go": {"available": True, "versions": ["1.22.3", "1.21.11", "1.20.15"], "latest": "1.22.3"},
            "rust": {"available": True, "versions": ["1.78.0", "1.77.2", "1.76.0"], "latest": "1.78.0"},
            "unavailable-tool": {"available": False, "error": "Tool not found"}
        }

    def check_tool(self, tool_spec: str) -> dict:
        """Check if mise recognizes a specified tool without installing it.

        Args:
            tool_spec: Tool specification (e.g., 'node', 'python', 'go', 'python:3.10')

        Returns:
            Dict with tool availability and version information
        """
        # Parse tool:version format
        if ':' in tool_spec:
            tool_name, requested_version = tool_spec.split(':', 1)
            tool_name = tool_name.strip()
            requested_version = requested_version.strip()
        else:
            tool_name = tool_spec.strip()
            requested_version = None

        # Check mock data
        if tool_name in self.tool_availability:
            tool_data = self.tool_availability[tool_name]
            if not tool_data["available"]:
                return {
                    "available": False,
                    "tool": tool_name,
                    "version": requested_version,
                    "error": tool_data["error"]
                }

            # Tool is available
            if requested_version:
                # Check if requested version exists
                if requested_version in tool_data["versions"]:
                    return {
                        "available": True,
                        "tool": tool_name,
                        "version": requested_version,
                        "latest_version": tool_data["latest"]
                    }
                else:
                    return {
                        "available": False,
                        "tool": tool_name,
                        "version": requested_version,
                        "error": f"Version {requested_version} not found for tool {tool_name}"
                    }
            else:
                # No specific version requested
                return {
                    "available": True,
                    "tool": tool_name,
                    "latest_version": tool_data["latest"]
                }
        else:
            # Tool not found in mock data
            return {
                "available": False,
                "tool": tool_name,
                "version": requested_version,
                "error": "Tool not found"
            }

    def get_tool_versions(self, tool_name: str) -> dict:
        """Get available versions for a mise tool.

        Args:
            tool_name: Name of the tool to get versions for

        Returns:
            Dict with tool versions and latest version
        """
        if tool_name in self.tool_availability:
            tool_data = self.tool_availability[tool_name]
            if tool_data["available"]:
                return {
                    "tool": tool_name,
                    "versions": tool_data["versions"],
                    "latest": tool_data["latest"]
                }
            else:
                return {
                    "tool": tool_name,
                    "versions": [],
                    "latest": None,
                    "error": tool_data["error"]
                }
        else:
            return {
                "tool": tool_name,
                "versions": [],
                "latest": None,
                "error": "Tool not found"
            }
