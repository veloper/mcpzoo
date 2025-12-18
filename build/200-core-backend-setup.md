# Phase 200: Core Backend Setup

## Objective

Implement core backend components: settings, Pydantic models, and TinyDB database wrapper.

## Prerequisites

- Phase 100 completed
- `backend/src/backend/` directory structure created
- `pyproject.toml` configured and `uv sync` successful

## Steps

### 2.1: Implement settings.py (Configuration)

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

### 2.2: Implement models.py (Pydantic Models)

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

### 2.3: Implement auth.py (JWT Authentication)

**Key Implementation**: JWT tokens have a **rolling window** — each successful use extends expiry to 7 days from now.

Create `backend/src/backend/auth.py`:

```python
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials

from .settings import settings
from .models import TokenData

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer scheme
security = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token with rolling window expiry.
    
    Tokens expire in 7 days. Each use extends the expiry to 7 days from now.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.jwt_expiration_days
        )
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    return encoded_jwt


def verify_token(credentials: HTTPAuthCredentials = Depends(security)) -> str:
    """Verify JWT token and refresh expiry on each use (rolling window).
    
    If token is valid, refresh it to expire 7 days from now.
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
        token_data = TokenData(sub=username)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    return token_data.sub


def authenticate_user(username: str, password: str) -> bool:
    """Authenticate user against configured credentials."""
    return (
        username == settings.app_username
        and password == settings.app_password
    )
```

---

### 2.2: Create Database Wrapper (backend/src/backend/tinydb.py)

Create `backend/src/backend/tinydb.py`:

**Key Features**:
- Thread-safe ID generation with mutex (auto-incrementing integers)
- Server configs stored as-is, awaiting sync operation
- No automatic file/directory creation
```python
from tinydb import TinyDB, Query
from pathlib import Path
from typing import Any, Dict, List, Optional
from .settings import settings


class Database:
    """TinyDB wrapper."""
    
    def __init__(self):
        """Initialize database."""
        db_path = Path(settings.tinydb_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db = TinyDB(str(db_path))
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Ensure required tables exist."""
        # Tables auto-create on first insert
        # Initialize with default tables
        for table_name in ["servers", "processes", "logs"]:
            if table_name not in self.db.tables():
                self.db.table(table_name)
    
    def insert_server(self, server_data: Dict[str, Any]) -> int:
        """Insert MCP server config."""
        table = self.db.table("servers")
        return table.insert(server_data)
    
    def get_server(self, server_id: int) -> Optional[Dict]:
        """Get server by ID."""
        table = self.db.table("servers")
        Server = Query()
        result = table.get(Server.id == server_id)
        return result.dict() if result else None
    
    def get_all_servers(self) -> List[Dict]:
        """Get all servers."""
        table = self.db.table("servers")
        return [doc for doc in table.all()]
    
    def update_server(self, server_id: int, data: Dict[str, Any]) -> bool:
        """Update server."""
        table = self.db.table("servers")
        Server = Query()
        results = table.update(data, Server.id == server_id)
        return len(results) > 0
    
    def delete_server(self, server_id: int) -> bool:
        """Delete server."""
        table = self.db.table("servers")
        Server = Query()
        removed = table.remove(Server.id == server_id)
        return len(removed) > 0
    
    def close(self):
        """Close database."""
        self.db.close()


# Global database instance
db = Database()
```

---

### 2.5: Implement supervisor_api.py (Supervisord Integration)

Create `backend/src/backend/supervisor_api.py`:

```python
import subprocess
from typing import Dict, List, Optional
from .utils.shell import run_command


class SupervisorAPI:
    """Wrapper around supervisorctl."""
    
    def __init__(self, socket_file: str = "/var/run/supervisor.sock"):
        """Initialize supervisor API."""
        self.socket_file = socket_file
    
    def _supervisorctl(self, *args) -> str:
        """Run supervisorctl command."""
        cmd = ["supervisorctl", "-s", f"unix://{self.socket_file}"] + list(args)
        result = run_command(cmd)
        return result
    
    def status(self) -> Dict[str, str]:
        """Get status of all processes."""
        output = self._supervisorctl("status")
        result = {}
        for line in output.strip().split("\n"):
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 2:
                name = parts[0]
                state = parts[1]
                result[name] = state
        return result
    
    def start(self, program: str) -> bool:
        """Start a program."""
        try:
            self._supervisorctl("start", program)
            return True
        except:
            return False
    
    def stop(self, program: str) -> bool:
        """Stop a program."""
        try:
            self._supervisorctl("stop", program)
            return True
        except:
            return False
    
    def restart(self, program: str) -> bool:
        """Restart a program."""
        try:
            self._supervisorctl("restart", program)
            return True
        except:
            return False
    
    def reread(self) -> bool:
        """Reread config files."""
        try:
            self._supervisorctl("reread")
            return True
        except:
            return False
    
    def update(self) -> bool:
        """Update supervisord."""
        try:
            self._supervisorctl("update")
            return True
        except:
            return False


supervisor = SupervisorAPI()
```

