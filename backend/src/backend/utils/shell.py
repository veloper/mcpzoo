import subprocess
from typing import List


def run_command(
    cmd: List[str],
    cwd: str = None,
    timeout: int = 30,
    check: bool = True,
) -> str:
    """
    Run a shell command and return output.
    
    Args:
        cmd: Command and arguments as list
        cwd: Working directory
        timeout: Command timeout in seconds
        check: Raise exception if command fails
    
    Returns:
        Command output as string
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            timeout=timeout,
            capture_output=True,
            text=True,
            check=check,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        if check:
            raise
        return e.stderr
