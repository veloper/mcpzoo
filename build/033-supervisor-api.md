# Phase 033: Supervisor API

## Objective

Implement supervisord process control wrapper for managing MCP server processes.

## Prerequisites

- Phase 030 completed
- `backend/src/backend/` directory structure created

## Steps

### 3.1: Implement supervisor_api.py (Supervisord Integration)

Create `backend/src/backend/supervisor_api.py`:

```python
import subprocess
from typing import Dict, List, Optional
from .utils.shell import run_command


class SupervisorAPI:
    """Wrapper around supervisorctl."""
    
    def __init__(self, socket_file: str = "/var/run/supervisor.sock"):
        """Initialize supervisor API."""
        self.socket_file = socket_file
    
    def _supervisorctl(self, *args) -> str:
        """Run supervisorctl command."""
        cmd = ["supervisorctl", "-s", f"unix://{self.socket_file}"] + list(args)
        result = run_command(cmd)
        return result
    
    def status(self) -> Dict[str, str]:
        """Get status of all processes."""
        output = self._supervisorctl("status")
        result = {}
        for line in output.strip().split("\n"):
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 2:
                name = parts[0]
                state = parts[1]
                result[name] = state
        return result
    
    def start(self, program: str) -> bool:
        """Start a program."""
        try:
            self._supervisorctl("start", program)
            return True
        except:
            return False
    
    def stop(self, program: str) -> bool:
        """Stop a program."""
        try:
            self._supervisorctl("stop", program)
            return True
        except:
            return False
    
    def restart(self, program: str) -> bool:
        """Restart a program."""
        try:
            self._supervisorctl("restart", program)
            return True
        except:
            return False
    
    def reread(self) -> bool:
        """Reread config files."""
        try:
            self._supervisorctl("reread")
            return True
        except:
            return False
    
    def update(self) -> bool:
        """Update supervisord."""
        try:
            self._supervisorctl("update")
            return True
        except:
            return False


supervisor = SupervisorAPI()
```

---

## Verification Checklist

- [ ] `backend/src/backend/supervisor_api.py` created
- [ ] SupervisorAPI class initializes correctly
- [ ] supervisorctl commands execute without errors

## Next Step

Proceed to [034-sync-and-deployment.md](./034-sync-and-deployment.md)
