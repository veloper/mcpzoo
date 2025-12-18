import json, os, signal

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ProcessState(str, Enum):
    """Universal process states."""
    STOPPED = "STOPPED"
    RUNNING = "RUNNING"
    UNKNOWN = "UNKNOWN"
    # Supervisor-specific states
    BACKOFF = "BACKOFF"
    FATAL = "FATAL"
    EXITED = "EXITED"


class SupervisorProcessInfo(BaseModel):
    """Typed model for supervisord RPC process info response."""
    model_config = ConfigDict(use_enum_values=True)
    
    name: str = Field(description="Process name as configured in supervisord")
    group: str = Field(description="Process group name")
    state: int = Field(description="Numeric state code (0=STOPPED, 10=BACKOFF, 20=RUNNING, 30=FATAL, 40=EXITED)")
    statename: str = Field(description="Human-readable state name (STOPPED, BACKOFF, RUNNING, FATAL, EXITED, etc.)")
    pid: int = Field(description="Process ID (0 if not running)")
    exitstatus: int = Field(description="Exit status code when process exited (0 if still running)")
    spawnerr: str = Field(description="Error message if spawning failed, empty string otherwise")
    now: int = Field(description="Current unix timestamp")
    uptime: int = Field(description="Seconds the process has been in current state")
    
    @property
    def process_state(self) -> ProcessState:
        """Map supervisor state code to ProcessState enum."""
        state_map = {
            0: ProcessState.STOPPED,
            10: ProcessState.BACKOFF,
            20: ProcessState.RUNNING,
            30: ProcessState.FATAL,
            40: ProcessState.EXITED,
        }
        return state_map.get(self.state, ProcessState.UNKNOWN)


class SupervisorState(BaseModel):
    """Typed model for supervisord state info."""
    model_config = ConfigDict()
    
    statecode: int = Field(description="Numeric supervisord state code (0=FATAL, 1=RUNNING, 2=RESTARTING, 3=SHUTDOWN)")
    statename: str = Field(description="Human-readable supervisord state (FATAL, RUNNING, RESTARTING, SHUTDOWN)")
    now: int = Field(description="Current unix timestamp")
    pid: int = Field(description="Process ID of supervisord daemon")
    server_version: str = Field(description="Supervisord version string")


class SupervisorRPCResponse(BaseModel):
    """Generic RPC response wrapper."""
    model_config = ConfigDict()
    
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class SupervisorGetStateResponse(BaseModel):
    """Response from supervisor.getState() RPC call."""
    model_config = ConfigDict()
    
    statecode: int = Field(description="Numeric supervisord state code")
    statename: str = Field(description="Human-readable supervisord state")
    now: int = Field(description="Current unix timestamp")
    pid: int = Field(description="Process ID of supervisord daemon")
    server_version: str = Field(description="Supervisord version string")


class SupervisorGetPIDResponse(BaseModel):
    """Response from supervisor.getPID() RPC call."""
    model_config = ConfigDict()
    
    pid: int = Field(description="Process ID of supervisord daemon")


class SupervisorReadConfigResponse(BaseModel):
    """Response from supervisor.rereadConfig() RPC call."""
    model_config = ConfigDict()
    
    added_group_names: List[str] = Field(default_factory=list, description="Group names that were added")
    changed_group_names: List[str] = Field(default_factory=list, description="Group names that were changed")
    removed_group_names: List[str] = Field(default_factory=list, description="Group names that were removed")


class SupervisorUpdateResponse(BaseModel):
    """Response from supervisor.update() RPC call."""
    model_config = ConfigDict()
    
    added_group_names: List[str] = Field(default_factory=list, description="Group names that were added")
    changed_group_names: List[str] = Field(default_factory=list, description="Group names that were changed")
    removed_group_names: List[str] = Field(default_factory=list, description="Group names that were removed")


class SupervisorStartProcessResponse(BaseModel):
    """Response from supervisor.startProcess() RPC call."""
    model_config = ConfigDict()
    
    success: bool = Field(description="Whether the process was successfully started")


