"""Service for interacting with mise CLI tool."""

import subprocess

from typing import Any, Dict, List, Optional

from fastapi import HTTPException


class MiseService:
    """Service for managing mise tool operations."""

    def __init__(self, mise_path: Optional[str] = None):
        """Initialize mise service.

        Args:
            mise_path: Path to mise executable. If None, will try to find it in PATH.
        """
        self.mise_path = mise_path or self._find_mise_path()

    def _find_mise_path(self) -> str:
        """Find mise executable path."""
        # Try common paths
        common_paths = [
            "/usr/local/bin/mise",
            "/opt/homebrew/bin/mise",
            "mise"  # Let system find it in PATH
        ]

        for path in common_paths:
            try:
                subprocess.run([path, "--version"], capture_output=True, check=True)
                return path
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue

        # If not found in common paths, try which command
        try:
            result = subprocess.run(["which", "mise"], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        raise HTTPException(
            status_code=500,
            detail="mise not found. Please install mise from https://mise.jdx.dev/"
        )

    def check_tool(self, tool_spec: str) -> Dict[str, Any]:
        """Check if mise recognizes a specified tool without installing it.

        Args:
            tool_spec: Tool specification (e.g., 'node', 'python', 'go', 'python:3.10')

        Returns:
            Dict with tool availability and version information
        """
        # Parse tool:version format
        if ':' in tool_spec:
            tool_name, requested_version = tool_spec.split(':', 1)
            tool_name = tool_name.strip()
            requested_version = requested_version.strip()
        else:
            tool_name = tool_spec.strip()
            requested_version = None

        try:
            # Use mise ls-remote to check available versions without installing
            result = subprocess.run(
                [self.mise_path, "ls-remote", tool_name],
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
                    "version": requested_version if requested_version is not None else "",
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
                detail=f"mise not found at {self.mise_path}: {str(e)}",
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error checking tool: {str(e)}",
            )

    def get_tool_versions(self, tool_name: str) -> Dict[str, Any]:
        """Get available versions for a mise tool.

        Args:
            tool_name: Name of the tool to get versions for

        Returns:
            Dict with tool versions and latest version
        """
        try:
            # Use mise ls-remote to get available versions
            result = subprocess.run(
                [self.mise_path, "ls-remote", tool_name],
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
                detail=f"mise not found at {self.mise_path}: {str(e)}",
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error getting versions: {str(e)}",
            )


def get_mise_service() -> MiseService:
    """Get mise service instance."""
    return MiseService()
