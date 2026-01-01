from __future__ import annotations

from enum import Enum
from typing import Annotated, Dict, List, Literal, Union

from pydantic import BaseModel, Field, model_serializer
from src.backend.enums import MCPServerTransport


class MCPServerTransports(Enum):
    """MCP server type types."""
    STDIO = "stdio"
    HTTP  = "http"
    SSE   = "sse"

class MCPServerJsonEntryBase(BaseModel):
    """MCP server entry in mcpServers.json configuration file."""
    # Remove the 'type' field from the base class to avoid conflicts with discriminated union
    pass

    @model_serializer(mode='wrap')
    def serializer(self, handler):
        """Custom serializer to match expected JSON structure."""
        data = handler(self)
        # Remove 'type' from serialized output
        data.pop("type", None)
        return data

class MCPServerJsonEntryStdIO(MCPServerJsonEntryBase):
    """MCP server entry for STDIO type."""

    type: Literal[MCPServerTransport.STDIO] = MCPServerTransport.STDIO
    command: str = Field(description="Command to start the MCP server")
    args: List[str] = Field(default_factory=list, description="Arguments for the command")
    envs: Dict[str, str] = Field(default_factory=dict, description="Environment variables for the MCP server")

class MCPServerJsonEntryHTTP(MCPServerJsonEntryBase):
    """MCP server entry for HTTP type."""

    type: Literal[MCPServerTransport.HTTP] = MCPServerTransport.HTTP
    url: str = Field(description="URL of the MCP server")
    headers: Dict[str, str] = Field(default_factory=dict, description="HTTP headers for the MCP server")

class MCPServerJsonEntrySSE(MCPServerJsonEntryBase):
    """MCP server entry for SSE type."""

    type: Literal[MCPServerTransport.SSE] = MCPServerTransport.SSE
    url: str = Field(description="URL of the MCP server")
    headers: Dict[str, str] = Field(default_factory=dict, description="HTTP headers for the MCP server")

# Discriminated union: type field selects the class
MCPServerJsonEntry = Annotated[
    Union[MCPServerJsonEntryStdIO, MCPServerJsonEntryHTTP, MCPServerJsonEntrySSE],
    Field(discriminator="type")
]

class MCPServersJson(BaseModel):
    """MCP servers configuration file model (mcpServers.json)."""

    mcp_servers: Dict[str, MCPServerJsonEntry] = Field(default_factory=dict, alias="mcpServers", description="Compiled mcpServers configurations")

    def __str__(self) -> str:
        """String representation as JSON."""
        return self.model_dump_json(by_alias=True, indent=4)