class SupervisorStopProcessResponse(BaseModel):
    """Response from supervisor.stopProcess() RPC call."""
    model_config = ConfigDict()
    
    success: bool = Field(description="Whether the process was successfully stopped")


class SupervisorProcessInfoData(BaseModel):
    """Individual process info data from supervisor.getAllProcessInfo() RPC."""
    model_config = ConfigDict()
    
    name: str = Field(description="Process name as configured in supervisord")
    group: str = Field(description="Process group name")
    state: int = Field(description="Numeric state code (0=STOPPED, 10=BACKOFF, 20=RUNNING, 30=FATAL, 40=EXITED)")
    statename: str = Field(description="Human-readable state name (STOPPED, BACKOFF, RUNNING, FATAL, EXITED)")
    pid: int = Field(description="Process ID (0 if not running)")
    exitstatus: int = Field(description="Exit status code when process exited (0 if still running)")
    spawnerr: str = Field(description="Error message if spawning failed, empty string otherwise")
    now: int = Field(description="Current unix timestamp")
    uptime: Optional[int] = Field(default=None, description="Seconds the process has been in current state")
    start: int = Field(description="Unix timestamp when process was started")
    stop: int = Field(description="Unix timestamp when process was stopped (0 if running)")
    description: Optional[str] = Field(default=None, description="Human-readable process description (e.g. 'pid 1234, uptime 1:23:45')")
    logfile: Optional[str] = Field(default=None, description="Path to stdout log file (deprecated, for backward compatibility)")
    stdout_logfile: Optional[str] = Field(default=None, description="Path to stdout log file")
    stderr_logfile: Optional[str] = Field(default=None, description="Path to stderr log file")


class SupervisorGetAllProcessInfoResponse(BaseModel):
    """Response from supervisor.getAllProcessInfo() RPC call."""
    model_config = ConfigDict()
    
    processes: List[SupervisorProcessInfoData] = Field(default_factory=list, description="List of all managed processes")


class SupervisorGetProcessInfoResponse(BaseModel):
    """Response from supervisor.getProcessInfo() RPC call."""
    model_config = ConfigDict()
    
    process_info: SupervisorProcessInfoData = Field(description="Information about the requested process")


class Process(BaseModel):
    """Universal Linux process model - pure data representation."""
    model_config = ConfigDict(use_enum_values=True)
    
    pid: int
    name: str
    state: ProcessState
    parent: Optional['Process'] = None
    uptime: Optional[int] = None
    memory_rss: Optional[int] = None
    memory_percent: Optional[float] = None
    cpu_percent: Optional[float] = None
    user: Optional[str] = None
    command: Optional[str] = None
    cwd: Optional[str] = None
    manager: Optional[str] = None  # e.g., "supervisor", "systemd", or None
    created_at: Optional[datetime] = None
    exit_code: Optional[int] = None
    num_threads: Optional[int] = None
    nice: Optional[int] = None
    io_read_bytes: Optional[int] = None
    io_write_bytes: Optional[int] = None
    
    @property
    def is_child(self) -> bool:
        """Check if this process is a child process."""
        return self.parent is not None
    
    @property
    def parent_pid(self) -> Optional[int]:
        """Get parent process ID if this is a child process."""
        return self.parent.pid if self.parent else None
    
    @property
    def is_running(self) -> bool:
        """Check if process is in running state."""
        return self.state == ProcessState.RUNNING
    
    @property
    def is_stopped(self) -> bool:
        """Check if process is in stopped state."""
        return self.state in (ProcessState.STOPPED, ProcessState.EXITED, ProcessState.FATAL)
    
    @property
    def is_healthy(self) -> bool:
        """Check if process is in a healthy state."""
        return self.state in (ProcessState.RUNNING, ProcessState.EXITED)


Process.model_rebuild()


class MiseTool(BaseModel):
    """Tool/language version requirement (e.g., python, node, go)."""
    name: str
    version: Optional[str] = None


class MCPServerConfigTransport(str, Enum):
    """MCP server transport type."""
    SSE = "sse"
    HTTP = "http"
    STDIO = "stdio"


