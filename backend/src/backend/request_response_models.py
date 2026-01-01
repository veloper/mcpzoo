from pydantic import BaseModel, Field

from src.backend.enums import LogLevel
from src.backend.mcp import MCPServerTransport


class ServerTool(BaseModel):
    """Tool/language requirement with version for server configuration."""
    name: str = Field(description="Tool/language name")
    version: str | None = Field(default=None, description="Version requirement")


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
    sub: str | None = None
    exp: int | None = None


class HomeSummary(BaseModel):
    """Summary statistics for the home page."""
    total_servers: int
    running_processes: int
    total_processes: int


class HomeResponse(BaseModel):
    """Response for the home page endpoint."""
    name: str
    version: str
    description: str
    summary: HomeSummary
    servers: list
    processes: list
