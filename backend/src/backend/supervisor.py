"""
This is a self contained module for Supervisor control via XML-RPC.

It contains typed models for the various RPC responses, as well as
a service wrapper for making the XML-RPC calls over a Unix socket.

All models are defined using Pydantic for type safety and validation.

It also includes helpful pydantic models for generating and representing
supervisord configurations and config files.

"""
from __future__ import annotations

import http.client, shlex, socket, xmlrpc.client

from configparser import ConfigParser
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field


if TYPE_CHECKING:
    from src.backend.models import Server


class UnixHTTPConnection(http.client.HTTPConnection):
    """HTTP connection over Unix socket.
    """
    def __init__(self, host, socket_path):
        super().__init__(host)
        self.socket_path = socket_path

    def connect(self):
        """Connect to the Unix socket (AF_UNIX) instead of TCP."""
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(self.socket_path)


class UnixTransport(xmlrpc.client.Transport):
    """XML-RPC transport over Unix socket."""
    def __init__(self, socket_path):
        super().__init__()
        self.socket_path = socket_path

    def make_connection(self, host):
        return UnixHTTPConnection(host, self.socket_path)

    
class SupervisorProcessState(str, Enum):
    """Supervisord process states."""
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    BACKOFF = "BACKOFF"
    STOPPING = "STOPPING"
    EXITED = "EXITED"
    FATAL = "FATAL"
    UNKNOWN = "UNKNOWN"

class SupervisorProcess(BaseModel):
    """Typed model representing xmlrpc.supervisor.getProcessInfo() or getAllProcessInfo() response for individual process information.

    {
        'name': 'context7',
        'group': 'context7',
        'start': 1766856158,
        'stop': 0,
        'now': 1766892175,
        'state': 20,
        'statename': 'RUNNING',
        'spawnerr': '',
        'exitstatus': 0,
        'logfile': '/var/log/supervisor/mcp_context7_stdout.log',
        'stdout_logfile': '/var/log/supervisor/mcp_context7_stdout.log',
        'stderr_logfile': '',
        'pid': 207,
        'description': 'pid 207, uptime 10:00:17'
        }

    """
    model_config = ConfigDict()

    name          : str           = Field(description="Process name as configured in supervisord")
    group         : str           = Field(description="Process group name")
    statename     : str           = Field(description="Human-readable state name (STOPPED, BACKOFF, RUNNING, FATAL, EXITED)")
    pid           : int           = Field(description="Process ID (0 if not running)")
    exitstatus    : int           = Field(description="Exit status code when process exited (0 if still running)")
    spawnerr      : str           = Field(description="Error message if spawning failed, empty string otherwise")
    now           : int           = Field(description="Current unix timestamp")
    start         : int           = Field(description="Unix timestamp when process was started")
    stop          : int           = Field(description="Unix timestamp when process was stopped (0 if running)")
    description   : str | None    = Field(default=None, description="Human-readable process description (e.g. 'pid 1234, uptime 1:23:45')")
    logfile       : str | None    = Field(default=None, description="Path to stdout log file (deprecated, for backward compatibility)")
    stdout_logfile: str | None    = Field(default=None, description="Path to stdout log file")
    stderr_logfile: str | None    = Field(default=None, description="Path to stderr log file")
    state         : int           = Field(description="Current process state as integer code")

    @property
    def uptime_seconds(self) -> int:
        """Get process uptime in seconds, or 0 if not running."""
        if self.state_enum == SupervisorProcessState.RUNNING:
            return self.now - self.start
        return 0


    @computed_field(description="Current process state as enum")
    @property
    def state_enum(self) -> SupervisorProcessState:
        # Map integer state codes to enum values
        state_map = {
            0: SupervisorProcessState.STOPPED,
            10: SupervisorProcessState.STARTING,
            20: SupervisorProcessState.RUNNING,
            30: SupervisorProcessState.BACKOFF,
            40: SupervisorProcessState.STOPPING,
            100: SupervisorProcessState.EXITED,
            200: SupervisorProcessState.FATAL,
            1000: SupervisorProcessState.UNKNOWN,
        }
        return state_map.get(self.state, SupervisorProcessState.UNKNOWN)
    
    @computed_field(description="Whether the process is currently running")
    @property
    def is_running(self) -> bool:
        return self.state_enum == SupervisorProcessState.RUNNING
    
    @property
    def is_stopped(self) -> bool: return self.state_enum == SupervisorProcessState.STOPPED
    
    @property
    def is_starting(self) -> bool: return self.state_enum == SupervisorProcessState.STARTING
    
    @property
    def is_stopping(self) -> bool: return self.state_enum == SupervisorProcessState.STOPPING
    
    @property
    def is_fatal(self) -> bool: return self.state_enum == SupervisorProcessState.FATAL
    
    @property
    def is_exited(self) -> bool: return self.state_enum == SupervisorProcessState.EXITED
    
    @property
    def is_backoff(self) -> bool: return self.state_enum == SupervisorProcessState.BACKOFF
    
    @property
    def is_unknown(self) -> bool: return self.state_enum == SupervisorProcessState.UNKNOWN
    


