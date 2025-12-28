import json, logging, os, re, signal, subprocess

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, field_validator
from sqlalchemy import Column
from sqlalchemy.types import JSON
from sqlmodel import Field, SQLModel
from src.backend.enums import LogLevel, MCPServerTransport, SyncTaskStatus
from src.backend.fast_mcp import FastMcpServerProxyServerFile
from src.backend.mcp import McpServersJsonFile
from src.backend.mise import MiseTomlFile
from src.backend.settings import get_settings
from src.backend.supervisor import SupervisorProgramConfig


settings = get_settings()

class ServerTool(BaseModel):
    """Tool/language requirement with version for server configuration."""
    name: str = Field(description="Tool/language name")
    version: str | None = Field(default=None, description="Version requirement")
    operator: str = Field(default="=", description="Version operator (=, >=, >, <, <=)")


class SyncTask(SQLModel, table=True):
    """Background sync task model."""

    id                : str              = Field(primary_key=True, description="Unique task identifier")
    status            : SyncTaskStatus   = Field(default=SyncTaskStatus.PENDING, description="Current task status")
    created_at        : datetime         = Field(description="When task was created")
    started_at        : datetime | None  = Field(default=None, description="When task started executing")
    completed_at      : datetime | None  = Field(default=None, description="When task finished (success or failure)")
    progress          : int              = Field(default=0, description="Progress percentage 0-100")
    current_step      : str              = Field(default="", description="Description of current operation")
    log_file_path     : str | None       = Field(default=None, description="Path to task log file")
    error_message     : str | None       = Field(default=None, description="Error message if task failed")
    servers_processed : int              = Field(default=0, description="Number of servers synced so far")
    total_servers     : int              = Field(default=0, description="Total servers to sync")



class Server(SQLModel, table=True):
    """MCP server configuration that persists to the database

    Contains all of the information needed to support, install, and run an MCP server.

    """
    __tablename__ = "servers"

    id              : str                      = Field(primary_key=True, description="Unique server identifier")
    name            : str                      = Field(description="Server name")

    
    transport       : MCPServerTransport       = Field(description="Transport type for MCP server")
    url             : str | None               = Field(default=None, description="URL for HTTP/SSE transport")
    command         : str | None               = Field(default=None, description="Command to run the server (for stdio transport)")
    arguments       : list[str]                = Field(sa_column=Column(JSON), default_factory=list, description="Arguments")
    port            : int | None               = Field(default=None, description="Port number for the server")
    envs            : dict[str, str]           = Field(sa_column=Column(JSON), default_factory=dict, description="Environment variables")
    tools           : list[ServerTool]         = Field(sa_column=Column(JSON), default_factory=list, description="Tools/languages")
    task_install    : str | None               = Field(default=None, description="Install task command")
    task_uninstall  : str | None               = Field(default=None, description="Uninstall task command")
    autostart       : bool                     = Field(default=True, description="Whether the program should start automatically when supervisord starts")
    autorestart     : str                      = Field(default="unexpected", description="When to restart the program")
    priority        : int                      = Field(default=999, description="Priority of the program")
    startsecs       : int                      = Field(default=1, description="Number of seconds the program needs to stay running to consider the start successful")
    startretries    : int                      = Field(default=3, description="Number of times to retry starting the program")
    stopsignal      : str                      = Field(default="TERM", description="Signal to send to stop the program")
    stopwaitsecs    : int                      = Field(default=10, description="Number of seconds to wait for the program to stop before sending KILL")
    log_level       : LogLevel                 = Field(default=LogLevel.INFO, description="Log level")
    stdout_logfile          : str | None = Field(default=None, description="Path to the stdout log file")
    stdout_logfile_maxbytes : int        = Field(default=50_000_000, description="Maximum size of the stdout log file before rotation")
    stdout_logfile_backups  : int        = Field(default=10, description="Number of stdout log file backups to keep")
    redirect_stderr         : bool       = Field(default=True, description="Whether to redirect stderr to stdout")
    stderr_logfile          : str | None = Field(default=None, description="Path to the stderr log file")
    stderr_logfile_maxbytes : int        = Field(default=50_000_000, description="Maximum size of the stderr log file before rotation")
    stderr_logfile_backups  : int        = Field(default=10, description="Number of stderr log file backups to keep")
    created_at      : datetime | None          = Field(default=None, description="Creation timestamp")
    updated_at      : datetime | None          = Field(default=None, description="Last update timestamp")
    synced_at       : datetime | None          = Field(default=None, description="Last sync timestamp")

    def get_supervisor_conf(self) -> SupervisorProgramConfig:
        """Gets the supervisord program configuration for this server."""
        return SupervisorProgramConfig(
            name=self.name,
            command="mise run start",
            directory="/app/servers/" + self.id,
            autostart=self.autostart,
            autorestart=self.autorestart,
            priority=self.priority,
            startsecs=self.startsecs,
            startretries=self.startretries,
            stopsignal=self.stopsignal,
            stopwaitsecs=self.stopwaitsecs,
            stdout_logfile=self.stdout_logfile,
            stdout_logfile_maxbytes=self.stdout_logfile_maxbytes,
            stdout_logfile_backups=self.stdout_logfile_backups,
            stderr_logfile=self.stderr_logfile,
            stderr_logfile_maxbytes=self.stderr_logfile_maxbytes,
            stderr_logfile_backups=self.stderr_logfile_backups,
            redirect_stderr=self.redirect_stderr,
            environment=self.envs
        )

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

class CommandResult(BaseModel):
    """Standard command return model."""
    stdout: str = Field(default="", description="Standard output from command")
    stderr: str = Field(default="", description="Standard error from command")
    returncode: int = Field(default=0, description="Return code from command")

    def is_success(self) -> bool: return self.returncode == 0
    def is_failure(self) -> bool: return self.returncode != 0

    @property
    def combined(self) -> str:
        return self.stdout + "\n" + self.stderr

