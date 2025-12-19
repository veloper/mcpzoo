import json, os, signal

from datetime import datetime
from enum import Enum
from pathlib import Path
from textwrap import dedent
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, model_serializer


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

class LogLevel(str, Enum):
    """Log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class MCPServerConfig(BaseModel):
    """MCP server configuration model."""
    
    id:               str                      = Field(description="Unique server identifier")
    name:             str                      = Field(description="Server name")
    transport:        MCPServerConfigTransport = Field(description="Transport type for MCP server")
    url:              str | None               = Field(default=None, description="URL for HTTP/SSE transport")
    command:          str | None               = Field(default=None, description="Command to run the server (for stdio transport)")
    arguments:        list[str]                = Field(default_factory=list, description="Arguments for the command")
    port:             int                      = Field(description="Port number for the server")
    supervisor_conf:  SupervisorConf           = Field(description="Supervisor configuration")
    tools:            List[MiseTool]           = Field(default_factory=list, description="List of required tools/languages")
    task_install:     str | None               = Field(default=None, description="Install task command")
    task_uninstall:   str | None               = Field(default=None, description="Uninstall task command")
    envs:             Dict[str, str]           = Field(default_factory=dict, description="Environment variables")
    log_level:        LogLevel                 = Field(default=LogLevel.INFO, description="Log level")
    created_at:       datetime                 = Field(description="Creation timestamp")
    updated_at:       datetime                 = Field(description="Last update timestamp")

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
    
    

class McpServersJsonFile(BaseModel):
    """MCP servers configuration file model."""

    mcp_servers_configs: List[MCPServerConfig]

    def servers(self) -> Dict[str, Dict[str, Any]]:
        """Generate mcpServers dict with all configs."""
        servers_dict = {}
        for config in self.mcp_servers_configs:
            servers_dict[config.name] = {}
            # Env
            if config.envs:
                servers_dict[config.name]["env"] = {k: v for k, v in config.envs.items()}
                
            # Transport-specific config
            if config.transport == MCPServerConfigTransport.STDIO:
                servers_dict[config.name] = {
                    "type": config.transport.value,
                    "command": config.command,
                    "args": config.arguments
                }
            else:
                servers_dict[config.name] = {
                    "type": config.transport.value,
                    "url": config.url
                }
                
        return servers_dict
            
    @model_serializer()
    def serialize(self) -> Dict[str, Any]:
        """Serialize to JSON string."""
        return { "mcpServers": self.servers() }
    
    def __str__(self) -> str:
        """String representation as JSON."""
        return json.dumps(self.serialize(), indent=4)


class FastMcpServerProxyServerFile(BaseModel):
    """FastMCP server that acts as a proxy to MCP server defined in mcpServers.json."""
    
    mcp_server_config: MCPServerConfig
    mcp_server_json_file_path: Path
    
    def __str__(self):
        return dedent(f"""
            \"\"\"MCP Server Proxy - Generated by mcpzoo\"\"\"
            from fastmcp import FastMCP
            import json
            from pathlib import Path
            
            # Load MCP server configuration from mcpServers.json
            config_file = Path("{self.mcp_server_json_file_path.resolve().as_posix()}")
            config = json.loads(config_file.read_text())
            
            # Create proxy server from config 
            mcp = FastMCP.as_proxy(config, name={self.mcp_server_config.name}
            
            # Note:
            # Server name must be `mcp` to allow `fastmcp run server.py` to recognize it.
        """).strip()

class MiseTomlFile(BaseModel):
    """mise.toml configuration file for MCP server."""
    
    mcp_server_config: MCPServerConfig
    
    @property
    def envs(self) -> Dict[str, str]:
        """Get environment variables for mise.toml."""
        return self.mcp_server_config.envs
    
    @property
    def tools(self) -> List[MiseTool]:
        """Get tools for mise.toml."""
        return self.mcp_server_config.tools
    
    @property
    def tasks(self) -> Dict[str, str]:
        """Get tasks for mise.toml."""
        tasks = {}
        if self.mcp_server_config.task_install:
            tasks["install"] = self.mcp_server_config.task_install
        if self.mcp_server_config.task_uninstall:
            tasks["uninstall"] = self.mcp_server_config.task_uninstall
        return tasks
    
    def __str__(self) -> str:
        file = []
        
        if self.envs:
            file += ""
            file += "[env]"
            for k, v in self.envs.items():
                file += f'{k} = "{v}"'
                
        if self.tools:
            file += ""
            file += "[tools]"
            for tool in self.tools:
                if tool.version:
                    file += f'{tool.name} = "{tool.version}"'
                else:
                    file += f'{tool.name} = "*"'
                    
        if self.tasks:
            file += ""
            file += "[tasks]"
            for task_name, command in self.tasks.items():
                file += f'{task_name} = "{command}"'
        
        if file and file[0] == "":
            file = file[1:]  # Remove leading empty line
        
        return "\n".join(file)

class SupervisordConfFile(BaseModel):
    """Supervisord configuration file for MCP server."""
    
    mcp_server_config: MCPServerConfig
    
    
    @property
    def supervisor_conf(self) -> SupervisorConf:
        return self.mcp_server_config.supervisor_conf

    def __str__(self) -> str:
        file = []
        
        file.append(f"[program:{self.supervisor_conf.name}]")
        file.append(f"command={self.supervisor_conf.command}")
        file.append(f"group={self.supervisor_conf.group}")
        file.append(f"process_name={self.supervisor_conf.process_name}")
        file.append(f"numprocs={self.supervisor_conf.numprocs}")
        file.append(f"priority={self.supervisor_conf.priority}")
        file.append(f"autostart={'true' if self.supervisor_conf.autostart else 'false'}")
        file.append(f"autorestart={self.supervisor_conf.autorestart}")
        file.append(f"startsecs={self.supervisor_conf.startsecs}")
        file.append(f"startretries={self.supervisor_conf.startretries}")
        file.append(f"stopsignal={self.supervisor_conf.stopsignal}")
        file.append(f"stopwaitsecs={self.supervisor_conf.stopwaitsecs}")
        file.append(f"umask={self.supervisor_conf.umask}")
        file.append(f"user={self.supervisor_conf.user}")
        file.append(f"redirect_stderr={'true' if self.supervisor_conf.redirect_stderr else 'false'}")
        
        if self.supervisor_conf.directory:
            file.append(f"directory={self.supervisor_conf.directory}")
        
        if self.supervisor_conf.stdout_logfile:
            file.append(f"stdout_logfile={self.supervisor_conf.stdout_logfile}")
            file.append(f"stdout_logfile_maxbytes={self.supervisor_conf.stdout_logfile_maxbytes}")
            file.append(f"stdout_logfile_backups={self.supervisor_conf.stdout_logfile_backups}")
        
        if self.supervisor_conf.stderr_logfile:
            file.append(f"stderr_logfile={self.supervisor_conf.stderr_logfile}")
            file.append(f"stderr_logfile_maxbytes={self.supervisor_conf.stderr_logfile_maxbytes}")
            file.append(f"stderr_logfile_backups={self.supervisor_conf.stderr_logfile_backups}")
        
        if self.supervisor_conf.environment:
            envs = ",".join([f'{k}="{v}"' for k, v in self.supervisor_conf.environment.items()])
            file.append(f"environment={envs}")
        
        return "\n".join(file)



class McpServerDirectory(BaseModel):
    """MCP server directory manager - creates and syncs server directories and files.
    
    - /app/servers/{server_id}
        - mcpServers.json
        - server.py
        - supervisord.conf
        - mise.toml
    
    
    """

    server_config: MCPServerConfig
    base_path: str = "/app/servers"

    
    def get_run_command(self) -> str:
        """Get the command to run the MCP server."""
        return " ".join([
            "mise", 
            "run", 
            "fastmcp", 
            "run", 
            "server.py", 
            "--host", "127.0.0.1", 
            "--no-banner", 
            "--transport", "http", 
            "--port", str(self.server_config.port), 
            "--log-level", str(self.server_config.log_level.value)
        ])
    
    
            


    @property
    def server_directory(self) -> str:
        """Get the server directory path."""
        return os.path.join(self.base_path, self.server_config.name)

    def ensure_directory_exists(self) -> None:
        """Create the server directory if it doesn't exist."""
        os.makedirs(self.server_directory, exist_ok=True)

    @property
    def mcp_server_json_path(self) -> str:
        """Get the path to the mcpServers.json file."""
        return os.path.join(self.server_directory, "mcpServers.json")
    
    @property
    def fastmcp_server_proxy_path(self) -> str:
        """Get the path to the FastMCP server proxy file."""
        return os.path.join(self.server_directory, "server.py")
    
    @property
    def supervisord_conf_path(self) -> str:
        """Get the path to the supervisord configuration file."""
        return os.path.join(self.server_directory, "supervisord.conf")
    
    @property
    def mise_toml_path(self) -> str:
        """Get the path to the mise.toml file."""
        return os.path.join(self.server_directory, "mise.toml")