class SupervisorGetStateResponse(BaseModel):
    """Response from supervisor.getState() RPC call."""
    model_config = ConfigDict()

    statecode: int = Field(description="Numeric supervisord state code")
    statename: str = Field(description="Human-readable supervisord state")
    now: int = Field(description="Current unix timestamp")
    pid: int = Field(description="Process ID of supervisord daemon")
    server_version: str = Field(description="Supervisord version string")



class SupervisorReadConfigResponse(BaseModel):
    """Response from supervisor.reloadConfig() RPC call."""
    model_config = ConfigDict()

    added_group_names   : List[str] = Field(default_factory=list, description="Group names that were added")
    changed_group_names : List[str] = Field(default_factory=list, description="Group names that were changed")
    removed_group_names : List[str] = Field(default_factory=list, description="Group names that were removed")

    @classmethod
    def from_xmlrpc_response(cls, data: Any) -> "SupervisorReadConfigResponse":
        """Parse XML-RPC response which returns [[added, changed, removed]]."""
        # The response format is [[added_list, changed_list, removed_list]]
        if isinstance(data, list) and len(data) == 1 and isinstance(data[0], list) and len(data[0]) == 3:
            added, changed, removed = data[0]
            return cls(
                added_group_names=added if isinstance(added, list) else [],
                changed_group_names=changed if isinstance(changed, list) else [],
                removed_group_names=removed if isinstance(removed, list) else []
            )
        else:
            # Fallback for unexpected format
            return cls()


class SupervisorUpdateResponse(BaseModel):
    """Response from supervisor.update() RPC call."""
    model_config = ConfigDict()

    added_group_names   : List[str] = Field(default_factory=list, description="Group names that were added")
    changed_group_names : List[str] = Field(default_factory=list, description="Group names that were changed")
    removed_group_names : List[str] = Field(default_factory=list, description="Group names that were removed")  


