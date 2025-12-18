"""Test implementations of services."""

import asyncio
import uuid
from typing import Optional
from src.backend.models import (
    Program, SupervisorConf, Process, ProcessState,
    SupervisorStartProcessResponse, SupervisorStopProcessResponse,
    SupervisorReadConfigResponse, SupervisorUpdateResponse
)
from src.backend.services.database import DatabaseService
from src.backend.services.supervisord import SupervisordService
from src.backend.services.processes import ProcessesService
from tinydb import TinyDB
from tinydb.storages import MemoryStorage


class InMemoryDatabaseService(DatabaseService):
    """In-memory database service for testing."""

    def __init__(self):
        """Initialize with in-memory TinyDB."""
        super().__init__(TinyDB(storage=MemoryStorage))
        self._id_counter = 0


class MockSupervisordService(SupervisordService):
    """Mock supervisord service for testing."""

    def __init__(self):
        """Initialize with test data."""
        self.programs = [
            Program(
                config=SupervisorConf(name="mcp_test", command="/usr/bin/python"),
                process=Process(
                    pid=1234,
                    name="mcp_test",
                    state=ProcessState.RUNNING,
                    uptime=3600,
                    manager="supervisor"
                )
            )
        ]

    async def get_all_programs(self) -> list[Program]:
        """Return all programs."""
        return self.programs

    async def get_program_status(self, name: str) -> Optional[Program]:
        """Get program status by name."""
        for prog in self.programs:
            if prog.name == name:
                return prog
        return None

    async def start_program(self, name: str) -> SupervisorStartProcessResponse:
        """Start a program."""
        for prog in self.programs:
            if prog.name == name and prog.process:
                prog.process.state = ProcessState.RUNNING
                return SupervisorStartProcessResponse(success=True)
        return SupervisorStartProcessResponse(success=False)

    async def stop_program(self, name: str) -> SupervisorStopProcessResponse:
        """Stop a program."""
        for prog in self.programs:
            if prog.name == name and prog.process:
                prog.process.state = ProcessState.STOPPED
                return SupervisorStopProcessResponse(success=True)
        return SupervisorStopProcessResponse(success=False)

    async def restart_program(self, name: str) -> bool:
        """Restart a program."""
        await self.stop_program(name)
        return (await self.start_program(name)).success

    async def reread_config(self) -> SupervisorReadConfigResponse:
        """Reread configuration."""
        return SupervisorReadConfigResponse(added_processes=[], removed_processes=[])

    async def update(self) -> SupervisorUpdateResponse:
        """Update supervisord."""
        return SupervisorUpdateResponse(added_processes=[], removed_processes=[])


class MockProcessesService(ProcessesService):
    """Mock processes service for testing."""

    async def get_by_pid(self, pid: int) -> Optional[Process]:
        """Get process by PID."""
        return None

    async def get_by_name(self, name: str) -> Optional[Process]:
        """Get process by name."""
        return None

    async def list_all(self) -> list[Process]:
        """List all processes."""
        return []

    async def refresh(self, process: Process) -> None:
        """Refresh process data."""
        pass

    async def send_term(self, process: Process) -> bool:
        """Send SIGTERM."""
        return True

    async def send_kill(self, process: Process) -> bool:
        """Send SIGKILL."""
        return True

    async def send_stop(self, process: Process) -> bool:
        """Send SIGSTOP."""
        return True

    async def send_cont(self, process: Process) -> bool:
        """Send SIGCONT."""
        return True

    async def send_hup(self, process: Process) -> bool:
        """Send SIGHUP."""
        return True

    async def send_usr1(self, process: Process) -> bool:
        """Send SIGUSR1."""
        return True

    async def send_usr2(self, process: Process) -> bool:
        """Send SIGUSR2."""
        return True
