"""API routes for background sync tasks."""

from fastapi import APIRouter, Depends, HTTPException, status
from src.backend.auth import verify_token
from src.backend.models import SyncTask
from src.backend.services.logging import logger
from src.backend.services.sync import SyncService, get_sync_service


router = APIRouter(prefix="/api/sync", tags=["sync"])


@router.post("", response_model=dict)
async def start_sync(
    username: str = Depends(verify_token),
    sync_service: SyncService = Depends(get_sync_service),
):
    """Start a new background sync task.
    
    Returns:
        task_id: Unique identifier for the sync task
    """
    logger.info(f"start_sync called by user: {username}")
    try:
        task_id = await sync_service.start_sync()
        logger.info(f"Started sync task: {task_id}")
        return {"task_id": task_id, "status": "started"}
    except Exception as e:
        logger.error(f"Error starting sync: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start sync: {str(e)}",
        )


@router.get("/{task_id}", response_model=dict)
async def get_sync_status(
    task_id: str,
    username: str = Depends(verify_token),
    sync_service: SyncService = Depends(get_sync_service),
):
    """Get status of a sync task.
    
    Returns:
        Task status, progress, timestamps, and current operation
    """
    logger.info(f"get_sync_status called by user: {username} for task: {task_id}")
    try:
        task = await sync_service.get_task(task_id)
        
        if not task:
            logger.warning(f"Task not found: {task_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )
        
        logger.info(f"Retrieved task {task_id}: {task.get('status')}")
        return task
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sync status for {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}",
        )


@router.get("", response_model=dict)
async def list_syncs(
    limit: int = 50,
    offset: int = 0,
    username: str = Depends(verify_token),
    sync_service: SyncService = Depends(get_sync_service),
):
    """List all sync tasks with pagination.
    
    Query Parameters:
        limit: Maximum number of tasks to return (default: 50)
        offset: Number of tasks to skip (default: 0)
    
    Returns:
        Paginated list of sync tasks
    """
    logger.info(f"list_syncs called by user: {username}")
    try:
        result = await sync_service.list_tasks(limit=limit, offset=offset)
        logger.info(f"Retrieved {len(result['tasks'])} sync tasks")
        return result
    except Exception as e:
        logger.error(f"Error listing syncs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tasks: {str(e)}",
        )


@router.get("/{task_id}/logs", response_model=dict)
async def get_sync_logs(
    task_id: str,
    tail: int = 100,
    username: str = Depends(verify_token),
    sync_service: SyncService = Depends(get_sync_service),
):
    """Get logs for a sync task.
    
    Query Parameters:
        tail: Number of lines to return from end of file (default: 100)
    
    Returns:
        Log content
    """
    logger.info(f"get_sync_logs called by user: {username} for task: {task_id}")
    try:
        # Verify task exists
        task = await sync_service.get_task(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )
        
        logs = await sync_service.get_task_logs(task_id, tail=tail)
        logger.info(f"Retrieved logs for task {task_id}")
        return {"task_id": task_id, "logs": logs}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting logs for {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get logs: {str(e)}",
        )