class SupervisorProgramConfig(BaseModel):
    """Supervisord [program:*] configuration.
    
    Only meant to represent a config with a single [program:name] section.
    """

    name                   : str            = Field(description="The name of the program")
    group                  : str | None     = Field(default=None, description="The group name for the program")
    command                : str            = Field(description="The command to run the program")
    directory              : str | None     = Field(default=None, description="The working directory for the program")
    umask                  : str            = Field(default="022", description="The umask for the program")
    user                   : str            = Field(default="root", description="The user to run the program as")
    autostart              : bool           = Field(default=True, description="Whether to start the program automatically")
    autorestart            : str            = Field(default="unexpected", description="When to restart the program (never, unexpected, true)")
    startsecs              : int            = Field(default=1, description="Number of seconds to wait before considering the program started")
    startretries           : int            = Field(default=3, description="Number of times to retry starting the program")
    priority               : int            = Field(default=999, description="Priority of the program")
    stopsignal             : str            = Field(default="TERM", description="Signal to send to stop the program")
    stopwaitsecs           : int            = Field(default=10, description="Seconds to wait before sending KILL signal")
    stdout_logfile         : str | None     = Field(default=None, description="Path to the stdout log file")
    stdout_logfile_maxbytes: int            = Field(default=50_000_000, description="Maximum size of stdout log file in bytes")
    stdout_logfile_backups : int            = Field(default=10, description="Number of stdout log file backups")
    stderr_logfile         : str | None     = Field(default=None, description="Path to the stderr log file")
    stderr_logfile_maxbytes: int            = Field(default=50_000_000, description="Maximum size of stderr log file in bytes")
    stderr_logfile_backups : int            = Field(default=10, description="Number of stderr log file backups")
    redirect_stderr        : bool           = Field(default=True, description="Whether to redirect stderr to stdout")
    environment            : Dict[str, str] = Field(default_factory=dict, description="Environment variables for the program")
    numprocs               : int            = Field(default=1, description="Number of processes to start")
    process_name           : str            = Field(default="%(program_name)s", description="Template for process names")

    @classmethod
    def parse(cls, file_contents: str) -> SupervisorProgramConfig:
        """Parse supervisord [program:*] config from string."""
        try:
            config = ConfigParser()
            config.read_string(file_contents)
        except Exception as e:
            raise ValueError(f"Failed to parse config file: {str(e)}") from e

        # Find the program section
        program_sections = [s for s in config.sections() if s.startswith("program:")]
        if not program_sections:
            raise ValueError("No [program:*] section found in config")
        if len(program_sections) > 1:
            raise ValueError(f"Multiple program sections found: {program_sections}. Only one program section is supported.")

        program_section_name = program_sections[0]
        section = config[program_section_name]

        # Extract name from section name
        name = program_section_name.split(":", 1)[1]

        # Validate required fields
        if not section.get("command"):
            raise ValueError("Required field 'command' is missing from program configuration")

        # Parse environment if present
        environment = {}
        env_str = section.get("environment")
        if env_str:
            try:
                # Split on commas to handle "KEY1=VAL1,KEY2=VAL2" format
                for pair in env_str.split(','):
                    pair = pair.strip()
                    if '=' in pair:
                        key, value = pair.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        if key:  # Ensure key is not empty
                            environment[key] = value
                        else:
                            raise ValueError(f"Empty environment variable key in pair: {pair}")
                    else:
                        raise ValueError(f"Invalid environment variable format (missing '='): {pair}")
            except Exception as e:
                raise ValueError(f"Failed to parse environment variables: {str(e)}") from e

        # Create SupervisorProgramConfig with manual field assignment using ConfigParser type converters
        try:
            supervisor_conf = cls(
                name=name,
                command=section.get("command"),
                group=section.get("group"),
                directory=section.get("directory"),
                umask=section.get("umask", "022"),
                user=section.get("user", "root"),
                autostart=section.getboolean("autostart", True),
                autorestart=section.get("autorestart", "unexpected"),
                startsecs=section.getint("startsecs", 1),
                startretries=section.getint("startretries", 3),
                priority=section.getint("priority", 999),
                stopsignal=section.get("stopsignal", "TERM"),
                stopwaitsecs=section.getint("stopwaitsecs", 10),
                stdout_logfile=section.get("stdout_logfile"),
                stdout_logfile_maxbytes=section.getint("stdout_logfile_maxbytes", 50_000_000),
                stdout_logfile_backups=section.getint("stdout_logfile_backups", 10),
                stderr_logfile=section.get("stderr_logfile"),
                stderr_logfile_maxbytes=section.getint("stderr_logfile_maxbytes", 50_000_000),
                stderr_logfile_backups=section.getint("stderr_logfile_backups", 10),
                redirect_stderr=section.getboolean("redirect_stderr", True),
                environment=environment,
                numprocs=section.getint("numprocs", 1),
                process_name=section.get("process_name", "%(program_name)s"),
            )
        except Exception as e:
            raise ValueError(f"Failed to parse program configuration: {str(e)}") from e

        return supervisor_conf

    def __str__(self) -> str:
        file = []
        file.append(f"[program:{self.name}]")
        file.append(f"command={self.command}")
        file.append(f"process_name={self.process_name}")
        file.append(f"numprocs={self.numprocs}")
        file.append(f"priority={self.priority}")
        file.append(f"autostart={'true' if self.autostart else 'false'}")
        file.append(f"autorestart={self.autorestart}")
        file.append(f"startsecs={self.startsecs}")
        file.append(f"startretries={self.startretries}")
        file.append(f"stopsignal={self.stopsignal}")
        file.append(f"stopwaitsecs={self.stopwaitsecs}")
        file.append(f"umask={self.umask}")
        file.append(f"user={self.user}")
        file.append(f"redirect_stderr={'true' if self.redirect_stderr else 'false'}")
        if self.group:
            file.append(f"group={self.group}")
            
        if self.directory:
            file.append(f"directory={self.directory}")
            
        if self.stdout_logfile:
            file.append(f"stdout_logfile={self.stdout_logfile}")
            file.append(f"stdout_logfile_maxbytes={self.stdout_logfile_maxbytes}")
            file.append(f"stdout_logfile_backups={self.stdout_logfile_backups}")
            
        if self.stderr_logfile:
            file.append(f"stderr_logfile={self.stderr_logfile}")
            file.append(f"stderr_logfile_maxbytes={self.stderr_logfile_maxbytes}")
            file.append(f"stderr_logfile_backups={self.stderr_logfile_backups}")
            
        if self.environment:
            envs = ",".join([f"{k}={shlex.quote(v)}" for k, v in self.environment.items()])
            file.append(f"environment={envs}")
            
        return "\n".join(file)

