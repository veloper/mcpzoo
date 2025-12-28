from functools import lru_cache
from typing import Optional

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, Field
from src.backend.services.database import DatabaseService, get_database_service
from src.backend.services.logging import Logger, get_logging_service
from src.backend.settings import get_settings


settings = get_settings()



class PortManagerService(BaseModel):
    """Service for managing MCP server port assignments."""
    model_config = {"arbitrary_types_allowed": True}


    db_service: DatabaseService 
    logger : Logger
    port_range: range = Field(default=range(7998, 8199))
    
    dedicated_port_range: range = Field(default=range(7998, 8010))
    mcp_server_port_range: range = Field(default=range(8011, 8199))
   

    def get_taken_mcp_server_ports(self) -> set[int]:
        """Get all ports currently taken by existing MCP servers."""
        db = self._db_service.get_db()
        existing_servers = db.get_all_servers()

        taken_ports = set()
        for server in existing_servers:
            if server.get("port"):
                taken_ports.add(server["port"])

        return taken_ports

    def get_available_mcp_server_ports(self) -> set[int]:
        """Get all available ports for MCP servers."""
        start_port = self.mcp_server_port_range.start
        end_port = self.mcp_server_port_range.stop

        assigned_ports = self.get_taken_mcp_server_ports()

        available_ports = set(range(start_port, end_port + 1))
        available_ports -= assigned_ports

        return available_ports

   
    def get_next_mcp_server_available_port(self) -> int:
        """Get the next available port not taken by an existing MCP server."""
        available_ports = self.get_available_mcp_server_ports()
        if not available_ports:
            self.logger.error("No available MCP server ports in range")
            raise Exception("No available MCP server ports in range")
        
        next_port = min(available_ports)
        return next_port 


@lru_cache()
def get_port_manager_service(
    db_service: DatabaseService = Depends(get_database_service),
    logging_service : Logger = Depends(get_logging_service)
) -> PortManagerService:
    """Dependency for FastAPI to inject port manager service."""
    return PortManagerService(db_service=db_service, logger=logging_service)
