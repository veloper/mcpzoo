# Phase 030: Settings and Models

## Objective

Implement configuration settings and Pydantic data models for the backend.

## Prerequisites

- Phase 100 completed
- `backend/src/backend/` directory structure created
- `pyproject.toml` configured and `uv sync` successful

## Steps

### 3.1: Implement settings.py (Configuration)

Create `backend/src/backend/settings.py`:

**CRITICAL**: APP_USERNAME and APP_PASSWORD are **REQUIRED** — no defaults allowed. Container must fail if not provided.

```python
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from .env file."""
    
    # Application - REQUIRED (no defaults)
    app_username: str  # Required, no default
    app_password: str  # Required, no default
    
    # JWT Configuration
    jwt_secret: str = "dev-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_expiration_days: int = 7  # 1 week
    jwt_token_refresh_days: int = 7  # Rolling window: extends to 7 days from last use
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def __init__(self, **data):
        super().__init__(**data)
        # Validate required fields
        if not self.app_username or not self.app_password:
            raise ValueError("APP_USERNAME and APP_PASSWORD are required")
    # JWT
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # Server
    fastapi_host: str = "127.0.0.1"
    fastapi_port: int = 8001
    
    # Database
    tinydb_path: str = "/app/data/tinydb.json"
    
    # MCP
    mcp_port_min: int = 8100
    mcp_port_max: int = 8999
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
```

---

### 3.2: Implement models.py (Pydantic Models)

Create `backend/src/backend/models.py`:

```python
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import json


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
    group: Optional[str] = None
    
    # Execution
    command: str
    directory: Optional[str] = None
    umask: Optional[str] = None
    user: Optional[str] = None
    
    # Startup
    autostart: bool = True
    autorestart: str = "unexpected"
    startsecs: int = 1
    startretries: int = 3
    priority: int = 999
    
    # Shutdown
    stopsignal: str = "TERM"
    stopwaitsecs: int = 10
    stopasgroup: bool = False
    
    # Logging
    stdout_logfile: Optional[str] = None
    stdout_logfile_maxbytes: int = 50_000_000
    stdout_logfile_backups: int = 10
    stdout_capture_maxbytes: int = 0
    stdout_events_enabled: bool = False
    
    stderr_logfile: Optional[str] = None
    stderr_logfile_maxbytes: int = 50_000_000
    stderr_logfile_backups: int = 10
    stderr_capture_maxbytes: int = 0
    stderr_events_enabled: bool = False
    
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
        lines.append(f"environment={','.join([f'{k}={v}' for k, v in self.environment.items()])}")
        return "\n".join(lines)


class MCPServerConfig(BaseModel):
    """MCP server configuration model."""
    
    id: int
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
```

---

## Verification Checklist

- [ ] `backend/src/backend/settings.py` created
- [ ] `backend/src/backend/models.py` created
- [ ] Settings loads from `.env` with required fields
- [ ] All Pydantic models validate correctly

## Next Step

Proceed to [031-authentication.md](./031-authentication.md)
