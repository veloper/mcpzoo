# Phase 037: Main App and Utilities

## Objective

Implement the FastAPI application entry point and utility modules for shell commands and logging.

## Prerequisites

- Phase 031 (auth routes) completed
- Phase 035 (server routes) completed
- Phase 036 (process routes) completed

## Steps

### 3.1: Implement utils/shell.py (Shell Command Execution)

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

### 3.2: Implement utils/logging.py (Logging Setup)

Create `backend/src/backend/utils/logging.py`:

```python
import logging
from ..settings import settings


def setup_logging():
    """Configure application logging."""
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger(__name__)


logger = setup_logging()
```

### 3.3: Implement main.py (FastAPI Application)

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

### 3.4: Create __init__.py files (Package Initialization)

Create `backend/src/backend/routers/__init__.py`:

```python
from . import auth, servers, processes

__all__ = ["auth", "servers", "processes"]
```

Create `backend/src/backend/utils/__init__.py`:

```python
from . import shell, logging

__all__ = ["shell", "logging"]
```

---

## Verification Checklist

- [ ] `backend/src/backend/utils/shell.py` created
- [ ] `backend/src/backend/utils/logging.py` created
- [ ] `backend/src/backend/routers/__init__.py` created
- [ ] `backend/src/backend/utils/__init__.py` created
- [ ] `backend/src/backend/main.py` created
- [ ] `uvicorn backend.main:app` runs without errors
- [ ] `/health` endpoint returns `{"status": "healthy"}`
- [ ] `/home` endpoint returns metadata

## Next Step

Proceed to [038-tests-and-verification.md](./038-tests-and-verification.md)
