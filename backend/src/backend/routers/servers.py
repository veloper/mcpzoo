import json, uuid

from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from src.backend.auth import verify_token
from src.backend.fast_mcp import FastMcpServerProxyServerFile
from src.backend.mcp import McpServersJsonFile
from src.backend.models import MiseTomlFile, Server, ServerDirectory, timezone
from src.backend.services.database import DatabaseService, get_database_service
from src.backend.services.logging import logger
from src.backend.services.supervisord import SupervisordService, get_supervisord_service
from src.backend.settings import get_settings
from src.backend.supervisor import SupervisorConfFile


settings = get_settings()
router = APIRouter(prefix="/api/servers", tags=["servers"])

def get_next_available_mcp_server_port(db_service: DatabaseService) -> int:
    """
    We make an assumption that ports will go up one past the web_port
    and up to 200.
    """
    web_port = settings.frontend_web_port
    start_port = web_port + 1
    end_port = start_port + 200

    # Get all existing servers to check assigned ports
    with db_service as db:
        existing_servers = db.get_all_servers()

    # Collect ports already assigned to servers
    assigned_ports = set()
    for existing_server in existing_servers:
        if existing_server.get("port"):
            assigned_ports.add(existing_server["port"])

    # make range set of ports, then remove assigned ports
    available_ports = set(range(start_port, end_port + 1))
    available_ports -= assigned_ports
    
    if available_ports:
        return min(available_ports)
    
    # All ports in range are assigned
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="No available ports in range 8100-8199",
    )


