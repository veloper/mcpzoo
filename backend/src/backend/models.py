import json, logging, os, signal, subprocess

from datetime import datetime
from enum import Enum
from pathlib import Path
from textwrap import dedent
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, field_validator, model_serializer

from backend.settings import get_settings


settings = get_settings()


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
    redirect_stderr: bool = True
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
    port:             Optional[int]            = Field(default=None, description="Port number for the server")
    supervisor_conf:  SupervisorConf           = Field(description="Supervisor configuration")
    tools:            List[MiseTool]           = Field(default_factory=list, description="List of required tools/languages")
    task_install:     str | None               = Field(default=None, description="Install task command")
    task_uninstall:   str | None               = Field(default=None, description="Uninstall task command")
    envs:             Dict[str, str]           = Field(default_factory=dict, description="Environment variables")
    log_level:        LogLevel                 = Field(default=LogLevel.INFO, description="Log level")
    created_at:       Optional[datetime]       = Field(default=None, description="Creation timestamp")
    updated_at:       Optional[datetime]       = Field(default=None, description="Last update timestamp")
    synced_at:        Optional[datetime]       = Field(default=None, description="Last sync timestamp")

    @field_validator('log_level', mode='before')
    @classmethod
    def validate_log_level(cls, v):
        """Ensure log_level is properly converted to LogLevel enum."""
        if isinstance(v, str):
            # Convert string to enum
            try:
                return LogLevel(v.upper())
            except ValueError:
                # If invalid string, default to INFO
                return LogLevel.INFO
        elif isinstance(v, LogLevel):
            return v
        else:
            # For any other type, default to INFO
            return LogLevel.INFO

    @field_validator('created_at', mode='before')
    @classmethod
    def validate_created_at(cls, v):
        """Set created_at to current datetime if None."""
        return v or datetime.now()

    @field_validator('updated_at', mode='before')
    @classmethod
    def validate_updated_at(cls, v):
        """Set updated_at to current datetime if None."""
        return v or datetime.now()

    @model_serializer()
    def serialize_model(self) -> Dict[str, Any]:
        """Serialize model to JSON-compatible dict, converting datetimes to ISO strings."""
        data = {}
        for field_name, field_info in self.model_fields.items():
            value = getattr(self, field_name)
            if isinstance(value, datetime):
                data[field_name] = value.isoformat()
            else:
                data[field_name] = value
        return data

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

    servers_dict: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Compiled mcpServers configuration dictionary")

    @classmethod
    def from_mcp_server_configs(cls, configs: List[MCPServerConfig]) -> "McpServersJsonFile":
        """Create McpServersJsonFile from list of MCPServerConfigs, extracting and transforming relevant fields."""
        servers_dict = {}
        for config in configs:
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
            
            # Environment variables
            if config.envs:
                servers_dict[config.name]["env"] = dict(config.envs)
        
        return cls(servers_dict=servers_dict)
            
    @model_serializer()
    def serialize(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {"mcpServers": self.servers_dict}
    
    def __str__(self) -> str:
        """String representation as JSON."""
        return json.dumps(self.serialize(), indent=4)


class FastMcpServerProxyServerFile(BaseModel):
    """FastMCP server that acts as a proxy to MCP server defined in mcpServers.json."""
    
    server_name: str = Field(description="Name of the MCP server")
    json_file_path: str = Field(description="Path to mcpServers.json configuration file")
    
    @classmethod
    def from_mcp_server_config(cls, config: MCPServerConfig, json_file_path: str) -> "FastMcpServerProxyServerFile":
        """Create FastMcpServerProxyServerFile from MCPServerConfig, extracting relevant fields."""
        return cls(
            server_name=config.name,
            json_file_path=json_file_path
        )
    
    def __str__(self) -> str:
        config_path = Path(self.json_file_path).resolve().as_posix()
        return dedent(f"""
            \"\"\"MCP Server Proxy - Generated by mcpzoo\"\"\"
            from fastmcp import FastMCP
            import json
            from pathlib import Path
            
            # Load MCP server configuration from mcpServers.json
            config_file = Path("{config_path}")
            config = json.loads(config_file.read_text())
            
            # Create proxy server from config 
            mcp = FastMCP.as_proxy(config, name="{self.server_name}")
            
            # Note:
            # Server name must be `mcp` to allow `fastmcp run server.py` to recognize it.
        """).strip()
        
        
class MiseTomlFile(BaseModel):
    """mise.toml configuration file for MCP server."""
    
    envs: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    tools: List[MiseTool] = Field(default_factory=list, description="Required tools/languages")
    tasks: Dict[str, str] = Field(default_factory=dict, description="Mise tasks (install, uninstall, etc.)")
    
    def ensure_tool(self, tool_name: str, version: Optional[str] = None) -> None:
        """Ensure tool exists, with version-aware upgrade semantics.
    
        Modes:
        - No version specified: add if missing (default to "*"), preserve any existing version
        - Version specified: add if missing, upgrade if existing < new (lexicographically), never downgrade
    
        Args:
            tool_name: Name of tool/language
            version: Exact or min version. None means any version acceptable, defaults to "*" if adding
        """
        existing = next((t for t in self.tools if t.name == tool_name), None)
    
        if existing is None:
            # Tool doesn't exist
            self.tools.append(MiseTool(name=tool_name, version=version or "*"))
        elif version is not None:
            # Tool exists + version constraint specified: upgrade if new > old (lex)
            if (
                existing.version is not None
                and existing.version != "*"
                and version is not None
                and version > existing.version
            ):
                existing.version = version
            elif existing.version == "*":
                # Wildcard always yields to explicit version
                existing.version = version
        # else: tool exists, no version constraint, leave untouched (permissive mode)
    
    
    def ensure_task(self, task_name: str, command: List[str]) -> None:
        """Ensure task exists. If already present, preserve existing value."""
        if task_name not in self.tasks:
            self.tasks[task_name] = " ".join(command)

    def ensure_env(self, key: str, value: str) -> None:
        """Ensure environment variable exists. If already present, preserve existing value."""
        if key not in self.envs:
            self.envs[key] = value
    
    def has_tool(self, tool_name: str) -> bool:
        return any(tool.name == tool_name for tool in self.tools)
    
    def has_task(self, task_name: str) -> bool:
        return task_name in self.tasks
    
    def has_env(self, key: str) -> bool:
        return key in self.envs
    
    @classmethod
    def from_mcp_server_config(cls, config: MCPServerConfig) -> "MiseTomlFile":
        """Create MiseTomlFile from MCPServerConfig, extracting and transforming relevant fields."""
        tasks = {}
        if config.task_install:
            tasks["install"] = config.task_install
        if config.task_uninstall:
            tasks["uninstall"] = config.task_uninstall
        
        
        
        return cls(
            envs=config.envs,
            tools=config.tools,
            tasks=tasks
        )
    
    def __str__(self) -> str:
        file = []

        if self.envs:
            file.append("")
            file.append("[env]")
            for k, v in self.envs.items():
                file.append(f'{k} = "{v}"')

        if self.tools:
            file.append("")
            file.append("[tools]")
            for tool in self.tools:
                if tool.version and tool.version != "*":
                    file.append(f'{tool.name} = "{tool.version}"')
                else:
                    file.append(f'{tool.name} = "latest"')

        if self.tasks:
            file.append("")
            file.append("[tasks]")
            for task_name, command in self.tasks.items():
                file.append(f'{task_name} = "{command}"')

        if file and file[0] == "":
            file = file[1:]  # Remove leading empty line

        return "\n".join(file)

class SupervisordConfFile(BaseModel):
    """Supervisord configuration file for MCP server."""
    
    supervisor_conf: SupervisorConf = Field(description="Supervisord [program:*] configuration")
    
    @classmethod
    def from_mcp_server_config(cls, config: MCPServerConfig) -> "SupervisordConfFile":
        """Create SupervisordConfFile from MCPServerConfig, extracting relevant fields."""
        return cls(supervisor_conf=config.supervisor_conf)

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


class PyProjectTomlDependency(BaseModel):
    """Dependency in pyproject.toml."""
    
    name: str = Field(description="Dependency name")
    operator: str | None = Field(default=None, description="Version operator (e.g., '==', '>=', '<', etc.)")
    version: str | None = Field(default=None, description="Version string")

class PyProjectTomlFile(BaseModel):
    """pyproject.toml file model."""
    
    name: str = Field(description="Project name")
    version: str = Field(description="Project version")
    description: str | None = Field(default=None, description="Project description")
    authors: List[str] = Field(default_factory=list, description="List of authors")
    dependencies: List[PyProjectTomlDependency] = Field(default_factory=list, description="List of dependencies")
    
    def __str__(self) -> str:
        file = []
        file.append('[project]')
        file.append(f'name = "{self.name}"')
        file.append(f'version = "{self.version}"')
        if self.description:
            file.append(f'description = "{self.description}"')
        if self.authors:
            authors_str = ', '.join([f'"{author}"' for author in self.authors])
            file.append(f'authors = [{authors_str}]')
        if self.dependencies:
            file.append('dependencies = [')
            for dep in self.dependencies:
                dep_str = dep.name
                if dep.operator and dep.version:
                    dep_str += f' {dep.operator} {dep.version}'
                elif dep.version:
                    dep_str += f' == {dep.version}'
                file.append(f'    "{dep_str}",')
            file.append(']')
        file.append('')
        file.append('[tool.uv]')
        file.append('')
        return '\n'.join(file)

class CommandReturn(BaseModel):
    """Standard command return model."""
    stdout: str = Field(default="", description="Standard output from command")
    stderr: str = Field(default="", description="Standard error from command")
    returncode: int = Field(default=0, description="Return code from command")
    
    def is_success(self) -> bool: return self.returncode == 0
    def is_failure(self) -> bool: return self.returncode != 0

class McpServerDirectory(BaseModel):
    """MCP server directory manager - creates and syncs server directories and files.

    - /app/servers/{server_id}
        - mcpServers.json
        - server.py
        - supervisord.conf
        - mise.toml
    """

    path: Path = Field(..., description="Base path for MCP servers")
    server_config: MCPServerConfig = Field(..., description="MCP server configuration")
   
    mise_toml_file: MiseTomlFile
    fastmcp_server_proxy_server_file: FastMcpServerProxyServerFile
    supervisord_conf_file: SupervisordConfFile
    mcp_servers_json_file: McpServersJsonFile
    
    @classmethod
    def from_server_config(cls, server_config: MCPServerConfig):
        """
        Create McpServerDirectory from MCPServerConfig.
        """
        deepcopy = MCPServerConfig.model_validate_json(server_config.model_dump_json())

        path = Path(get_settings().mcp_server_path) / deepcopy.id
        
        data = {
            "path": path,
            "server_config": deepcopy,
            "mise_toml_file": MiseTomlFile.from_mcp_server_config(deepcopy),
            "fastmcp_server_proxy_server_file": FastMcpServerProxyServerFile.from_mcp_server_config(deepcopy, json_file_path=os.path.join(path, "mcpServers.json")),
            "supervisord_conf_file": SupervisordConfFile.from_mcp_server_config(deepcopy),
            "mcp_servers_json_file": McpServersJsonFile.from_mcp_server_configs([deepcopy])
        }
        
        return cls(**data)
           
    
    # =========================
    # Main Actions
    # =========================
    
    def sync(self, logger : logging.Logger | None = None) -> None:
        ident = f"{self.server_config.name} (ID: {self.server_config.id})"
        
        self.ensure_directory()
        if logger: logger.info(f"Ensured directory exists for server: {ident}")
        
        self.clear_directory()
        if logger: logger.info(f"Cleared directory for server: {ident}")
        
        self.write_all_files()
        if logger: logger.info(f"Wrote files for server: {ident}")
        
        cmd_return = self.run_mise_install()
        if cmd_return.is_failure():
            if logger: logger.error(f"Mise install failed for server {ident}:\n{cmd_return.stderr}")
            raise RuntimeError(f"Mise install failed for server {ident}:\n{cmd_return.stderr}")
        else:
            if logger: logger.info(f"Mise install output for server {ident}:\n{cmd_return.stdout}")
            
        cmd_return = self.run_mise_task_install()
        if cmd_return.is_failure():
            if logger: logger.error(f"Mise install task failed for server {ident}:\n{cmd_return.stderr}")
            raise RuntimeError(f"Mise install task failed for server {ident}:\n{cmd_return.stderr}")
        else:
            if logger: logger.info(f"Mise install task output for server {ident}:\n{cmd_return.stdout}")
            
            
        if logger: logger.info(f"Completed MISE installation for server: {ident}")
    
    # =========================
    # Sub Actions
    # =========================
    
    def ensure_directory(self) -> None:
        """Ensure the server directory exists."""
        self.path.mkdir(parents=True, exist_ok=True)
    
    def clear_directory(self) -> None:
        """Clear all files in the server directory."""
        if self.path.exists() and self.path.is_dir():
            for item in self.path.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    import shutil
                    shutil.rmtree(item)
    
    def write_all_files(self) -> None:
        """Write all configuration files to the server directory."""
        # Ensure directory exists
        self.path.mkdir(parents=True, exist_ok=True)

        # Write all files
        (self.path / "mcpServers.json").write_text(str(self.mcp_servers_json_file))
        (self.path / "server.py").write_text(str(self.fastmcp_server_proxy_server_file))
        (self.path / "supervisord.conf").write_text(str(self.supervisord_conf_file))
        (self.path / "mise.toml").write_text(str(self.mise_toml_file))
        
        
    def run_mise_install(self, timeout: int = 300) -> CommandReturn:
        """Install dependencies using mise re"""

        try:
            
            env = {
                "MISE_TRUSTED_CONFIG_PATHS": str(self.path),
                **os.environ
            }
                
            # Change to server directory and run mise install (installs tools)
            result = subprocess.run(
                ["mise", "install"],
                cwd=str(self.path),
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env
            )

            if result.returncode != 0:
                raise RuntimeError(f"Failed to install mise tools: {result.stderr}")
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to install mise tools: {e.stderr}") from e
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(f"Mise install timed out after {timeout} seconds") from e
        
        return CommandReturn(
            stdout=result.stdout or "",
            stderr=result.stderr or "",
            returncode=result.returncode
        )

    def run_mise_task_install(self, timeout: int = 300) -> CommandReturn:
        """Run the 'install' task defined in mise.toml, if it exists.
        
        Args:
            timeout: Maximum time in seconds to allow the install task to run.
        """
        
        if not self.mise_toml_file.has_task("install"):
            return CommandReturn( stdout="", stderr="", returncode=0 )
        
        # Try to run the install task if it exists
        try:
            result = subprocess.run(
                ["mise", "run", "install"],
                cwd=self.path,
                capture_output=True,
                text=True,
                timeout=timeout 
            )

            if result.returncode != 0 and "No such task 'install'" not in result.stderr:
                raise RuntimeError(f"Failed to run install task: {result.stderr}")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to run install task: {e.stderr}") from e
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(f"Install task timed out after {timeout} seconds") from e
        
        return CommandReturn(
            stdout=result.stdout or "",
            stderr=result.stderr or "",
            returncode=result.returncode
        )
    
    # =========================
    # Command Generation helpers
    # =========================
    
    def get_mise_start_task_command(self) -> List[str]:
        """Get the command to run the MCP server via FastMCP."""
        return [
            "fastmcp", 
            "run", 
            "server.py", 
            "--host", "127.0.0.1",
            "--port", str(self.server_config.port), 
            "--log-level", self.server_config.log_level.value,
            "--transport", self.server_config.transport.value,
            "--project", str(self.path),
            "--no-banner"
        ]
    
    
    def get_supervisord_program_command(self) -> List[str]:
        """Get the command to run the MCP server via supervisord."""
        return ["mise", "run", "start"]
    
    # =========================
    # Lifecycle Methods
    # =========================
    
    def model_post_init(self, __context: Any) -> None:
        """Modify what is necessary after initialization."""

        # == Mise.toml ==

        # add run command to mise.toml
        self.mise_toml_file.ensure_task("start", self.get_mise_start_task_command())

        # if transport is stdio, we need to ensure runtime tools are present
        if self.server_config.transport == MCPServerConfigTransport.STDIO:
            command = self.server_config.command
            if command in ["pipx"]:
                self.mise_toml_file.ensure_tool("python")
                self.mise_toml_file.ensure_tool("pipx")
            
            elif command in ["python"]:
                self.mise_toml_file.ensure_tool("python")
            
            elif command in ["python3"]:
                self.mise_toml_file.ensure_tool("python", version=">=3")
            
            elif command in ["uvx"]:
                self.mise_toml_file.ensure_tool("python")
                self.mise_toml_file.ensure_tool("uv")
            
            elif command in ["go", "golang"]:
                self.mise_toml_file.ensure_tool("go")
                
            elif command in ["node", "npm", "npx"]:
                self.mise_toml_file.ensure_tool("node")
                self.mise_toml_file.ensure_tool("npm")
                
        # == Supervisord ==   

        # set supervisord directory to the server path
        self.supervisord_conf_file.supervisor_conf.directory = str(self.path)
        
        # set supervisord environment variable to allow mise to use the mise.toml in this directory
        self.supervisord_conf_file.supervisor_conf.environment["MISE_TRUSTED_CONFIG_PATHS"] = str(self.path)

        # we need to set the run command on supervisord to use mise run
        self.supervisord_conf_file.supervisor_conf.command = " ".join(self.get_supervisord_program_command())
        

    # =========================
    # Path helpers
    # =========================
    
    @property
    def server_dir_path(self) -> str:
        """Get the server directory path."""
        return os.path.join(self.base_path, self.server_config.name)

    def ensure_directory_exists(self) -> None:
        """Create the server directory if it doesn't exist."""
        os.makedirs(self.server_dir_path, exist_ok=True)

    @property
    def mcp_server_json_path(self) -> str:
        """Get the path to the mcpServers.json file."""
        return os.path.join(self.server_dir_path, "mcpServers.json")
    
    @property
    def fastmcp_server_proxy_path(self) -> str:
        """Get the path to the FastMCP server proxy file."""
        return os.path.join(self.server_dir_path, "server.py")
    
    @property
    def supervisord_conf_path(self) -> str:
        """Get the path to the supervisord configuration file."""
        return os.path.join(self.server_dir_path, "supervisord.conf")
    
    @property
    def mise_toml_path(self) -> str:
        """Get the path to the mise.toml file."""
        return os.path.join(self.server_dir_path, "mise.toml")


    # =========================
    # File Helpers
    # =========================

    def sync_files(self) -> None:
        """Write all configuration files to disk."""
        # Ensure directory exists
        self.path.mkdir(parents=True, exist_ok=True)

        # Write all files
        (self.path / "mcpServers.json").write_text(str(self.mcp_servers_json_file))
        (self.path / "server.py").write_text(str(self.fastmcp_server_proxy_server_file))
        (self.path / "supervisord.conf").write_text(str(self.supervisord_conf_file))
        (self.path / "mise.toml").write_text(str(self.mise_toml_file))

    def install_dependencies(self) -> None:
        """Install dependencies using mise."""
        import subprocess

        # Change to server directory and run mise install (installs tools)
        result = subprocess.run(
            ["mise", "install"],
            cwd=self.path,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(f"Failed to install mise tools: {result.stderr}")

        # Try to run the install task if it exists
        try:
            result = subprocess.run(
                ["mise", "run", "install"],
                cwd=self.path,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout for install tasks
            )
            # If the task doesn't exist, mise returns exit code 1 with "mise No such task 'install'"
            # We don't raise an error for this case since it's optional
            if result.returncode != 0 and "No such task 'install'" not in result.stderr:
                raise RuntimeError(f"Failed to run install task: {result.stderr}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("Install task timed out after 5 minutes")
