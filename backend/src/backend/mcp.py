from __future__ import annotations

import json

from typing import TYPE_CHECKING, Any, Dict, List

from pydantic import BaseModel, Field, model_serializer
from src.backend.enums import MCPServerTransport


if TYPE_CHECKING:
    from src.backend.models import Server


class McpServersJsonFile(BaseModel):
    """MCP servers configuration file model."""

    servers_dict: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Compiled mcpServers configuration dictionary")

    @classmethod
    def from_mcp_server_configs(cls, configs: List[Server]) -> "McpServersJsonFile":
        """Create McpServersJsonFile from list of MCPServerConfigs, extracting and transforming relevant fields."""
        servers_dict = {}
        for config in configs:
            # Transport-specific config
            if config.transport == MCPServerTransport.STDIO:
                servers_dict[config.name] = {
                    "type": config.transport,
                    "command": config.command,
                    "args": config.arguments
                }
            else:
                servers_dict[config.name] = {
                    "type": config.transport,
                    "url": config.url
                }

            # Environment variables
            if config.envs:
                if "env" not in servers_dict[config.name]:
                        servers_dict[config.name]["env"] = {}
                for key, value in config.envs.items():
                    servers_dict[config.name]["env"][key] = value

        return cls(servers_dict=servers_dict)

    @model_serializer()
    def serialize(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {"mcpServers": self.servers_dict}

    def __str__(self) -> str:
        """String representation as JSON."""
        return json.dumps(self.serialize(), indent=4)