@router.get("", response_model=List[dict])
async def list_servers(
    username: str = Depends(verify_token),
    db_service: DatabaseService = Depends(get_database_service),
):
    """List all MCP servers."""
    logger.info(f"list_servers called by user: {username}")
    try:
        with db_service as db:
            servers = db.get_all_servers()
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
    1. Loads McpDirectory objects for all servers (creates/updates directory structures and files)
    2. Writes config files to /app/servers/
    3. Generates supervisord program files
    4. Restarts supervisord group:mcp_servers
    5. Installs MISE dependencies (if needed)
    """
    try:
        with db_service as db:
            servers = db.get_all_servers()

        # Load McpDirectory objects for each server (this creates/updates directory structures and files)
        directories = []
        synced_servers = []
        for server_data in servers:
            try:
                # Convert dict to MCPServerConfig
                server_config = Server(**server_data)
                # Create McpDirectory object (this generates all files and directory structure)
                directory = ServerDirectory.from_server_config(server_config)
                directories.append(directory)

                # Update synced_at timestamp
                server_data["synced_at"] = datetime.now(timezone.utc)
                synced_servers.append(server_data)

                logger.info(f"Loaded McpDirectory for server: {server_config.name} (ID: {server_config.id})")
            except Exception as e:
                logger.error(f"Failed to load McpDirectory for server {server_data.get('name', 'unknown')}: {str(e)}")
                raise

        # Update synced_at timestamps in database
        for server_data in synced_servers:
            db.update_server(server_data["id"], {"synced_at": server_data["synced_at"]})

        # for each directory, clear it, then write all files
        for directory in directories:
            directory.sync(logger=logger)

        logger.info(f"Successfully loaded {len(directories)} McpDirectory objects")

        # Tell supervisord to reread and update configuration
        try:
            reread_result = supervisor_service.reread_config()
            logger.info(f"Supervisord reread result: added={reread_result.added_group_names}, changed={reread_result.changed_group_names}, removed={reread_result.removed_group_names}")

            if reread_result.added_group_names or reread_result.changed_group_names or reread_result.removed_group_names:
                logger.info("Configuration changes detected, supervisord applied them")
            else:
                logger.info("No configuration changes detected")

        except Exception as e:
            logger.error(f"Failed to reread supervisord config: {str(e)}")
            # Don't fail the entire sync if reread fails
            pass

        return {
            "status": "success",
            "message": "MCP server directories and files synced, supervisord config updated",
            "details": {
                "servers_synced": len(servers),
                "directories_loaded": len(directories)
            },
        }
    except Exception as e:
        logger.error(f"Sync failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Sync failed: {str(e)}",
        )

@router.get("/{server_id}", response_model=dict)
async def get_server(
    server_id: str,
    username: str = Depends(verify_token),
    db_service: DatabaseService = Depends(get_database_service),
):
    """Get specific server."""
    logger.info(f"get_server called by user: {username} for server_id: {server_id}")
    try:
        with db_service as db:
            server = db.get_server(server_id)

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


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_server(
    server: dict,
    username: str = Depends(verify_token),
    db_service: DatabaseService = Depends(get_database_service),
):
    """Create a new MCP server."""
    # Generate ID before validation since MCPServerConfig requires it
    server_id = str(uuid.uuid4())
    server["id"] = server_id
    server["port"] = get_next_available_mcp_server_port(db_service)

    # Validate incoming data using MCPServerConfig model
    server_config = Server.model_validate(server)
    
    server_dict = server_config.model_dump()

    with db_service as db:
        db.insert_server(server_dict)
        
    return {"id": server_id, **server_dict}



@router.put("/{server_id}")
async def update_server(
    server_id: str,
    server: dict,
    username: str = Depends(verify_token),
    db_service: DatabaseService = Depends(get_database_service),
):
    """Update server configuration."""
    with db_service as db:
        existing_server = db.get_server(server_id)
        if not existing_server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Server not found",
            )

        # Validate incoming data using MCPServerConfig model
        server_config = Server.model_validate(server)
        server_dict = server_config.model_dump()
        logger.info(f"Validated server config: {server_dict}")
        server_dict["id"] = server_id
        server_dict["updated_at"] = datetime.now(timezone.utc)

        # Always assign port for all transports (ignore any port in request)
        transport = server_dict.get("transport")
        if transport:
            logger.info("Auto-assigning port for update")
            # Get all existing servers to check assigned ports
            all_servers = db.get_all_servers()

            # Collect ports already assigned to other servers (exclude current server)
            assigned_ports = set()
            for srv in all_servers:
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

        db.update_server(server_id, server_dict)
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
    with db_service as db:
        server = db.get_server(server_id)
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

@router.delete("/{server_id}", status_code=204)
async def delete_server(
    server_id: str,
    username: str = Depends(verify_token),
    db_service: DatabaseService = Depends(get_database_service),
):
    """Delete server configuration."""
    with db_service as db:
        server = db.get_server(server_id)
        if not server:
            raise HTTPException(
                status_code=404,
                detail="Server not found",
            )
        db.delete_server(server_id)
    return None

@router.get("/mcp-config", response_model=dict)
async def get_mcp_config(
    username: str = Depends(verify_token),
    db_service: DatabaseService = Depends(get_database_service),
):
    """Generate mcpServer.json configuration for FastMCP proxy server."""
    with db_service as db:
        servers = db.get_all_servers()

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

@router.post("/parse-config")
async def parse_server_config(
    data: dict,
    username: str = Depends(verify_token),
):
    """Parse and validate JSON configuration for MCP server."""
    try:
        json_str = data.get("json", "")
        if not json_str:
            raise HTTPException(status_code=400, detail="JSON configuration is required")

        # Parse JSON
        try:
            config_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")

        # Check if it's McpServersJsonFile format (has mcpServers key)
        if "mcpServers" in config_data and isinstance(config_data["mcpServers"], dict):
            # Convert from McpServersJsonFile format to MCPServerConfig
            mcp_servers = config_data["mcpServers"]
            if len(mcp_servers) != 1:
                raise HTTPException(
                    status_code=400,
                    detail="McpServersJsonFile must contain exactly one server configuration"
                )

            server_name, server_config = next(iter(mcp_servers.items()))

            # Convert to MCPServerConfig format
            mcpserver_config = {
                "id": str(uuid.uuid4()),  # Generate unique ID
                "name": server_name,
                "transport": server_config.get("type", "stdio"),
                "command": server_config.get("command"),
                "arguments": server_config.get("args", []),
                "url": server_config.get("url"),
                "envs": server_config.get("env", {}),
                # Set defaults for required fields
                "supervisor_conf": {
                    "name": server_name,
                    "command": "",  
                    "group": "mcp_servers",
                    "autostart": True,
                    "autorestart": "unexpected",
                    "startsecs": 1,
                    "startretries": 3,
                    "priority": 999,
                    "stopsignal": "TERM",
                    "stopwaitsecs": 10,
                    "redirect_stderr": False,
                    "numprocs": 1
                },
                "tools": [],
                "log_level": "INFO"
            }

            # Validate using MCPServerConfig model
            server_config_obj = Server.model_validate(mcpserver_config)
            return server_config_obj.model_dump()

        else:
            # Assume it's already MCPServerConfig format
            # Validate using MCPServerConfig model
            server_config = Server.model_validate(config_data)
            return server_config.model_dump()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse configuration: {str(e)}")

@router.post("/{server_id}/files", response_model=dict)
async def get_server_files(
    server_id: str,
    server_config_data: dict | None = None,
    username: str = Depends(verify_token),
    db_service: DatabaseService = Depends(get_database_service),
):
    """Get generated files for a server configuration."""
    logger.info(f"get_server_files called by user: {username} for server_id: {server_id}")
    try:
        # Use provided server config data if available, otherwise fetch from database
        if server_config_data:
            logger.info(f"Using provided server config data for server: {server_id}")
            config_data = server_config_data
        else:
            logger.info(f"Fetching server config from database for server: {server_id}")
            with db_service as db:
                server_data = db.get_server(server_id)

            if not server_data:
                logger.warning(f"Server not found: {server_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Server not found",
                )
            config_data = server_data

        



        # Convert dict to MCPServerConfig
        server_config = Server(**config_data)

        # Directory 
        directory = ServerDirectory.from_server_config(server_config)


        # Create file generators
        mcp_servers_json = directory.mcp_servers_json_file
        fastmcp_proxy = directory.fastmcp_server_proxy_server_file
        mise_toml = directory.mise_toml_file
        supervisord_conf = directory.supervisord_conf_file

        # Generate file contents
        files = {
            "mcpServers.json": str(mcp_servers_json),
            "server.py": str(fastmcp_proxy),
            "mise.toml": str(mise_toml),
            "supervisord.conf": str(supervisord_conf),
        }

        logger.info(f"Successfully generated files for server: {server_id}")
        return {"files": files}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error in get_server_files for {server_id}: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating server files: {str(e)}"
        ) from e
