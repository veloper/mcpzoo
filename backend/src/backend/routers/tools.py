import os, subprocess

from fastapi import APIRouter, Depends, HTTPException

from src.backend.services.mise import MiseService, get_mise_service


router = APIRouter(prefix="/api/tools", tags=["tools"])


@router.get("/mise/check/{tool_spec}")
async def check_mise_tool(tool_spec: str, mise_service: MiseService = Depends(get_mise_service)):
    """Check if mise recognizes a specified tool without installing it.

    Args:
        tool_spec: Tool specification (e.g., 'node', 'python', 'go', 'python:3.10')

    Returns:
        - available: bool - whether mise recognizes the tool
        - tool: str - the tool name
        - version: str - requested version (if specified)
        - latest_version: str - latest available version if found
        - error: str - error message if any
    """
    return mise_service.check_tool(tool_spec)

@router.get("/mise/versions/{tool_name}")
async def get_mise_tool_versions(tool_name: str, mise_service: MiseService = Depends(get_mise_service)):
    """Get available versions for a mise tool.

    Args:
        tool_name: Name of the tool to get versions for

    Returns:
        - tool: str - the tool name
        - versions: list - available versions
        - latest: str - latest version
        - error: str - error message if any
    """
    return mise_service.get_tool_versions(tool_name)