---

### 2.6: Implement utils/shell.py (Shell Command Execution)

Create `backend/src/backend/utils/shell.py`:

```python
import subprocess
from typing import List


def run_command(
    cmd: List[str],
    cwd: str = None,
    timeout: int = 30,
    check: bool = True,
) -> str:
    """
    Run a shell command and return output.
    
    Args:
        cmd: Command and arguments as list
        cwd: Working directory
        timeout: Command timeout in seconds
        check: Raise exception if command fails
    
    Returns:
        Command output as string
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            timeout=timeout,
            capture_output=True,
            text=True,
            check=check,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        if check:
            raise
        return e.stderr
```

---

### 2.7: Implement utils/logging.py (Logging Setup)

Create `backend/src/backend/utils/logging.py`:

```python
import logging
from .settings import settings


def setup_logging():
    """Configure application logging."""
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger(__name__)


logger = setup_logging()
```

---

### 2.8: Implement routers/auth.py (Authentication Routes)

Create `backend/src/backend/routers/auth.py`:

```python
from fastapi import APIRouter, HTTPException, status
from ..models import LoginRequest, LoginResponse
from ..auth import authenticate_user, create_access_token, verify_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login with username and password."""
    if not authenticate_user(request.username, request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    
    access_token = create_access_token(data={"sub": request.username})
    return LoginResponse(access_token=access_token)


@router.post("/logout")
async def logout():
    """Logout (client-side token removal)."""
    return {"message": "Logged out successfully"}


@router.get("/verify")
async def verify(username: str = Depends(verify_token)):
    """Verify current token."""
    return {"username": username}
```

---

---

### 2.7: Create Sync Processes Module (backend/src/backend/sync_processes.py)

**CRITICAL MODULE**: This is the ONLY place where server configs are written to disk.

When called:
1. **Per-server directories**: Creates `/app/servers/{server_name}/` for each server
2. **`.mise.toml` generation**: Generates `.mise.toml` in each server directory with `[tools]` section from config
3. **Task execution**: Runs `task_install` from `.mise.toml` (if specified in ServerConfig)
4. **Supervisord config**: Generates `/etc/supervisor/conf.d/mcp_{server_name}.conf`
5. **Group restart**: Restarts supervisord `group:mcp_servers`

**To uninstall a server**:
- Delete server config from DB (via DELETE endpoint)
- Click "Sync Processes" (removes files from `/app/servers/{name}/`)
- No need to manually remove directories

All errors logged to `/var/log/supervisor/` via supervisord. Detailed error messages in response.

---

### 2.9: Implement routers/servers.py (Servers CRUD)

Create `backend/src/backend/routers/servers.py`:

