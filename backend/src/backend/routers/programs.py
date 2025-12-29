import subprocess

from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from src.backend.auth import verify_token
from src.backend.models import Server
from src.backend.services.database import DatabaseService, get_database_service
from src.backend.services.supervisor import SupervisorService, get_supervisor_service


router = APIRouter(prefix="/api/programs", tags=["programs"])


@router.get("", response_model=List[dict])
async def list_processes(
    username: str = Depends(verify_token),
    srv : SupervisorService = Depends(get_supervisor_service),
):
    """List all supervisor programs."""
    programs = srv.get_all_programs()
    return [p.model_dump() for p in programs if p.name != "overmind"]



@router.post("/{name}/start")
async def start_process(
    name: str,
    username: str = Depends(verify_token),
    srv = Depends(get_supervisor_service),
):
    """Start program."""
    result = srv.start_program(name)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to start {name}",
        )
    return {"status": "started", "program": name}


@router.post("/{name}/stop")
async def stop_process(
    name: str,
    username: str = Depends(verify_token),
    srv = Depends(get_supervisor_service),
):
    """Stop program."""
    if not srv.stop_program(name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to stop {name}",
        )
    return {"status": "stopped", "program": name}
    

@router.get("/{name}/logs")
async def get_process_logs(
    name: str,
    limit: int = 1000,
    username: str = Depends(verify_token),
    db_service: DatabaseService = Depends(get_database_service),
):
    """Get process logs from actual log files as structured records."""
    server_name = name

    # Look up server config by name
    db = db_service.get_db()
    all_servers = db.get_all_servers()
    server_data = next((s for s in all_servers if s.get('name') == server_name), None)

    if not server_data:
        raise HTTPException(status_code=404, detail=f"Server not found: {server_name}")

    # Convert to Server to access supervisor config
    server_config = Server(**server_data)
    supervisor_conf = server_config.get_supervisor_conf()

    # Get log file paths from supervisor config
    stdout_logfile = supervisor_conf.stdout_logfile
    stderr_logfile = supervisor_conf.stderr_logfile

    if not stdout_logfile and not stderr_logfile:
        raise HTTPException(status_code=404, detail="No log files configured for this server")

    logs = []

    # Read stdout logs
    if stdout_logfile:
        try:
            with open(stdout_logfile, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:  # Skip empty lines
                        logs.append({
                            "type": "STDOUT",
                            "message": line
                        })
        except FileNotFoundError:
            # Log file doesn't exist yet, skip
            pass
        except Exception:
            # Log read error, but continue with other logs
            pass

    # Read stderr logs
    if stderr_logfile:
        try:
            with open(stderr_logfile, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:  # Skip empty lines
                        logs.append({
                            "type": "STDERR",
                            "message": line
                        })
        except FileNotFoundError:
            # Log file doesn't exist yet, skip
            pass
        except Exception:
            # Log read error, but continue
            pass

    # Replace truncated start commands with full command
    for log in logs:
        if log["type"] == "STDERR" and log["message"].startswith("[start] $ ") and log["message"].endswith(" -…"):
            log["message"] = f"[start] $ {supervisor_conf.command}"

    # Return last N log entries (configurable limit)
    recent_logs = logs[-limit:] if len(logs) > limit else logs

    return {
        "process": name,
        "server_name": server_name,
        "logs": recent_logs,
        "total_entries": len(logs),
        "returned_entries": len(recent_logs)
    }


@router.get("/{name}/status", response_model=dict)
async def process_status(
    name: str,
    username: str = Depends(verify_token),
    srv = Depends(get_supervisor_service),
):
    """Get program status."""
    try:
        prog = srv.get_process_info(name)
        if not prog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Program {name} not found",
            )
        return prog.model_dump()
    except RuntimeError as e:
        # Handle cases where supervisor raises RuntimeError for non-existent processes
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Program {name} not found",
            ) from e
        else:
            # Re-raise other RuntimeErrors as internal server errors
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get program status: {str(e)}",
            ) from e

@router.put("/reread_config")
async def reread_config(
    username: str = Depends(verify_token),
    srv = Depends(get_supervisor_service),
):
    """Reread supervisord configuration and apply changes."""
    # reread_config() already handles both reading and updating
    result = srv.reread_config()

    return {
        "status": "success",
        "message": "Configuration reread and updated successfully",
        "details": {
            "added_groups": result.added_group_names,
            "changed_groups": result.changed_group_names,
            "removed_groups": result.removed_group_names
        }
    }
