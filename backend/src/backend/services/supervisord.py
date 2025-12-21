"""Supervisord service wrapper with typed Program models."""
import http.client, socket, xmlrpc.client

from typing import Any, Dict, List, Optional

from src.backend.models import (Process, ProcessState, Program, SupervisorConf, SupervisorGetAllProcessInfoResponse,
                                SupervisorGetPIDResponse, SupervisorGetProcessInfoResponse, SupervisorGetStateResponse,
                                SupervisorProcessInfoData, SupervisorReadConfigResponse, SupervisorStartProcessResponse,
                                SupervisorStopProcessResponse, SupervisorUpdateResponse)


class UnixHTTPConnection(http.client.HTTPConnection):
    def __init__(self, host, socket_path):
        super().__init__(host)
        self.socket_path = socket_path

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(self.socket_path)


class UnixTransport(xmlrpc.client.Transport):
    def __init__(self, socket_path):
        super().__init__()
        self.socket_path = socket_path

    def make_connection(self, host):
        return UnixHTTPConnection(host, self.socket_path)


class SupervisordService:
    """Service wrapper for supervisord via XML-RPC over Unix socket."""
    
    def __init__(self, socket_path: str = "/var/run/supervisor.sock"):
        self.socket_path = socket_path
        self.transport = UnixTransport(socket_path)
        self.proxy = xmlrpc.client.ServerProxy('http://localhost', transport=self.transport)
    
    async def get_all_programs(self) -> List[Program]:
        """Get all supervisor programs as typed Program models."""
        try:
            info_response = self.get_all_process_info()
            programs = []

            for process_info in info_response.processes:
                # Create Process model from supervisor info
                process = Process(
                    pid=process_info.pid,
                    name=process_info.name,
                    state=self._map_supervisor_state(process_info.state),
                    uptime=process_info.uptime,
                    exit_code=process_info.exitstatus if process_info.exitstatus > 0 else None,
                    manager="supervisor"
                )

                # Create SupervisorConf from supervisor info
                config = SupervisorConf(
                    name=process_info.name,
                    command=""  # Would need to fetch from config file
                )

                # Create Program combining config and process
                program = Program(
                    config=config,
                    process=process
                )
                programs.append(program)

            return programs
        except Exception as e:
            raise RuntimeError(f"Failed to get programs: {str(e)}")
    
    def _map_supervisor_state(self, state_code: int) -> ProcessState:
        """Map supervisor state code to ProcessState enum."""
        state_map = {
            0: ProcessState.STOPPED,
            10: ProcessState.BACKOFF,
            20: ProcessState.RUNNING,
            30: ProcessState.FATAL,
            40: ProcessState.EXITED,
        }
        return state_map.get(state_code, ProcessState.UNKNOWN)
    
    async def get_program_status(self, name: str) -> Optional[Program]:
        """Get status of a specific program with its process."""
        try:
            all_programs = await self.get_all_programs()
            for prog in all_programs:
                if prog.name == name:
                    return prog
            return None
        except Exception as e:
            raise RuntimeError(f"Failed to get program status: {str(e)}")
    
    async def start_program(self, name: str) -> SupervisorStartProcessResponse:
        """Start a specific program's process and return typed response."""
        try:
            success = self.proxy.supervisor.startProcess(name)
            return SupervisorStartProcessResponse(success=success)
        except Exception as e:
            raise RuntimeError(f"Failed to start program {name}: {str(e)}")
    
    async def stop_program(self, name: str) -> SupervisorStopProcessResponse:
        """Stop a specific program's process and return typed response."""
        try:
            success = self.proxy.supervisor.stopProcess(name)
            return SupervisorStopProcessResponse(success=success)
        except Exception as e:
            raise RuntimeError(f"Failed to stop program {name}: {str(e)}")
    
    def get_process_info(self, name: str) -> SupervisorGetProcessInfoResponse:
        """Get info for a specific process by name."""
        try:
            data: Any = self.proxy.supervisor.getProcessInfo(name)
            if isinstance(data, dict):
                if 'uptime' not in data and 'now' in data and 'start' in data:
                    data['uptime'] = data['now'] - data['start'] if data['start'] > 0 else 0
            process_data = SupervisorProcessInfoData(**data)
            return SupervisorGetProcessInfoResponse(process_info=process_data)
        except Exception as e:
            raise RuntimeError(f"Failed to get process info for {name}: {str(e)}")
    
    def get_supervisord_pid(self) -> SupervisorGetPIDResponse:
        """Get the PID of supervisord itself."""
        try:
            pid: Any = self.proxy.supervisor.getPID()
            return SupervisorGetPIDResponse(pid=pid)
        except Exception as e:
            raise RuntimeError(f"Failed to get supervisord PID: {str(e)}")
    
    def get_state(self) -> SupervisorGetStateResponse:
        """Get supervisord state information."""
        try:
            data: Any = self.proxy.supervisor.getState()
            return SupervisorGetStateResponse(**data)
        except Exception as e:
            raise RuntimeError(f"Failed to get supervisord state: {str(e)}")
    
    def get_all_process_info(self) -> SupervisorGetAllProcessInfoResponse:
        """Get all process info as typed response."""
        try:
            data: Any = self.proxy.supervisor.getAllProcessInfo()
            processes = []
            for p in data:
                # Calculate uptime if missing
                if isinstance(p, dict):
                    if 'uptime' not in p and 'now' in p and 'start' in p:
                        p['uptime'] = p['now'] - p['start'] if p['start'] > 0 else 0
                processes.append(SupervisorProcessInfoData(**p))
            return SupervisorGetAllProcessInfoResponse(processes=processes)
        except Exception as e:
            raise RuntimeError(f"Failed to get process info: {str(e)}")
    
    def reread_config(self) -> SupervisorReadConfigResponse:
        """Reread and update supervisord config using supervisorctl commands."""
        try:
            # Use supervisorctl commands instead of XML-RPC
            import subprocess

            # First run 'supervisorctl reread' to read config files
            reread_result = subprocess.run(
                ["supervisorctl", "reread"],
                capture_output=True,
                text=True,
                timeout=30
            )

            # Then run 'supervisorctl update' to apply changes
            update_result = subprocess.run(
                ["supervisorctl", "update"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if update_result.returncode == 0:
                # Parse the output to extract added/changed/removed groups
                # supervisorctl update output shows which groups were affected
                output = update_result.stdout.strip()

                # Simple parsing - look for patterns like "group: added", "group: changed", etc.
                added_groups = []
                changed_groups = []
                removed_groups = []

                for line in output.split('\n'):
                    line = line.strip()
                    if ': added' in line:
                        group = line.split(': added')[0].strip()
                        added_groups.append(group)
                    elif ': changed' in line:
                        group = line.split(': changed')[0].strip()
                        changed_groups.append(group)
                    elif ': removed' in line:
                        group = line.split(': removed')[0].strip()
                        removed_groups.append(group)

                return SupervisorReadConfigResponse(
                    added_group_names=added_groups,
                    changed_group_names=changed_groups,
                    removed_group_names=removed_groups
                )
            else:
                # If update failed, try reload as fallback
                reload_result = subprocess.run(
                    ["supervisorctl", "reload"],
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if reload_result.returncode == 0:
                    return SupervisorReadConfigResponse(
                        added_group_names=[],  # Reload doesn't provide detailed info
                        changed_group_names=[],
                        removed_group_names=[]
                    )
                else:
                    raise RuntimeError(f"supervisorctl reload failed: {reload_result.stderr}")

        except Exception as e:
            raise RuntimeError(f"Failed to reread supervisord config: {str(e)}")
    
    async def update(self) -> SupervisorUpdateResponse:
        """Update supervisord from new config and return response."""
        try:
            # update() returns [[added], [changed], [removed]]
            data: Any = self.proxy.supervisor.update()
            return SupervisorUpdateResponse(
                added_group_names=data[0],
                changed_group_names=data[1],
                removed_group_names=data[2]
            )
        except Exception as e:
            raise RuntimeError(f"Failed to update supervisord: {str(e)}")


supervisord_service = SupervisordService()


def get_supervisord_service() -> SupervisordService:
    """Dependency for FastAPI to inject supervisord service."""
    return supervisord_service
