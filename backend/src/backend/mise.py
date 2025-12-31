"""Mise-related models for MCP server configuration and management."""

from __future__ import annotations

import re

from typing import TYPE_CHECKING, Dict, List, Optional

from pydantic import BaseModel, Field


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
        """
        Ensure that a tool with the given name (and optionally version) exists in the tools list.

        Logic:
        - If the tool does not exist, add it with the specified version (or "*" if no version is given).
        - If the tool exists and a version is specified:
            - If both the existing and new versions are numeric (e.g., '1.2.3'), compare them part by part.
            - Upgrade to the higher version if the new version is greater; never downgrade.
            - If versions are not comparable or new version is not specified, keep the existing version.
        - If the tool exists and no version is specified, do nothing (preserve existing version).

        Args:
            tool_name: Name of the tool or language to ensure.
            version: Optional version string. If None, any version is acceptable (defaults to "*" if adding).
        """
        existing = next((t for t in self.tools if t.name == tool_name), None)
        if existing is None:
            self.tools.append(MiseTool(name=tool_name, version=version or "*"))
            return

        if version is None:
            return

        existing_version = existing.version or "*"
        if not re.match(r'^\d+(\.\d+)*$', existing_version) or not re.match(r'^\d+(\.\d+)*$', version):
            return

        # Compare versions
        v1_parts = [int(p) for p in existing_version.split('.')]
        v2_parts = [int(p) for p in version.split('.')]
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts.extend([0] * (max_len - len(v1_parts)))
        v2_parts.extend([0] * (max_len - len(v2_parts)))
        for p1, p2 in zip(v1_parts, v2_parts):
            if p1 < p2:
                existing.version = version
                break
            elif p1 > p2:
                break


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
