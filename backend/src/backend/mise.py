"""Mise-related models for MCP server configuration and management."""

from __future__ import annotations

import json, logging, os, re, signal, subprocess

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_serializer
from src.backend.settings import get_settings


if TYPE_CHECKING:
    from src.backend.models import Server



class MiseTool(BaseModel):
    """Tool/language version requirement (e.g., python, node, go)."""
    name: str
    version: Optional[str] = None



class MiseToml(BaseModel):
    """mise.toml configuration file for MCP server."""

    envs: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    tools: List[MiseTool] = Field(default_factory=list, description="Required tools/languages")
    tasks: Dict[str, str] = Field(default_factory=dict, description="Mise tasks (install, uninstall, etc.)")

    def ensure_tool(self, tool_name: str, version: Optional[str] = None) -> None:
        """Ensure tool exists, with version-aware upgrade semantics.

        Modes:
        - No version specified: add if missing (default to "*"), preserve any existing version
        - Version specified: add if missing, upgrade if existing < new (lexicographically), never downgrade

        Args:
            tool_name: Name of tool/language
            version: Exact or min version. None means any version acceptable, defaults to "*" if adding
        """
        existing = next((t for t in self.tools if t.name == tool_name), None)

        if existing is None:
            # Tool doesn't exist
            self.tools.append(MiseTool(name=tool_name, version=version or "*"))
        elif version is not None:
            # Tool exists + version constraint specified: upgrade if new > old (lex)
            if (
                existing.version is not None
                and existing.version != "*"
                and version is not None
                and version > existing.version
            ):
                existing.version = version
            elif existing.version == "*":
                # Wildcard always yields to explicit version
                existing.version = version
        # else: tool exists, no version constraint, leave untouched (permissive mode)


    def ensure_task(self, task_name: str, command: List[str]) -> None:
        """Ensure task exists. If already present, preserve existing value."""
        if task_name not in self.tasks:
            self.tasks[task_name] = " ".join(command)

    def ensure_env(self, key: str, value: str) -> None:
        """Ensure environment variable exists. If already present, preserve existing value."""
        if key not in self.envs:
            self.envs[key] = value

    def has_tool(self, tool_name: str) -> bool:
        return any(tool.name == tool_name for tool in self.tools)

    def has_task(self, task_name: str) -> bool:
        return task_name in self.tasks

    def has_env(self, key: str) -> bool:
        return key in self.envs


    def __str__(self) -> str:
        file = []

        if self.envs:
            file.append("")
            file.append("[env]")
            for k, v in self.envs.items():
                file.append(f'{k} = "{v}"')

        if self.tools:
            file.append("")
            file.append("[tools]")
            for tool in self.tools:
                if tool.version and tool.version != "*":
                    file.append(f'{tool.name} = "{tool.version}"')
                else:
                    file.append(f'{tool.name} = "latest"')

        if self.tasks:
            file.append("")
            file.append("[tasks]")
            for task_name, command in self.tasks.items():
                file.append(f'{task_name} = "{command}"')

        if file and file[0] == "":
            file = file[1:]  # Remove leading empty line

        return "\n".join(file)
