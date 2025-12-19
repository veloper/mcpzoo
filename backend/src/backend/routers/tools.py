import os, subprocess

from fastapi import APIRouter, HTTPException


router = APIRouter(prefix="/api/tools", tags=["tools"])


@router.get("/mise/check/{tool_spec}")
async def check_mise_tool(tool_spec: str):
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
    # Parse tool:version format
    if ':' in tool_spec:
        tool_name, requested_version = tool_spec.split(':', 1)
        tool_name = tool_name.strip()
        requested_version = requested_version.strip()
    else:
        tool_name = tool_spec.strip()
        requested_version = None

    # Try absolute path first, then fallback to PATH
    mise_path = "/usr/local/bin/mise"

    try:

        # Use mise ls-remote to check available versions without installing
        result = subprocess.run(
            [mise_path, "ls-remote", tool_name],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0 and result.stdout.strip():
            # Tool is recognized by mise
            lines = result.stdout.strip().split('\n')
            latest_version = lines[0] if lines else "unknown"

            # If a specific version was requested, check if it exists
            if requested_version:
                version_exists = any(requested_version in line for line in lines)
                if not version_exists:
                    return {
                        "available": False,
                        "tool": tool_name,
                        "version": requested_version,
                        "error": f"Version {requested_version} not found for tool {tool_name}",
                    }
                return {
                    "available": True,
                    "tool": tool_name,
                    "version": requested_version,
                    "latest_version": latest_version,
                }
            else:
                # No specific version requested
                return {
                    "available": True,
                    "tool": tool_name,
                    "latest_version": latest_version,
                }
        else:
            # Tool not found or error
            return {
                "available": False,
                "tool": tool_name,
                "version": requested_version,
                "error": result.stderr.strip() or "Tool not found",
            }
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=504,
            detail=f"Timeout checking tool {tool_name}",
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=500,
            detail=f"mise not found at {mise_path}: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error checking tool: {str(e)}",
        )

@router.get("/mise/versions/{tool_name}")
async def get_mise_tool_versions(tool_name: str):
    """Get available versions for a mise tool.

    Args:
        tool_name: Name of the tool to get versions for

    Returns:
        - tool: str - the tool name
        - versions: list - available versions
        - latest: str - latest version
        - error: str - error message if any
    """
    # Try absolute path first, then fallback to PATH
    mise_path = "/usr/local/bin/mise"

    try:

        # Use mise ls-remote to get available versions
        result = subprocess.run(
            [mise_path, "ls-remote", tool_name],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0 and result.stdout.strip():
            # Parse versions from output
            lines = result.stdout.strip().split('\n')
            versions = [line.strip() for line in lines if line.strip()]

            if versions:
                latest_version = versions[0]  # First line is typically latest
                return {
                    "tool": tool_name,
                    "versions": versions,
                    "latest": latest_version,
                }
            else:
                return {
                    "tool": tool_name,
                    "versions": [],
                    "latest": None,
                    "error": "No versions found",
                }
        else:
            # Tool not found or error
            return {
                "tool": tool_name,
                "versions": [],
                "latest": None,
                "error": result.stderr.strip() or "Tool not found",
            }
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=504,
            detail=f"Timeout getting versions for {tool_name}",
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=500,
            detail=f"mise not found at {mise_path}: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting versions: {str(e)}",
        )
