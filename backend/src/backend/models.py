import json, logging, os, re, signal, subprocess

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, field_validator
from sqlalchemy import JSON, Boolean, Column, DateTime, Enum, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.backend.enums import LogLevel, SyncTaskStatus
from src.backend.fast_mcp import FastMcpServerProxyServerFile
from src.backend.mcp import MCPServersJson, MCPServerTransport
from src.backend.mise import MiseToml, MiseTool
from src.backend.settings import get_settings
from src.backend.supervisor import SupervisorProgramConfig


settings = get_settings()


# ===== SQLAlchemy Base and Database Models =====

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


class ServerTool(BaseModel):
    """Tool/language requirement with version for server configuration."""
    name: str = Field(description="Tool/language name")
    version: str | None = Field(default=None, description="Version requirement")

class SyncTaskRecord(Base):
    """Background sync task database record."""
    __tablename__ = "sync_tasks"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    status: Mapped[SyncTaskStatus] = mapped_column(Enum(SyncTaskStatus), default=SyncTaskStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    current_step: Mapped[str] = mapped_column(String, default="")
    log_file_path: Mapped[str | None] = mapped_column(String, default=None)
    error_message: Mapped[str | None] = mapped_column(String, default=None)
    servers_processed: Mapped[int] = mapped_column(Integer, default=0)
    total_servers: Mapped[int] = mapped_column(Integer, default=0)

    def to_pydantic_model(self) -> "SyncTask":
        """Convert SQLAlchemy record to Pydantic model."""
        return SyncTask(
            id=self.id,
            status=self.status,
            created_at=self.created_at,
            started_at=self.started_at,
            completed_at=self.completed_at,
            progress=self.progress,
            current_step=self.current_step,
            log_file_path=self.log_file_path,
            error_message=self.error_message,
            servers_processed=self.servers_processed,
            total_servers=self.total_servers,
        )


class ServerRecord(Base):
    """MCP server configuration database record."""
    __tablename__ = "servers"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)
    transport: Mapped[MCPServerTransport] = mapped_column(Enum(MCPServerTransport))
    url: Mapped[str | None] = mapped_column(String, default=None)
    command: Mapped[str | None] = mapped_column(String, default=None)
    arguments: Mapped[list[str]] = mapped_column(JSON, default=[])
    port: Mapped[int | None] = mapped_column(Integer, default=None)
    envs: Mapped[dict[str, str]] = mapped_column(JSON, default={})
    headers: Mapped[dict[str, str]] = mapped_column(JSON, default={})
    tools: Mapped[list[dict]] = mapped_column(JSON, default=[])
    task_install: Mapped[str | None] = mapped_column(String, default=None)
    task_uninstall: Mapped[str | None] = mapped_column(String, default=None)
    autostart: Mapped[bool] = mapped_column(Boolean, default=True)
    autorestart: Mapped[str] = mapped_column(String, default="unexpected")
    priority: Mapped[int] = mapped_column(Integer, default=999)
    startsecs: Mapped[int] = mapped_column(Integer, default=1)
    startretries: Mapped[int] = mapped_column(Integer, default=3)
    stopsignal: Mapped[str] = mapped_column(String, default="TERM")
    stopwaitsecs: Mapped[int] = mapped_column(Integer, default=10)
    log_level: Mapped[LogLevel] = mapped_column(Enum(LogLevel), default=LogLevel.INFO)
    stdout_logfile: Mapped[str | None] = mapped_column(String, default=None)
    stdout_logfile_maxbytes: Mapped[int] = mapped_column(Integer, default=50_000_000)
    stdout_logfile_backups: Mapped[int] = mapped_column(Integer, default=10)
    redirect_stderr: Mapped[bool] = mapped_column(Boolean, default=True)
    stderr_logfile: Mapped[str | None] = mapped_column(String, default=None)
    stderr_logfile_maxbytes: Mapped[int] = mapped_column(Integer, default=50_000_000)
    stderr_logfile_backups: Mapped[int] = mapped_column(Integer, default=10)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    synced_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)

    def to_pydantic_model(self) -> "Server":
        """Convert SQLAlchemy record to Pydantic model."""
        return Server(
            id=self.id,
            name=self.name,
            transport=self.transport,
            url=self.url,
            command=self.command,
            arguments=self.arguments,
            port=self.port,
            envs=self.envs,
            headers=self.headers,
            tools=[ServerTool(**t) for t in self.tools] if self.tools else [],
            task_install=self.task_install,
            task_uninstall=self.task_uninstall,
            autostart=self.autostart,
            autorestart=self.autorestart,
            priority=self.priority,
            startsecs=self.startsecs,
            startretries=self.startretries,
            stopsignal=self.stopsignal,
            stopwaitsecs=self.stopwaitsecs,
            log_level=self.log_level,
            stdout_logfile=self.stdout_logfile,
            stdout_logfile_maxbytes=self.stdout_logfile_maxbytes,
            stdout_logfile_backups=self.stdout_logfile_backups,
            redirect_stderr=self.redirect_stderr,
            stderr_logfile=self.stderr_logfile,
            stderr_logfile_maxbytes=self.stderr_logfile_maxbytes,
            stderr_logfile_backups=self.stderr_logfile_backups,
            created_at=self.created_at,
            updated_at=self.updated_at,
            synced_at=self.synced_at,
        )


