# Phase 034: Sync and Deployment

## Objective

Implement the critical sync_processes module that writes server configurations to disk and manages supervisord.

## Prerequisites

- Phase 032 completed
- Database wrapper functional

## Overview

**CRITICAL MODULE**: This is the ONLY place where server configs are written to disk.

When called:
1. **Per-server directories**: Creates `/app/servers/{server_name}/` for each server
2. **`.mise.toml` generation**: Generates `.mise.toml` in each server directory with `[tools]` section from config
3. **Task execution**: Runs `task_install` from `.mise.toml` (if specified in ServerConfig)
4. **Supervisord config**: Generates `/etc/supervisor/conf.d/mcp_{server_name}.conf`
5. **Group restart**: Restarts supervisord `group:mcp_servers`

**To uninstall a server**:
- Delete server config from DB (via DELETE endpoint)
- Click "Sync Processes" (removes files from `/app/servers/{name}/`)
- No need to manually remove directories

All errors logged to `/var/log/supervisor/` via supervisord. Detailed error messages in response.

## Steps

### 3.1: Implement sync_processes.py

Create `backend/src/backend/sync_processes.py`:

```python
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from .tinydb import db
from .supervisor_api import supervisor
from .utils.shell import run_command


def sync_mcp_servers() -> Dict[str, Any]:
    """
    Sync all server configs from database to disk and restart supervisord.
    
    This function:
    1. Reads all server configs from TinyDB
    2. Creates per-server directories
    3. Generates .mise.toml files
    4. Generates supervisord config files
    5. Restarts supervisord mcp_servers group
    
    Returns:
        Dict with sync results and status
    """
    servers = db.get_all_servers()
    results = {
        "timestamp": datetime.now().isoformat(),
        "servers_synced": len(servers),
        "details": []
    }
    
    try:
        # Step 1: Create per-server directories and config files
        for server in servers:
            try:
                server_name = server.get("name")
                server_dir = Path(f"/app/servers/{server_name}")
                server_dir.mkdir(parents=True, exist_ok=True)
                
                # Generate .mise.toml
                mise_toml_path = server_dir / ".mise.toml"
                mise_content = _generate_mise_toml(server)
                mise_toml_path.write_text(mise_content)
                
                # Run task_install if specified
                if server.get("task_install"):
                    try:
                        run_command(
                            ["task", server.get("task_install")],
                            cwd=str(server_dir),
                            timeout=120
                        )
                    except Exception as e:
                        results["details"].append({
                            "server": server_name,
                            "status": "task_install_failed",
                            "error": str(e)
                        })
                        continue
                
                # Generate supervisord config
                supervisor_conf_path = Path(f"/etc/supervisor/conf.d/mcp_{server_name}.conf")
                supervisor_conf = _generate_supervisord_config(server)
                supervisor_conf_path.write_text(supervisor_conf)
                
                results["details"].append({
                    "server": server_name,
                    "status": "synced",
                    "directory": str(server_dir),
                    "config": str(supervisor_conf_path)
                })
            
            except Exception as e:
                results["details"].append({
                    "server": server_name,
                    "status": "failed",
                    "error": str(e)
                })
        
        # Step 2: Reread supervisord configs
        supervisor.reread()
        
        # Step 3: Update supervisord
        supervisor.update()
        
        # Step 4: Restart mcp_servers group
        try:
            supervisor.restart("group:mcp_servers")
        except:
            pass  # Group may not exist if no servers
        
        results["status"] = "success"
    
    except Exception as e:
        results["status"] = "failed"
        results["error"] = str(e)
    
    return results


def _generate_mise_toml(server: Dict[str, Any]) -> str:
    """Generate .mise.toml content from server config."""
    lines = ["# Auto-generated .mise.toml for server management\n"]
    
    # Add tools section
    tools = server.get("tools", [])
    if tools:
        lines.append("[tools]\n")
        for tool in tools:
            name = tool.get("name")
            version = tool.get("version", "*")
            lines.append(f"{name} = \"{version}\"\n")
    
    # Add environment variables
    envs = server.get("envs", {})
    if envs:
        lines.append("\n[env]\n")
        for key, value in envs.items():
            lines.append(f"{key} = \"{value}\"\n")
    
    return "".join(lines)


def _generate_supervisord_config(server: Dict[str, Any]) -> str:
    """Generate supervisord config from server config."""
    supervisor_conf = server.get("supervisor_conf", {})
    
    if isinstance(supervisor_conf, dict):
        # If it's a dict, generate manually
        lines = [f"[program:mcp_{server['name']}]"]
        lines.append(f"command={supervisor_conf.get('command', '')}")
        
        for key, value in supervisor_conf.items():
            if key in ["command", "name"]:
                continue
            if value is not None:
                lines.append(f"{key}={value}")
        
        return "\n".join(lines)
    else:
        # If it's a SupervisorConf object
        return supervisor_conf.to_supervisord_program_section()
```

---

## Verification Checklist

- [ ] `backend/src/backend/sync_processes.py` created
- [ ] Sync function creates server directories
- [ ] .mise.toml generation works
- [ ] Supervisord config generation works

## Next Step

Proceed to [035-server-routes.md](./035-server-routes.md)