class SupervisorConf(BaseModel):
    """Supervisord [program:*] configuration."""
    
    name: str
    group: str = "mcp_servers"
    command: str
    directory: Optional[str] = None
    umask: str = "022"
    user: str = "root"
    autostart: bool = True
    autorestart: str = "unexpected"
    startsecs: int = 1
    startretries: int = 3
    priority: int = 999
    stopsignal: str = "TERM"
    stopwaitsecs: int = 10
    stdout_logfile: Optional[str] = None
    stdout_logfile_maxbytes: int = 50_000_000
    stdout_logfile_backups: int = 10
    stderr_logfile: Optional[str] = None
    stderr_logfile_maxbytes: int = 50_000_000
    stderr_logfile_backups: int = 10
    redirect_stderr: bool = False
    environment: Dict[str, str] = {}
    numprocs: int = 1
    process_name: str = "%(program_name)s"

    def to_supervisord_program_section(self) -> str:
        """Generate [program:*] section."""
        lines = [f"[program:{self.name}]"]
        lines.append(f"command={self.command}")
        if self.directory:
            lines.append(f"directory={self.directory}")
        if self.user:
            lines.append(f"user={self.user}")
        lines.append(f"autostart={'true' if self.autostart else 'false'}")
        lines.append(f"autorestart={self.autorestart}")
        lines.append(f"priority={self.priority}")
        if self.stdout_logfile:
            lines.append(f"stdout_logfile={self.stdout_logfile}")
            lines.append(f"stdout_logfile_maxbytes={self.stdout_logfile_maxbytes}")
            lines.append(f"stdout_logfile_backups={self.stdout_logfile_backups}")
        if self.stderr_logfile:
            lines.append(f"stderr_logfile={self.stderr_logfile}")
        if self.environment:
            lines.append(f"environment={','.join([f'{k}={v}' for k, v in self.environment.items()])}")
        return "\n".join(lines)


class Program(BaseModel):
    """Supervisor program - composition of config and optional running process."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    config: SupervisorConf
    process: Optional[Process] = None
    
    @property
    def name(self) -> str:
        """Alias to config.name."""
        return self.config.name
    
    @property
    def command(self) -> str:
        """Alias to config.command."""
        return self.config.command
    
    @property
    def directory(self) -> Optional[str]:
        """Alias to config.directory."""
        return self.config.directory
    
    @property
    def user(self) -> Optional[str]:
        """Alias to config.user."""
        return self.config.user
    
    @property
    def autostart(self) -> bool:
        """Alias to config.autostart."""
        return self.config.autostart
    
    @property
    def autorestart(self) -> str:
        """Alias to config.autorestart."""
        return self.config.autorestart
    
    @property
    def environment(self) -> Dict[str, str]:
        """Alias to config.environment."""
        return self.config.environment
    
    @property
    def group(self) -> Optional[str]:
        """Alias to config.group."""
        return self.config.group
    
    @property
    def priority(self) -> int:
        """Alias to config.priority."""
        return self.config.priority


class MCPServerConfig(BaseModel):
    """MCP server configuration model."""
    
    id: str
    name: str
    transport: MCPServerConfigTransport
    url: Optional[str] = None
    command: Optional[str] = None
    arguments: List[str] = []
    port: int
    supervisor_conf: SupervisorConf
    tools: List[MiseTool] = []
    task_install: Optional[str] = None
    task_uninstall: Optional[str] = None
    task_run: Optional[str] = None
    envs: Dict[str, str] = {}
    created_at: datetime
    updated_at: datetime

    def to_mcp_server_json(self) -> str:
        """Generate MCP server config JSON."""
        if self.transport == MCPServerConfigTransport.STDIO:
            config = {
                "type": "stdio",
                "command": self.command,
                "args": self.arguments
            }
        else:
            config = {
                "type": self.transport.value,
                "url": self.url
            }
        
        return json.dumps({self.name: config}, indent=4)


# Request/Response Models

class LoginRequest(BaseModel):
    """Login request."""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """JWT token data."""
    sub: Optional[str] = None
    exp: Optional[int] = None