# ===== Pydantic Models =====

class ServerCreateOrUpdateRequest(BaseModel):
    """Input schema for creating or updating servers."""
    name: str
    transport: MCPServerTransport
    url: str | None = None
    command: str | None = None
    arguments: list[str] = Field(default_factory=list)
    port: int | None = None
    envs: dict[str, str] = Field(default_factory=dict)
    headers: dict[str, str] = Field(default_factory=dict)
    tools: list[ServerTool] = Field(default_factory=list)
    task_install: str | None = None
    task_uninstall: str | None = None
    autostart: bool = True
    autorestart: str = "unexpected"
    priority: int = 999
    startsecs: int = 1
    startretries: int = 3
    stopsignal: str = "TERM"
    stopwaitsecs: int = 10
    log_level: LogLevel = LogLevel.INFO
    stdout_logfile: str | None = None
    stdout_logfile_maxbytes: int = 50_000_000
    stdout_logfile_backups: int = 10
    redirect_stderr: bool = True
    stderr_logfile: str | None = None
    stderr_logfile_maxbytes: int = 50_000_000
    stderr_logfile_backups: int = 10


class Server(BaseModel):
    """Primary Pydantic model for server. Used for API responses and business logic."""
    id: int | None = None
    name: str
    transport: MCPServerTransport
    url: str | None = None
    command: str | None = None
    arguments: list[str] = Field(default_factory=list)
    port: int | None = None
    envs: dict[str, str] = Field(default_factory=dict)
    headers: dict[str, str] = Field(default_factory=dict)
    tools: list[ServerTool] = Field(default_factory=list)
    task_install: str | None = None
    task_uninstall: str | None = None
    autostart: bool = True
    autorestart: str = "unexpected"
    priority: int = 999
    startsecs: int = 1
    startretries: int = 3
    stopsignal: str = "TERM"
    stopwaitsecs: int = 10
    log_level: LogLevel = LogLevel.INFO
    stdout_logfile: str | None = None
    stdout_logfile_maxbytes: int = 50_000_000
    stdout_logfile_backups: int = 10
    redirect_stderr: bool = True
    stderr_logfile: str | None = None
    stderr_logfile_maxbytes: int = 50_000_000
    stderr_logfile_backups: int = 10
    created_at: datetime | None = None
    updated_at: datetime | None = None
    synced_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator('log_level', mode='before')
    @classmethod
    def validate_log_level(cls, v):
        """Ensure log_level is properly converted to LogLevel enum."""
        if isinstance(v, str):
            try:
                return LogLevel(v.upper())
            except ValueError:
                return LogLevel.INFO
        elif isinstance(v, LogLevel):
            return v
        else:
            return LogLevel.INFO

    def to_sa_record(self) -> ServerRecord:
        """Convert Pydantic model to SQLAlchemy record for persistence."""
        kwargs = dict(
            name=self.name,
            transport=self.transport,
            url=self.url,
            command=self.command,
            arguments=self.arguments,
            port=self.port,
            envs=self.envs,
            headers=self.headers,
            tools=[t.model_dump() for t in self.tools],
            task_install=self.task_install,
            task_uninstall=self.task_uninstall,
            autostart=self.autostart,
            autorestart=self.autorestart,
            priority=self.priority,
            startsecs=self.startsecs,
            startretries=self.startretries,
            stopsignal=self.stopsignal,
            stopwaitsecs=self.stopwaitsecs,
            log_level=self.log_level,
            stdout_logfile=self.stdout_logfile,
            stdout_logfile_maxbytes=self.stdout_logfile_maxbytes,
            stdout_logfile_backups=self.stdout_logfile_backups,
            redirect_stderr=self.redirect_stderr,
            stderr_logfile=self.stderr_logfile,
            stderr_logfile_maxbytes=self.stderr_logfile_maxbytes,
            stderr_logfile_backups=self.stderr_logfile_backups,
            created_at=self.created_at,
            updated_at=self.updated_at,
            synced_at=self.synced_at,
        )
        if self.id is not None:
            kwargs["id"] = self.id
        return ServerRecord(**kwargs)

    def get_supervisor_conf(self) -> SupervisorProgramConfig:
        """Gets the supervisord program configuration for this server."""
        return SupervisorProgramConfig(
            name=self.name,
            command="mise run start",
            directory="/app/servers/" + str(self.id),
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

        mise_tools = [MiseTool(name=t.name, version=t.version) for t in self.tools]

        return MiseToml(
            envs=self.envs,
            tools=mise_tools,
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
                "url": self.url,
                "headers": self.headers
            }

        # Environment variables
        if self.envs:
            if "env" not in servers_dict[self.name]:
                servers_dict[self.name]["env"] = {}
            for key, value in self.envs.items():
                servers_dict[self.name]["env"][key] = value

        return MCPServersJson(mcpServers=servers_dict)

    def get_server_directory_path(self) -> Path:
        """Get the filesystem path for this server's directory."""
        return Path(get_settings().mcp_server_path) / str(self.id)

    def deepcopy(self) -> "Server":
        """Create a deep copy of this Server instance via de/serialization."""
        server_json = self.model_dump_json()
        return Server.model_validate_json(server_json)

    def get_server_directory(self) -> "ServerDirectory":
        """Get the ServerDirectory representation for this server."""
        from src.backend.server_directory import ServerDirectory

        server_config = self.deepcopy()

        return ServerDirectory(
            path=server_config.get_server_directory_path(),
            server_config=server_config,
            mise_toml_file=server_config.get_mise_toml(),
            fastmcp_server_proxy_server_file=server_config.get_fastmcp_server_proxy_file(),
            supervisord_program_config=server_config.get_supervisor_conf(),
            mcp_servers_json_file=server_config.get_mcp_servers_json()
        )


class SyncTask(BaseModel):
    """Primary Pydantic model for background sync tasks."""
    id: int | None = None
    status: SyncTaskStatus = SyncTaskStatus.PENDING
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    progress: int = 0
    current_step: str = ""
    log_file_path: str | None = None
    error_message: str | None = None
    servers_processed: int = 0
    total_servers: int = 0

    model_config = ConfigDict(from_attributes=True)

    def to_sa_record(self) -> SyncTaskRecord:
        """Convert Pydantic model to SQLAlchemy record for persistence."""
        # For new records, don't specify id so SQLite can auto-generate it
        if self.id is None:
            return SyncTaskRecord(
                status=self.status,
                created_at=self.created_at,
                started_at=self.started_at,
                completed_at=self.completed_at,
                progress=self.progress,
                current_step=self.current_step,
                log_file_path=self.log_file_path,
                error_message=self.error_message,
                servers_processed=self.servers_processed,
                total_servers=self.total_servers,
            )
        else:
            # For updates, include the id
            return SyncTaskRecord(
                id=self.id,
                status=self.status,
                created_at=self.created_at,
                started_at=self.started_at,
                completed_at=self.completed_at,
                progress=self.progress,
                current_step=self.current_step,
                log_file_path=self.log_file_path,
                error_message=self.error_message,
                servers_processed=self.servers_processed,
                total_servers=self.total_servers,
            )
