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
from src.backend.mcp import MCPServersJson
from src.backend.mise import MiseToml
# Rebuild ServerDirectory to resolve forward references
from src.backend.server_directory import ServerDirectory
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
    
    __tablename__ = "sync_tasks"

    id                : int | None       = Field(default=None, primary_key=True, sa_column_kwargs={"autoincrement": True}, description="Unique task identifier")
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

    def get_mise_toml(self) -> MiseToml:
        """Gets the mise.toml configuration for this server."""
        tasks = {}
        if self.task_install:
            tasks["install"] = self.task_install
        if self.task_uninstall:
            tasks["uninstall"] = self.task_uninstall

        return MiseToml(
            envs=self.envs,
            tools=self.tools,
            tasks=tasks
        )
        
    def get_fastmcp_server_proxy_file(self) -> FastMcpServerProxyServerFile:
        """Gets the FastMCP server proxy file for this server."""
        return FastMcpServerProxyServerFile(
            server_name=self.name,
            json_file_path=f"/app/servers/{self.id}/mcpServers.json"
        )
        
    def get_mcp_servers_json(self) -> MCPServersJson:
        """Gets the mcpServers.json configuration for this server."""
        servers_dict = {}
        # Transport-specific config
        if self.transport == MCPServerTransport.STDIO:
            servers_dict[self.name] = {
                "type": self.transport,
                "command": self.command,
                "args": self.arguments
            }
        else:
            servers_dict[self.name] = {
                "type": self.transport,
                "url": self.url
            }

        # Environment variables
        if self.envs:
            if "env" not in servers_dict[self.name]:
                    servers_dict[self.name]["env"] = {}
            for key, value in self.envs.items():
                servers_dict[self.name]["env"][key] = value

        return MCPServersJson(mcp_servers=servers_dict)

    def get_server_directory_path(self) -> Path:
        """Get the filesystem path for this server's directory."""
        return Path(get_settings().mcp_server_path) / self.id

    def deepcopy(self) -> "Server":
        """Create a deep copy of this Server instance via de/serialization."""
        server_json = self.model_dump_json()
        return Server.model_validate_json(server_json)

    def get_server_directory(self)  -> "ServerDirectory":
        """Get the ServerDirectory representation for this server."""
        server_config = self.deepcopy()
        
        return ServerDirectory(
            path=server_config.get_server_directory_path(),
            server_config=server_config,
            mise_toml_file=server_config.get_mise_toml(),
            fastmcp_server_proxy_server_file=server_config.get_fastmcp_server_proxy_file(),
            supervisord_program_config=server_config.get_supervisor_conf(),
            mcp_servers_json_file=server_config.get_mcp_servers_json()
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

ServerDirectory.model_rebuild()