```python
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from datetime import datetime
from ..models import MCPServerConfig
from ..auth import verify_token
from ..tinydb import db

router = APIRouter(prefix="/api/servers", tags=["servers"])


@router.get("", response_model=List[dict])
async def list_servers(username: str = Depends(verify_token)):
    """List all MCP servers."""
    return db.get_all_servers()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_server(
    server: MCPServerConfig,
    username: str = Depends(verify_token),
):
    """Create a new MCP server."""
    server_dict = server.dict()
    server_dict["created_at"] = datetime.now().isoformat()
    server_dict["updated_at"] = datetime.now().isoformat()
    server_id = db.insert_server(server_dict)
    return {"id": server_id, **server_dict}


@router.get("/{server_id}", response_model=dict)
async def get_server(
    server_id: int,
    username: str = Depends(verify_token),
):
    """Get specific server."""
    server = db.get_server(server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        )
    return server


@router.put("/{server_id}")
async def update_server(
    server_id: int,
    server: MCPServerConfig,
    username: str = Depends(verify_token),
):
    """Update server configuration."""
    if not db.get_server(server_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        )
    
    server_dict = server.dict()
    server_dict["updated_at"] = datetime.now().isoformat()
    db.update_server(server_id, server_dict)
    return {"id": server_id, **server_dict}


@router.get("/{server_id}/logs")
async def get_server_logs(
    server_id: int,
    type: str = "stdout",
    username: str = Depends(verify_token),
):
    """Get logs for a specific server.
    
    Type can be 'stdout' or 'stderr'.
    Returns last 100 lines of the requested logfile.
    """
    server = db.get_server(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    log_file = f"/var/log/supervisor/mcp_{server['name']}_{type}.log"
    
    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()
            # Return last 100 lines
            content = ''.join(lines[-100:])
        
        return {
            "server_name": server['name'],
            "type": type,
            "content": content,
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Log file not found for {type}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading logs: {str(e)}")


@router.delete("/{server_id}", status_code=204)
async def delete_server(
    server_id: int,
    username: str = Depends(verify_token),
):
    """Delete server configuration."""
    if not db.get_server(server_id):
        raise HTTPException(
            status_code=404,
            detail="Server not found",
        )
    db.delete_server(server_id)
    return None


@router.post("/sync")
async def sync_processes(username: str = Depends(verify_token)):
    """
    CRITICAL: Write all server configs to disk and restart supervisord MCP group.
    
    Changes to server configs don't take effect until this is called.
    This endpoint:
    1. Writes config files to /app/servers/
    2. Generates supervisord program files
    3. Restarts supervisord group:mcp_servers
    4. Installs MISE dependencies (if needed)
    """
    try:
        from ..sync_processes import sync_mcp_servers
        result = sync_mcp_servers()
        return {
            "status": "success",
            "message": "MCP servers synced and supervisord restarted",
            "details": result,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Sync failed: {str(e)}",
        )
```

---

### 2.10: Implement routers/processes.py (Process Management)

Create `backend/src/backend/routers/processes.py`:

```python
from fastapi import APIRouter, HTTPException, status, Depends
from ..auth import verify_token
from ..supervisor_api import supervisor

router = APIRouter(prefix="/api/processes", tags=["processes"])


@router.get("")
async def list_processes(username: str = Depends(verify_token)):
    """List all supervisor processes."""
    return supervisor.status()


@router.post("/{name}/start")
async def start_process(
    name: str,
    username: str = Depends(verify_token),
):
    """Start process."""
    if not supervisor.start(name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to start {name}",
        )
    return {"status": "started", "process": name}


@router.post("/{name}/stop")
async def stop_process(
    name: str,
    username: str = Depends(verify_token),
):
    """Stop process."""
    if not supervisor.stop(name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to stop {name}",
        )
    return {"status": "stopped", "process": name}


@router.get("/{name}/status")
async def process_status(
    name: str,
    username: str = Depends(verify_token),
):
    """Get process status."""
    status = supervisor.status()
    if name not in status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Process {name} not found",
        )
    return {"process": name, "status": status[name]}
```

---

### 2.11: Implement main.py (FastAPI Application)

Create `backend/src/backend/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .routers import auth, servers, processes
from .utils.logging import logger

app = FastAPI(title="MCPZoo", version="0.1.0")

# CORS middleware - Allow frontend to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://localhost"],  # Frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(servers.router)
app.include_router(processes.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/home")
async def home():
    """Home page metadata."""
    return {
        "name": "MCPZoo",
        "version": "0.1.0",
        "description": "MCP Server Management",
    }


# Serve static files from frontend/dist
static_path = Path(__file__).parent.parent.parent.parent / "frontend" / "dist"
if static_path.exists():
    app.mount("/", StaticFiles(directory=str(static_path), html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
```

---

### 2.12: Create Tests (Optional)

Create `backend/tests/test_auth.py`:

```python
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_check():
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_login_success():
    """Test successful login."""
    # Note: use actual credentials from .env
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "changeme123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_failure():
    """Test failed login."""
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "wrong"},
    )
    assert response.status_code == 401
```

---

## Verification Checklist

After completing Phase 2:

- [ ] All Python files created in `backend/src/backend/`
- [ ] `uvicorn backend.main:app` runs without errors
- [ ] `/health` endpoint returns `{"status": "healthy"}`
- [ ] `/api/auth/login` endpoint exists and works
- [ ] `/api/servers` endpoints exist
- [ ] `/api/processes` endpoints exist
- [ ] JWT authentication working
- [ ] TinyDB initialized at configured path
- [ ] Supervisord API wrapper functional

## Next Step

Once verified, proceed to [Phase 3: Frontend Implementation](./03-frontend-implementation.md)
