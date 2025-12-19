import uuid

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from src.backend.auth import verify_token
from src.backend.models import MCPServerConfig
from src.backend.services.database import DatabaseService, get_database_service
from src.backend.services.logging import logger
from src.backend.services.supervisord import SupervisordService, get_supervisord_service
from tinydb import Query


router = APIRouter(prefix="/api/servers", tags=["servers"])


@router.get("", response_model=List[dict])
async def list_servers(
    username: str = Depends(verify_token),
    db_service: DatabaseService = Depends(get_database_service),
):
    """List all MCP servers."""
    logger.info(f"list_servers called by user: {username}")
    try:
        async with db_service as db:
            servers_table = db.table('servers')
            servers = servers_table.all()
            logger.info(f"Found {len(servers)} servers")
            return servers
    except Exception as e:
        logger.error(f"Error in list_servers: {str(e)}")
        raise


@router.post("/sync")
async def sync_processes(
    username: str = Depends(verify_token),
    db_service: DatabaseService = Depends(get_database_service),
    supervisor_service: SupervisordService = Depends(get_supervisord_service),
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

    # Always assign port for all transports (ignore any port in request)
    transport = server_dict.get("transport")
    if transport:
        # Get all existing servers to check assigned ports
        async with db_service as db:
            servers_table = db.table('servers')
            existing_servers = servers_table.all()

        # Collect ports already assigned to other servers
        assigned_ports = set()
        for existing_server in existing_servers:
            if existing_server.get("port"):
                assigned_ports.add(existing_server["port"])

        # Find first available port in 8100-8199 range
        for port in range(8100, 8200):  # 8100 to 8199 inclusive
            if port not in assigned_ports:
                server_dict["port"] = port
                break
        else:
            # All ports in range are assigned
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No available ports in range 8100-8199",
            )

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
    logger.info(f"get_server called by user: {username} for server_id: {server_id}")
    try:
        async with db_service as db:
            servers_table = db.table('servers')
            Server = Query()
            server = servers_table.get(Server.id == server_id)

        if not server:
            logger.warning(f"Server not found: {server_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Server not found",
            )

        logger.info(f"Successfully retrieved server: {server_id}")
        return server
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_server for {server_id}: {str(e)}")
        raise


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
        existing_server = servers_table.get(Server.id == server_id)
        if not existing_server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Server not found",
            )

        server_dict = server.copy() if isinstance(server, dict) else server.model_dump()
        server_dict["id"] = server_id
        server_dict["updated_at"] = datetime.now().isoformat()

        # Always assign port for all transports (ignore any port in request)
        transport = server_dict.get("transport")
        if transport:
            logger.info("Auto-assigning port for update")
            # Get all existing servers to check assigned ports
            existing_servers = servers_table.all()

            # Collect ports already assigned to other servers (exclude current server)
            assigned_ports = set()
            for srv in existing_servers:
                if srv.get("id") != server_id and srv.get("port"):
                    assigned_ports.add(srv["port"])

            logger.info(f"Assigned ports: {assigned_ports}")

            # Find first available port in 8100-8199 range
            for port in range(8100, 8200):  # 8100 to 8199 inclusive
                if port not in assigned_ports:
                    server_dict["port"] = port
                    logger.info(f"Assigned port {port}")
                    break
            else:
                # All ports in range are assigned
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="No available ports in range 8100-8199",
                )

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
    srv: SupervisordService = Depends(get_supervisord_service),
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
    srv: SupervisordService = Depends(get_supervisord_service),
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
    srv: SupervisordService = Depends(get_supervisord_service),
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
    srv: SupervisordService = Depends(get_supervisord_service),
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

@router.get("/mcp-config", response_model=dict)
async def get_mcp_config(
    username: str = Depends(verify_token),
    db_service: DatabaseService = Depends(get_database_service),
):
    """Generate mcpServer.json configuration for FastMCP proxy server."""
    async with db_service as db:
        servers_table = db.table('servers')
        servers = servers_table.all()

    mcp_servers = {}

    for server in servers:
        server_name = server.get("name", "")
        transport = server.get("transport", "")
        port = server.get("port")

        if not server_name or not transport:
            continue

        if transport == "stdio":
            # For stdio servers, FastMCP runs the actual MCP server command
            command = server.get("command", "")
            arguments = server.get("arguments", [])

            if command:
                # Build the command array as configured in MCPZoo
                cmd_parts = [command]
                if arguments:
                    cmd_parts.extend(arguments)

                mcp_servers[server_name] = {
                    "command": cmd_parts[0],
                    "args": cmd_parts[1:] if len(cmd_parts) > 1 else []
                }

        elif transport in ["http", "sse"] and port:
            # For HTTP/SSE servers, use the standard MCP remote server format
            # FastMCP can connect directly to the running MCP server
            base_url = f"http://localhost:{port}"

            mcp_servers[server_name] = {
                "url": base_url,
                "transport": transport
            }

    return {"mcpServers": mcp_servers}
