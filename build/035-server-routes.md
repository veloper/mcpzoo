# Phase 035: Server Routes

## Objective

Implement FastAPI routes for managing MCP server configurations and syncing processes.

## Prerequisites

- Phase 031 (authentication) completed
- Phase 032 (database wrapper) completed
- Phase 034 (sync module) completed

## Steps

### 3.1: Implement routers/servers.py (Servers CRUD)

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

## Verification Checklist

- [ ] `backend/src/backend/routers/servers.py` created
- [ ] All CRUD endpoints implemented
- [ ] Authentication required for all endpoints
- [ ] Sync endpoint callable

## Next Step

Proceed to [036-process-routes.md](./036-process-routes.md)
