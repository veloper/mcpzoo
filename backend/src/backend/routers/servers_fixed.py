from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from datetime import datetime
import uuid
from tinydb import Query
from src.backend.models import MCPServerConfig
from src.backend.auth import verify_token
from src.backend.services.database import get_database_service, DatabaseService
from src.backend.services.supervisord import get_supervisord_service

router = APIRouter(prefix="/api/servers", tags=["servers"])


@router.get("", response_model=List[dict])
async def list_servers(
    username: str = Depends(verify_token),
    db_service: DatabaseService = Depends(get_database_service),
):
    """List all MCP servers."""
    async with db_service as db:
        servers_table = db.table('servers')
        return servers_table.all()


@router.post("/sync")
async def sync_processes(
    username: str = Depends(verify_token),
    db_service: DatabaseService = Depends(get_database_service),
    supervisor_service = Depends(get_supervisord_service),
):
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
        async with db_service as db:
            servers_table = db.table('servers')
            servers = servers_table.all()
        
        # Reread supervisord config and update
        await supervisor_service.reread_config()
        await supervisor_service.update()
        
        return {
            "status": "success",
            "message": "MCP servers synced and supervisord restarted",
            "details": {"servers_synced": len(servers)},
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Sync failed: {str(e)}",
        )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_server(
    server: dict,
    username: str = Depends(verify_token),
    db_service: DatabaseService = Depends(get_database_service),
):
    """Create a new MCP server."""
    server_dict = server.copy() if isinstance(server, dict) else server.model_dump()
    server_id = str(uuid.uuid4())
    server_dict["id"] = server_id
    server_dict["created_at"] = datetime.now().isoformat()
    server_dict["updated_at"] = datetime.now().isoformat()
    async with db_service as db:
        servers_table = db.table('servers')
        servers_table.insert(server_dict)
    return {"id": server_id, **server_dict}


@router.get("/{server_id}", response_model=dict)
async def get_server(
    server_id: str,
    username: str = Depends(verify_token),
    db_service: DatabaseService = Depends(get_database_service),
):
    """Get specific server."""
    async with db_service as db:
        servers_table = db.table('servers')
        Server = Query()
        server = servers_table.get(Server.id == server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        )
    return server


@router.put("/{server_id}")
async def update_server(
    server_id: str,
    server: dict,
    username: str = Depends(verify_token),
    db_service: DatabaseService = Depends(get_database_service),
):
    """Update server configuration."""
    async with db_service as db:
        servers_table = db.table('servers')
        Server = Query()
        if not servers_table.get(Server.id == server_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Server not found",
            )
        
        server_dict = server.copy() if isinstance(server, dict) else server.model_dump()
        server_dict["id"] = server_id
        server_dict["updated_at"] = datetime.now().isoformat()
        servers_table.update(server_dict, Server.id == server_id)
    return {"id": server_id, **server_dict}


@router.get("/{server_id}/logs")
async def get_server_logs(
    server_id: str,
    type: str = "stdout",
    username: str = Depends(verify_token),
    db_service: DatabaseService = Depends(get_database_service),
):
    """Get logs for a specific server.
    
    Type can be 'stdout' or 'stderr'.
    Returns last 100 lines of the requested logfile.
    """
    async with db_service as db:
        servers_table = db.table('servers')
        Server = Query()
        server = servers_table.get(Server.id == server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    log_file = f"/var/log/supervisor/mcp_{server['name']}_{type}.log"
    
    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()
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


@router.post("/{server_id}/start")
async def start_server(
    server_id: str,
    username: str = Depends(verify_token),
    db_service: DatabaseService = Depends(get_database_service),
    srv = Depends(get_supervisord_service),
):
    """Start MCP server process."""
    async with db_service as db:
        servers_table = db.table('servers')
        Server = Query()
        server = servers_table.get(Server.id == server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        )
    
    process_name = f"mcp_{server['name']}"
    try:
        if not srv.start_process(process_name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to start server {server['name']}",
            )
        return {"status": "started", "server": server['name']}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting server: {str(e)}"
        )


@router.post("/{server_id}/stop")
async def stop_server(
    server_id: str,
    username: str = Depends(verify_token),
    db_service: DatabaseService = Depends(get_database_service),
    srv = Depends(get_supervisord_service),
):
    """Stop MCP server process."""
    async with db_service as db:
        servers_table = db.table('servers')
        Server = Query()
        server = servers_table.get(Server.id == server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        )
    
    process_name = f"mcp_{server['name']}"
    try:
        if not srv.stop_process(process_name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to stop server {server['name']}",
            )
        return {"status": "stopped", "server": server['name']}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error stopping server: {str(e)}"
        )


@router.post("/{server_id}/restart")
async def restart_server(
    server_id: str,
    username: str = Depends(verify_token),
    db_service: DatabaseService = Depends(get_database_service),
    srv = Depends(get_supervisord_service),
):
    """Restart MCP server process."""
    async with db_service as db:
        servers_table = db.table('servers')
        Server = Query()
        server = servers_table.get(Server.id == server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        )
    
    process_name = f"mcp_{server['name']}"
    try:
        if not (srv.stop_process(process_name) and srv.start_process(process_name)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to restart server {server['name']}",
            )
        return {"status": "restarted", "server": server['name']}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error restarting server: {str(e)}"
        )


@router.get("/{server_id}/status")
async def get_server_status(
    server_id: str,
    username: str = Depends(verify_token),
    db_service: DatabaseService = Depends(get_database_service),
    srv = Depends(get_supervisord_service),
):
    """Get current status of MCP server process."""
    async with db_service as db:
        servers_table = db.table('servers')
        Server = Query()
        server = servers_table.get(Server.id == server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        )
    
    process_name = f"mcp_{server['name']}"
    try:
        proc = srv.get_process_status(process_name)
        if not proc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Process {process_name} not found",
            )
        return {
            "server": server['name'],
            "process": process_name,
            "status": proc.state,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting server status: {str(e)}"
        )

@router.delete("/{server_id}", status_code=204)
async def delete_server(
    server_id: str,
    username: str = Depends(verify_token),
    db_service: DatabaseService = Depends(get_database_service),
):
    """Delete server configuration."""
    async with db_service as db:
        servers_table = db.table('servers')
        Server = Query()
        if not servers_table.get(Server.id == server_id):
            raise HTTPException(
                status_code=404,
                detail="Server not found",
            )
        servers_table.remove(Server.id == server_id)
    return None
