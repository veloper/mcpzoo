from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from src.backend.auth import verify_token
from src.backend.process import Process
from src.backend.services.processes import get_processes_service, ProcessesService


router = APIRouter(prefix="/api/processes", tags=["processes"])

@router.get("", response_model=List[Process])
async def get_processes(
    username: str = Depends(verify_token),
    processes_service: ProcessesService = Depends(get_processes_service)
):
    """Get the current processes."""
    try:
        return processes_service.get_all_processes()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get processes: {str(e)}"
        ) from e

@router.get("/tree", response_model=List[Process])
async def get_process_tree(
    username: str = Depends(verify_token),
    processes_service: ProcessesService = Depends(get_processes_service)
):
    """Get the current process tree."""
    try:
        return processes_service.get_all_processes()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get process tree: {str(e)}"
        ) from e
