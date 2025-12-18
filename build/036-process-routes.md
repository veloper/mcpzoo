# Phase 036: Process Routes

## Objective

Implement FastAPI routes for managing supervisor processes.

## Prerequisites

- Phase 031 (authentication) completed
- Phase 033 (supervisor API) completed

## Steps

### 3.1: Implement routers/processes.py (Process Management)

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

## Verification Checklist

- [ ] `backend/src/backend/routers/processes.py` created
- [ ] Process list endpoint works
- [ ] Process start/stop endpoints work
- [ ] Process status endpoint works
- [ ] Authentication required for all endpoints

## Next Step

Proceed to [037-main-app-and-utilities.md](./037-main-app-and-utilities.md)
