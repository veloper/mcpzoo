from __future__ import annotations

from configparser import ConfigParser
from typing import TYPE_CHECKING, Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field
from src.backend.enums import SupervisorProcessState
from src.backend.process import Process


if TYPE_CHECKING:
    from src.backend.models import ServerConfiguration


class SupervisorProcessInfo(BaseModel):
    """Typed model for supervisord RPC process info response."""
    model_config = ConfigDict(use_enum_values=True)

    name      : str = Field(description="Process name as configured in supervisord")
    group     : str = Field(description="Process group name")
    state     : int = Field(description="Numeric state code (0=STOPPED, 10=BACKOFF, 20=RUNNING, 30=FATAL, 40=EXITED)")
    statename : str = Field(description="Human-readable state name (STOPPED, BACKOFF, RUNNING, FATAL, EXITED, etc.)")
    pid       : int = Field(description="Process ID (0 if not running)")
    exitstatus: int = Field(description="Exit status code when process exited (0 if still running)")
    spawnerr  : str = Field(description="Error message if spawning failed, empty string otherwise")
    now       : int = Field(description="Current unix timestamp")
    uptime    : int = Field(description="Seconds the process has been in current state")

    @property
    def process_state(self) -> SupervisorProcessState:
        """Map supervisor state code to ProcessState enum."""
        state_map = {
            0: SupervisorProcessState.STOPPED,
            10: SupervisorProcessState.BACKOFF,
            20: SupervisorProcessState.RUNNING,
            30: SupervisorProcessState.FATAL,
            40: SupervisorProcessState.EXITED,
        }
        return state_map.get(self.state, SupervisorProcessState.UNKNOWN)


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
    data: Dict[str, Any] | None = None
    error: str | None = None


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

    name          : str           = Field(description="Process name as configured in supervisord")
    group         : str           = Field(description="Process group name")
    state         : int           = Field(description="Numeric state code (0=STOPPED, 10=BACKOFF, 20=RUNNING, 30=FATAL, 40=EXITED)")
    statename     : str           = Field(description="Human-readable state name (STOPPED, BACKOFF, RUNNING, FATAL, EXITED)")
    pid           : int           = Field(description="Process ID (0 if not running)")
    exitstatus    : int           = Field(description="Exit status code when process exited (0 if still running)")
    spawnerr      : str           = Field(description="Error message if spawning failed, empty string otherwise")
    now           : int           = Field(description="Current unix timestamp")
    uptime        : int | None    = Field(default=None, description="Seconds the process has been in current state")
    start         : int           = Field(description="Unix timestamp when process was started")
    stop          : int           = Field(description="Unix timestamp when process was stopped (0 if running)")
    description   : str | None    = Field(default=None, description="Human-readable process description (e.g. 'pid 1234, uptime 1:23:45')")
    logfile       : str | None    = Field(default=None, description="Path to stdout log file (deprecated, for backward compatibility)")
    stdout_logfile: str | None    = Field(default=None, description="Path to stdout log file")
    stderr_logfile: str | None    = Field(default=None, description="Path to stderr log file")


class SupervisorGetAllProcessInfoResponse(BaseModel):
    """Response from supervisor.getAllProcessInfo() RPC call."""
    model_config = ConfigDict()

    processes: List[SupervisorProcessInfoData] = Field(default_factory=list, description="List of all managed processes")


class SupervisorGetProcessInfoResponse(BaseModel):
    """Response from supervisor.getProcessInfo() RPC call."""
    model_config = ConfigDict()

    process_info: SupervisorProcessInfoData = Field(description="Information about the requested process")


class SupervisorConf(BaseModel):
    """Supervisord [program:*] configuration."""

    name                   : str            = Field(description="The name of the program")
    group                  : str            = Field(default="mcp_servers", description="The group name for the program")
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


class SupervisorProgram(BaseModel):
    """Supervisor program - composition of config and optional running process."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    config: SupervisorConf
    process: Process | None = None

    @property
    def name(self) -> str: return self.config.name

    @property
    def command(self) -> str: return self.config.command

    @property
    def directory(self) -> str | None: return self.config.directory

    @property
    def user(self) -> str | None: return self.config.user

    @property
    def autostart(self) -> bool: return self.config.autostart

    @property
    def autorestart(self) -> str: return self.config.autorestart

    @property
    def environment(self) -> Dict[str, str]: return self.config.environment

    @property
    def group(self) -> str | None: return self.config.group

    @property
    def priority(self) -> int: return self.config.priority


class SupervisorConfFile(BaseModel):
    """Supervisord configuration file for MCP server."""

    supervisor_conf: SupervisorConf = Field(description="Supervisord [program:*] configuration")

    @classmethod
    def from_mcp_server_config(cls, config: ServerConfiguration) -> "SupervisorConfFile":
        """Create SupervisordConfFile from MCPServerConfig, extracting relevant fields."""
        return cls(supervisor_conf=config.supervisor_conf)

    @classmethod
    def from_string(cls, file_contents : str) -> "SupervisorConfFile":
        config = ConfigParser()
        config.read_string(file_contents)
        
        # Find the program section
        program_sections = [s for s in config.sections() if s.startswith("program:")]
        if not program_sections:
            raise ValueError("No [program:*] section found in config")
        program_section_name = program_sections[0]
        section = config[program_section_name]
        
        # Extract name from section name
        name = program_section_name.split(":", 1)[1]
        
        # Parse environment if present
        environment = {}
        env_str = section.get("environment")
        if env_str:
            for pair in env_str.split(","):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"')
                    environment[k] = v
        
        # Create SupervisorProgramConf
        supervisor_conf = SupervisorConf.model_validate(section)
        
        return cls(supervisor_conf=supervisor_conf)
    
    def __str__(self) -> str:
        conf = self.supervisor_conf
        file = []

        file.append(f"[program:{conf.name}]")
        file.append(f"command={conf.command}")
        file.append(f"process_name={conf.process_name}")
        file.append(f"numprocs={conf.numprocs}")
        file.append(f"priority={conf.priority}")
        file.append(f"autostart={'true' if conf.autostart else 'false'}")
        file.append(f"autorestart={conf.autorestart}")
        file.append(f"startsecs={conf.startsecs}")
        file.append(f"startretries={conf.startretries}")
        file.append(f"stopsignal={conf.stopsignal}")
        file.append(f"stopwaitsecs={conf.stopwaitsecs}")
        file.append(f"umask={conf.umask}")
        file.append(f"user={conf.user}")
        file.append(f"redirect_stderr={'true' if conf.redirect_stderr else 'false'}")


        if conf.group:
            file.append(f"group={conf.group}")
        
        if conf.directory:
            file.append(f"directory={conf.directory}")

        if conf.stdout_logfile:
            file.append(f"stdout_logfile={conf.stdout_logfile}")
            file.append(f"stdout_logfile_maxbytes={conf.stdout_logfile_maxbytes}")
            file.append(f"stdout_logfile_backups={conf.stdout_logfile_backups}")

        if conf.stderr_logfile:
            file.append(f"stderr_logfile={conf.stderr_logfile}")
            file.append(f"stderr_logfile_maxbytes={conf.stderr_logfile_maxbytes}")
            file.append(f"stderr_logfile_backups={conf.stderr_logfile_backups}")

        if conf.environment:
            envs = ",".join([f'{k}="{v}"' for k, v in self.supervisor_conf.environment.items()])
            file.append(f"environment={envs}")

        return "\n".join(file)
