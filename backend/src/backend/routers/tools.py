import os, subprocess

from fastapi import APIRouter, HTTPException


router = APIRouter(prefix="/api/tools", tags=["tools"])


@router.get("/mise/check/{tool_name}")
async def check_mise_tool(tool_name: str):
    """Check if mise recognizes a specified tool without installing it.
    
    Args:
        tool_name: Name of the tool to check (e.g., 'node', 'python', 'go')
    
    Returns:
        - available: bool - whether mise recognizes the tool
        - latest_version: str - latest available version if found
        - error: str - error message if any
    """
    try:
        # Try absolute path first, then fallback to PATH
        mise_path = "/usr/local/bin/mise"
        
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
