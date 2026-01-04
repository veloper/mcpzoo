from datetime import datetime, timezone, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import desc
from sqlalchemy.orm import joinedload

from src.backend.auth import verify_token
from src.backend.models import SystemSnapshot, SystemSnapshotRecord
from src.backend.services.database import DatabaseService, get_database_service
from src.backend.settings import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/snapshots", response_model=List[SystemSnapshot])
async def get_system_snapshots(
    username: str = Depends(verify_token),
    db_service: DatabaseService = Depends(get_database_service),
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=400),
    sort: str = Query("timestamp", regex="^[a-z_]+$"),
    dir: str = Query("desc", regex="^(asc|desc)$"),
):
    """Get paginated system snapshots with eager-loaded process data.
    
    Returns paginated list of SystemSnapshot objects ordered by specified field.
    Each snapshot contains nested process data collected at that timestamp.
    
    Args:
        username: Authenticated user (required)
        db_service: Database service dependency
        page: Page number (1-indexed, default 1)
        per_page: Results per page (1-400, default 100)
        sort: Field to sort by (default 'timestamp')
        dir: Sort direction 'asc' or 'desc' (default 'desc')
        
    Returns:
        List[SystemSnapshot]: Paginated snapshots with nested processes
        
    Raises:
        HTTPException 500: If database query fails
    """
    try:
        db = db_service.get_db()
        
        with db.get_session() as session:
            # Eager load processes using SQLAlchemy joinedload to avoid N+1 queries
            query = session.query(SystemSnapshotRecord).options(
                joinedload(SystemSnapshotRecord.processes)
            )
            
            # Apply sorting
            sort_field = getattr(SystemSnapshotRecord, sort, SystemSnapshotRecord.timestamp)
            if dir.lower() == "asc":
                query = query.order_by(sort_field.asc())
            else:
                query = query.order_by(sort_field.desc())
            
            # Apply pagination
            offset = (page - 1) * per_page
            snapshots = query.offset(offset).limit(per_page).all()
            
            return [s.to_pydantic_model() for s in snapshots]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system snapshots: {str(e)}"
        ) from e