class ServerDirectory(BaseModel):
    """Server directory manager - creates, represents, and syncs server directories and files.

    - /app/servers/{server_id}
        - mcpServers.json
        - server.py
        - supervisord.conf
        - mise.toml
    """

    path: Path = Field(..., description="Base path for MCP servers")
    server_config: Any = Field(..., description="MCP server configuration")

    mise_toml_file: MiseTomlFile
    fastmcp_server_proxy_server_file: FastMcpServerProxyServerFile
    supervisord_program_config: SupervisorProgramConfig
    mcp_servers_json_file: McpServersJsonFile

    @classmethod
    def from_server_config(cls, server_config: Server):
        """
        Create McpServerDirectory from MCPServerConfig.
        """
        
        path = Path(get_settings().mcp_server_path) / server_config.id

        server_config = Server.model_validate_json(server_config.model_dump_json())

        supervisord_program_config = SupervisorProgramConfig(
            name=server_config.name,
            command="mise run start",
            directory=str(path),
            autostart=server_config.autostart,
            autorestart=server_config.autorestart,
            priority=server_config.priority,
            startsecs=server_config.startsecs,
            startretries=server_config.startretries,
            stopsignal=server_config.stopsignal,
            stopwaitsecs=server_config.stopwaitsecs,
            stdout_logfile=server_config.stdout_logfile,
            stdout_logfile_maxbytes=server_config.stdout_logfile_maxbytes,
            stdout_logfile_backups=server_config.stdout_logfile_backups,
            stderr_logfile=server_config.stderr_logfile,
            stderr_logfile_maxbytes=server_config.stderr_logfile_maxbytes,
            stderr_logfile_backups=server_config.stderr_logfile_backups,
            redirect_stderr=server_config.redirect_stderr,
            environment=server_config.envs
        )


        data = {
            "path": path,
            "server_config": server_config,
            "mise_toml_file": MiseTomlFile.from_mcp_server_config(server_config),
            "fastmcp_server_proxy_server_file": FastMcpServerProxyServerFile.from_mcp_server_config(server_config, json_file_path=os.path.join(path, "mcpServers.json")),
            "supervisord_program_config": supervisord_program_config,
            "mcp_servers_json_file": McpServersJsonFile.from_mcp_server_configs([server_config])
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


        if logger: logger.info(f"Starting MISE tool installation for server: {ident}")
        cmd_return = self.run_mise_install()
        if cmd_return.is_failure():
            if logger: logger.error(f"Mise install failed for server {ident}:\n{cmd_return.combined}")
            raise RuntimeError(f"Mise install failed for server {ident}:\n{cmd_return.combined}")
        else:
            if logger: logger.info(f"Mise install output for server {ident}:\n{cmd_return.combined}")

        if logger: logger.info(f"Starting MISE task \"install\" for server: {ident}")
        cmd_return = self.run_mise_task_install()
        if cmd_return.is_failure():
            if logger: logger.error(f"Mise install task failed for server {ident}:\n{cmd_return.combined}")
            raise RuntimeError(f"Mise install task failed for server {ident}:\n{cmd_return.combined}")
        else:
            if logger: logger.info(f"Mise install task output for server {ident}:\n{cmd_return.combined}")


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
        (self.path / "supervisord.conf").write_text(str(self.supervisord_program_config))
        (self.path / "mise.toml").write_text(str(self.mise_toml_file))


    def run_mise_install(self, timeout: int = 300) -> CommandResult:
        try:

            env = {
                # Allows the mise.toml file to be used.
                "MISE_TRUSTED_CONFIG_PATHS": str(self.path),
                **os.environ
            }

            # Change to server directory and run mise install (installs tools)
            result = subprocess.run(
                ["mise", "install", "--verbose"],
                cwd=str(self.path),
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env
            )

            if result.returncode != 0:
                raise RuntimeError(f"Failed to install mise tools: {result.stderr}")

            result = CommandResult(
                stdout=result.stdout or "",
                stderr=result.stderr or "",
                returncode=result.returncode
            )

            return result
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to install mise tools: {e.stderr}") from e
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(f"Mise install timed out after {timeout} seconds") from e



    def run_mise_task_install(self, timeout: int = 300) -> CommandResult:
        """Run the 'install' task defined in mise.toml, if it exists.

        Args:
            timeout: Maximum time in seconds to allow the install task to run.
        """

        if not self.mise_toml_file.has_task("install"):
            return CommandResult( stdout="", stderr="", returncode=0 )

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

        return CommandResult(
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
            "--host", "0.0.0.0",
            "--port", str(self.server_config.port),
            "--log-level", self.server_config.log_level,
            "--transport", "http",
            "--project", str(self.path),
            "--no-banner"
        ]


    def get_supervisor_program_command(self) -> List[str]:
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
        if self.server_config.transport == MCPServerTransport.STDIO:
            command = self.server_config.command
            if command in ["pipx"]:
                self.mise_toml_file.ensure_tool("python")

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
                self.mise_toml_file.ensure_tool("node", version="lts")

        # == Supervisord ==

        # set supervisord directory to the server path
        self.supervisord_program_config.directory = str(self.path)

        # set supervisord environment variable to allow mise to use the mise.toml in this directory
        self.supervisord_program_config.environment["MISE_TRUSTED_CONFIG_PATHS"] = str(self.path)

        # we need to set the run command on supervisord to use mise run
        self.supervisord_program_config.command = " ".join(self.get_supervisor_program_command())


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
        (self.path / "supervisord.conf").write_text(str(self.supervisord_program_config))
        (self.path / "mise.toml").write_text(str(self.mise_toml_file))
