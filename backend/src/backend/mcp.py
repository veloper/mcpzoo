from __future__ import annotations

from enum import Enum
from typing import Annotated, Dict, List, Literal, Union

from pydantic import BaseModel, Field, model_serializer
from src.backend.enums import MCPServerTransport


class MCPServerTransports(Enum):
    """MCP server transport types."""
    STDIO = "stdio"
    HTTP  = "http"
    SSE   = "sse"

class MCPServerJsonEntryBase(BaseModel):
    """MCP server entry in mcpServers.json configuration file."""

    transport: MCPServerTransport = Field(description="Transport type of the MCP server")

class MCPServerJsonEntryStdIO(MCPServerJsonEntryBase):
    """MCP server entry for STDIO transport."""

    transport: Literal[MCPServerTransport.STDIO] = MCPServerTransport.STDIO
    command: List[str] = Field(description="Command to start the MCP server")
    args: List[str] = Field(default_factory=list, description="Arguments for the command")
    envs: Dict[str, str] = Field(default_factory=dict, description="Environment variables for the MCP server")

class MCPServerJsonEntryHTTP(MCPServerJsonEntryBase):
    """MCP server entry for HTTP transport."""

    transport: Literal[MCPServerTransport.HTTP] = MCPServerTransport.HTTP
    url: str = Field(description="URL of the MCP server")
    headers: Dict[str, str] = Field(default_factory=dict, description="HTTP headers for the MCP server")

class MCPServerJsonEntrySSE(MCPServerJsonEntryBase):
    """MCP server entry for SSE transport."""

    transport: Literal[MCPServerTransport.SSE] = MCPServerTransport.SSE
    url: str = Field(description="URL of the MCP server")
    headers: Dict[str, str] = Field(default_factory=dict, description="HTTP headers for the MCP server")

# Discriminated union: transport field selects the class
MCPServerJsonEntry = Annotated[
    Union[MCPServerJsonEntryStdIO, MCPServerJsonEntryHTTP, MCPServerJsonEntrySSE],
    Field(discriminator="transport")
]

class MCPServersJson(BaseModel):
    """MCP servers configuration file model (mcpServers.json)."""

    mcp_servers: Dict[str, MCPServerJsonEntry] = Field(default_factory=dict, alias="mcpServers", description="Compiled mcpServers configurations")

    def __str__(self) -> str:
        """String representation as JSON."""
        return self.model_dump_json(by_alias=True, indent=4)