class SupervisorService:
    """Service wrapper for supervisord via XML-RPC over Unix socket.
    
    Returns typed models for all applicable RPC calls that return dict-like responses, otherwise
    returns native types (e.g. bool for start/stop, int for pid, etc.).
    
    unique names reference `[program:name]` sections in supervisord.conf files.
    
    Methods:
    - get_all_programs()
    - start_program(name: str)
    - stop_program(name: str)
    - get_process_info(name: str)
    - get_supervisord_pid()
    - get_state()
    - reread_config()
    - update()
    """
    
    def __init__(self, socket_path: str = "/var/run/supervisor.sock"):
        self.socket_path = socket_path
        self.transport = UnixTransport(socket_path)
        self.proxy = xmlrpc.client.ServerProxy('http://localhost', transport=self.transport)
        
    
    def get_all_programs(self) -> List[SupervisorProcess]:
        """Get __all__ supervisor programs as typed Program models"""
        try:
            result = self.proxy.supervisor.getAllProcessInfo()
            print("=" * 20)
            print(result)
            print("=" * 20)
            if not isinstance(result, list):
                raise RuntimeError("Invalid response from supervisord getAllProcessInfo")
            return [SupervisorProcess.model_validate(p) for p in result]
        except Exception as e:
            raise RuntimeError(f"Failed to get programs: {str(e)}") from e
    
    def start_program(self, name: str) -> bool:
        """Start a specific program's process and return typed response."""
        try:
            return bool(self.proxy.supervisor.startProcess(name))
        except Exception as e:
            raise RuntimeError(f"Failed to start program {name}: {str(e)}") from e
        
    def stop_program(self, name: str) -> bool:
        """Stop a specific program's process and return typed response."""
        try:
            return bool(self.proxy.supervisor.stopProcess(name))
        except Exception as e:
            raise RuntimeError(f"Failed to stop program {name}: {str(e)}") from e
        
    def get_process_info(self, name: str) -> SupervisorProcess:
        """Get info for a specific process by name."""
        try:
            data: Any = self.proxy.supervisor.getProcessInfo(name)
            return SupervisorProcess.model_validate(data)
        except Exception as e:
            raise RuntimeError(f"Failed to get process info for {name}: {str(e)}") from e


    def get_supervisord_pid(self) -> int:
        """Get the PID of supervisord itself."""
        try:
            pid: Any = self.proxy.supervisor.getPID()
            return int(pid)
        except Exception as e:
            raise RuntimeError(f"Failed to get supervisord PID: {str(e)}") from e

    def get_state(self) -> SupervisorGetStateResponse:
        """Get supervisord state information
        
        Meaning, get the state of supervisord itself, not the managed processes.
        """
        try:
            data: Any = self.proxy.supervisor.getState()
            return SupervisorGetStateResponse(**data)
        except Exception as e:
            raise RuntimeError(f"Failed to get supervisord state: {str(e)}") from e
        
    def reread_config(self) -> bool:
        """Reload supervisord configuration files.

        Due to a bug in supervisord's xmlrpc service, this method actually needs to
        shell-out to the supervisorctl reread command to properly reread configs.
        """
        try:
            # data: Any = self.proxy.supervisor.reloadConfig()
            # return SupervisorReadConfigResponse.from_xmlrpc_response(data)

            import subprocess

            result = subprocess.run(
                ["supervisorctl", "reread"],
                capture_output=True,
                text=True,
                check=True,
            )

            output = result.stdout.strip()
            if "No config updates to process" in output:
                return True

            # Parse the actual output format: "groupname: status"
            # where status can be: changed, disappeared, available
            lines = output.split('\n')
            for line in lines:
                line = line.strip()
                if ':' in line:
                    group_name, status = line.split(':', 1)
                    group_name = group_name.strip()
                    status = status.strip()
                    if status in ['changed', 'disappeared', 'available']:
                        return True

            # If we get here, the output format is unexpected
            raise RuntimeError(f"Unexpected output from supervisorctl reread: {output}")
        except Exception as e:
            raise RuntimeError(f"Failed to reload supervisord config: {str(e)}") from e
        
    def update(self) -> SupervisorUpdateResponse:
        """Update supervisord with any changes from the last reread."""
        try:
            import subprocess

            result = subprocess.run(
                ["supervisorctl", "update"],
                capture_output=True,
                text=True,
                check=True,
            )

            # Parse the output to extract added/changed/removed groups
            output = result.stdout.strip()
            added = []
            changed = []
            removed = []

            for line in output.split('\n'):
                line = line.strip()
                if ': added' in line:
                    added.append(line.split(': added')[0])
                elif ': changed' in line:
                    changed.append(line.split(': changed')[0])
                elif ': removed' in line:
                    removed.append(line.split(': removed')[0])

            return SupervisorUpdateResponse(
                added_group_names=added,
                changed_group_names=changed,
                removed_group_names=removed
            )
        except Exception as e:
            raise RuntimeError(f"Failed to update supervisord config: {str(e)}") from e
