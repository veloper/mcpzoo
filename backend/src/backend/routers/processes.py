from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from src.backend.auth import verify_token
from src.backend.services.supervisord import get_supervisord_service
from src.backend.models import Program
from src.backend.utils.shell import run_command

router = APIRouter(prefix="/api/processes", tags=["processes"])


@router.get("", response_model=List[dict])
async def list_processes(
    username: str = Depends(verify_token),
    srv = Depends(get_supervisord_service),
):
    """List all supervisor programs."""
    try:
        programs = await srv.get_all_programs()
        return [p.model_dump() for p in programs]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list programs: {str(e)}"
        )


@router.post("/{name}/start")
async def start_process(
    name: str,
    username: str = Depends(verify_token),
    srv = Depends(get_supervisord_service),
):
    """Start program."""
    try:
        result = await srv.start_program(name)
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to start {name}",
            )
        return {"status": "started", "program": name}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting program: {str(e)}"
        )


@router.post("/{name}/stop")
async def stop_process(
    name: str,
    username: str = Depends(verify_token),
    srv = Depends(get_supervisord_service),
):
    """Stop program."""
    try:
        if not await srv.stop_program(name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to stop {name}",
            )
        return {"status": "stopped", "program": name}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error stopping program: {str(e)}"
        )


@router.post("/{name}/kill")
async def kill_process(
    name: str,
    username: str = Depends(verify_token),
    srv = Depends(get_supervisord_service),
):
    """Kill program with SIGKILL."""
    try:
        run_command(["supervisorctl", "signal", "SIGKILL", name], check=False)
        return {"status": "killed", "program": name}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to kill {name}: {str(e)}",
        )


@router.get("/{name}/logs")
async def get_process_logs(
    name: str,
    type: str = "stdout",
    username: str = Depends(verify_token),
):
    """Get process logs (stdout or stderr)."""
    log_file = f"/var/log/supervisor/{name}_{type}.log"
    
    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()
            content = ''.join(lines[-100:])
        
        return {
            "process": name,
            "type": type,
            "content": content,
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Log file not found for {type}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading logs: {str(e)}")


@router.get("/{name}/status", response_model=dict)
async def process_status(
    name: str,
    username: str = Depends(verify_token),
    srv = Depends(get_supervisord_service),
):
    """Get program status."""
    try:
        prog = await srv.get_program_status(name)
        if not prog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Program {name} not found",
            )
        return prog.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting program status: {str(e)}"
        )
