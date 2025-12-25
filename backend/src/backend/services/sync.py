"""Background sync task service using fork-based execution."""

import json, logging, os, subprocess, uuid

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.backend.models import MCPServerConfig, McpServerDirectory, SyncTask, SyncTaskStatus
from src.backend.services.database import database_service
from src.backend.services.logging import logger
from src.backend.settings import get_settings


settings = get_settings()


class SyncService:
    """Service for managing background sync tasks using fork-based execution."""
    
    # Log directory for sync tasks
    LOG_DIR = Path("/var/log/sync_task")
    
    def __init__(self):
        """Initialize sync service."""
        try:
            self.LOG_DIR.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            # Fall back to temp directory if /var/log is not accessible
            import tempfile
            self.LOG_DIR = Path(tempfile.gettempdir()) / "mcpzoo_sync_logs"
            self.LOG_DIR.mkdir(parents=True, exist_ok=True)
            logger.warning(f"Cannot write to /var/log/sync_task, using {self.LOG_DIR} instead")
    
    async def start_sync(self) -> str:
        """Start a new sync task in background.
        
        Returns:
            task_id: Unique identifier for the sync task
        """
        # Create task ID
        task_id = str(uuid.uuid4())
        
        # Create log file path
        log_file_path = str(self.LOG_DIR / f"{task_id}.log")
        
        # Create task record in database
        task = SyncTask(
            id=task_id,
            status=SyncTaskStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            log_file_path=log_file_path,
            total_servers=0,
        )
        
        with database_service as db:
            sync_tasks_table = db.table("sync_tasks")
            sync_tasks_table.insert(task.model_dump())
        
        logger.info(f"Created sync task: {task_id}")
        
        # Fork child process to run sync
        pid = os.fork()
        
        if pid == 0:
            # Child process - run sync logic
            try:
                self._run_sync_child(task_id, log_file_path)
            except Exception as e:
                logger.error(f"Sync child process error: {e}")
                exit(1)
        else:
            # Parent process - return task ID immediately
            logger.info(f"Forked sync task {task_id} with PID {pid}")
            return task_id
    
    def _run_sync_child(self, task_id: str, log_file_path: str) -> None:
        """Child process that runs the actual sync.
        
        Args:
            task_id: Task identifier
            log_file_path: Path to write logs to
        """
        # Create a dedicated logger for this task
        task_logger = self._create_task_logger(task_id, log_file_path)
        
        task_logger.info(f"Starting sync task: {task_id}")
        
        try:
            # Update task status to RUNNING
            self._update_task_status(
                task_id=task_id,
                status=SyncTaskStatus.RUNNING,
                started_at=datetime.now(timezone.utc),
                current_step="Loading server configurations"
            )
            
            # Get all servers from database
            # Note: Re-establish DB connection in child process
            from src.backend.services.supervisord import SupervisordService
            from src.backend.tinydb import Database
            from tinydb import Query
            
            db = Database()
            servers_table = db.db.table("servers")
            servers = servers_table.all()
            
            total_servers = len(servers)
            task_logger.info(f"Found {total_servers} servers to sync")
            
            # Update task with total server count
            self._update_task_status(
                task_id=task_id,
                total_servers=total_servers,
                current_step=f"Starting sync of {total_servers} servers"
            )
            
            # Load McpDirectory objects for each server (same as servers.py endpoint)
            directories = []
            synced_servers = []
            
            self._update_task_status(
                task_id=task_id,
                current_step="Loading MCP server directories"
            )
            
            for idx, server_data in enumerate(servers):
                try:
                    server_config = MCPServerConfig(**server_data)
                    directory = McpServerDirectory.from_server_config(server_config)
                    directories.append(directory)
                    
                    # Update synced_at timestamp
                    server_data["synced_at"] = datetime.now(timezone.utc).isoformat()
                    synced_servers.append(server_data)
                    
                    task_logger.info(f"Loaded McpDirectory for server: {server_config.name} (ID: {server_config.id})")
                except Exception as e:
                    task_logger.error(f"Failed to load McpDirectory for server {server_data.get('name', 'unknown')}: {str(e)}")
                    raise
            
            # Update synced_at timestamps in database
            for server_data in synced_servers:
                Server = Query()
                servers_table.update({"synced_at": server_data["synced_at"]}, Server.id == server_data["id"])
            
            # Sync each directory (clear, write files, install deps)
            for idx, directory in enumerate(directories):
                try:
                    progress = int((idx / total_servers) * 100)
                    self._update_task_status(
                        task_id=task_id,
                        progress=progress,
                        current_step=f"Syncing {directory.server_config.name}",
                        servers_processed=idx
                    )
                    
                    directory.sync(logger=task_logger)
                    task_logger.info(f"Successfully synced server: {directory.server_config.name}")
                    
                except Exception as e:
                    task_logger.error(f"Failed to sync server {directory.server_config.name}: {e}")
                    raise
            
            # Tell supervisord to reread and update configuration
            self._update_task_status(
                task_id=task_id,
                current_step="Updating supervisord configuration"
            )
            
            try:
                supervisor_service = SupervisordService()
                
                # Reread configuration
                task_logger.info("=" * 70)
                task_logger.info("SUPERVISORD CONFIGURATION UPDATE")
                task_logger.info("=" * 70)
                task_logger.info("Rereading supervisord configuration...")
                reread_result = supervisor_service.reread_config()
                
                # Log detailed reread results
                task_logger.info(f"✓ Supervisord reread completed")
                if reread_result.added_group_names:
                    task_logger.info(f"  Added groups: {', '.join(reread_result.added_group_names)}")
                if reread_result.changed_group_names:
                    task_logger.info(f"  Changed groups: {', '.join(reread_result.changed_group_names)}")
                if reread_result.removed_group_names:
                    task_logger.info(f"  Removed groups: {', '.join(reread_result.removed_group_names)}")
                
                # If there are changes, update supervisord
                if reread_result.added_group_names or reread_result.changed_group_names or reread_result.removed_group_names:
                    task_logger.info("")
                    task_logger.info("Configuration changes detected")
                    task_logger.info("Applying supervisord updates...")
                    
                    self._update_task_status(
                        task_id=task_id,
                        current_step="Applying supervisord updates"
                    )
                    
                    try:
                        update_result = supervisor_service.update()
                        
                        # Log detailed update results
                        task_logger.info(f"✓ Supervisord update completed")
                        if update_result.added_group_names:
                            task_logger.info(f"  Added groups: {', '.join(update_result.added_group_names)}")
                        if update_result.changed_group_names:
                            task_logger.info(f"  Changed groups: {', '.join(update_result.changed_group_names)}")
                        if update_result.removed_group_names:
                            task_logger.info(f"  Removed groups: {', '.join(update_result.removed_group_names)}")
                        
                        task_logger.info("Supervisord configuration updated successfully")
                        task_logger.info("=" * 70)
                        
                    except Exception as update_error:
                        task_logger.error(f"✗ Failed to update supervisord: {str(update_error)}", exc_info=True)
                        task_logger.error("=" * 70)
                        raise RuntimeError(f"Supervisord update failed: {str(update_error)}") from update_error
                else:
                    task_logger.info("No configuration changes detected")
                    task_logger.info("Supervisord is already in sync with current configuration")
                    task_logger.info("=" * 70)
                    
            except Exception as e:
                task_logger.error(f"✗ Failed to update supervisord configuration: {str(e)}", exc_info=True)
                # Mark task as failed due to supervisord error
                self._update_task_status(
                    task_id=task_id,
                    status=SyncTaskStatus.FAILED,
                    completed_at=datetime.now(timezone.utc),
                    error_message=f"Supervisord update failed: {str(e)}"
                )
                exit(1)
            
            # Mark task as completed
            self._update_task_status(
                task_id=task_id,
                status=SyncTaskStatus.COMPLETED,
                completed_at=datetime.now(timezone.utc),
                progress=100,
                current_step="Sync completed",
                servers_processed=total_servers
            )
            
            task_logger.info(f"Sync task {task_id} completed successfully")
            db.close()
            exit(0)
            
        except Exception as e:
            task_logger.error(f"Sync task {task_id} failed: {e}", exc_info=True)
            
            # Mark task as failed
            self._update_task_status(
                task_id=task_id,
                status=SyncTaskStatus.FAILED,
                completed_at=datetime.now(timezone.utc),
                error_message=str(e)
            )
            
            exit(1)
    
    def _create_task_logger(self, task_id: str, log_file_path: str) -> logging.Logger:
        """Create a dedicated logger for a sync task that writes to the task's log file.
        
        Args:
            task_id: Task identifier
            log_file_path: Path to write logs to
            
        Returns:
            Configured logger instance
        """
        task_logger = logging.getLogger(f"mcpzoo.sync.{task_id}")
        task_logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers to avoid duplication
        task_logger.handlers.clear()
        
        # File handler - writes all logs to the task's log file
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        task_logger.addHandler(file_handler)
        
        # Console handler - also log to console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        task_logger.addHandler(console_handler)
        
        # Prevent propagation to parent logger to avoid duplication
        task_logger.propagate = False
        
        return task_logger
    
    def _update_task_status(
        self,
        task_id: str,
        status: Optional[SyncTaskStatus] = None,
        progress: Optional[int] = None,
        current_step: Optional[str] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        error_message: Optional[str] = None,
        servers_processed: Optional[int] = None,
        total_servers: Optional[int] = None,
    ) -> None:
        """Update sync task status in database.
        
        Args:
            task_id: Task identifier
            status: New task status
            progress: Progress percentage 0-100
            current_step: Description of current operation
            started_at: Task start time
            completed_at: Task completion time
            error_message: Error message if failed
            servers_processed: Number of servers processed
            total_servers: Total servers to process
        """
        try:
            from src.backend.tinydb import Database
            db = Database()
            sync_tasks_table = db.db.table("sync_tasks")
            
            from tinydb import Query
            Task = Query()
            
            update_data = {}
            if status is not None:
                update_data["status"] = status.value
            if progress is not None:
                update_data["progress"] = progress
            if current_step is not None:
                update_data["current_step"] = current_step
            if started_at is not None:
                update_data["started_at"] = started_at.isoformat()
            if completed_at is not None:
                update_data["completed_at"] = completed_at.isoformat()
            if error_message is not None:
                update_data["error_message"] = error_message
            if servers_processed is not None:
                update_data["servers_processed"] = servers_processed
            if total_servers is not None:
                update_data["total_servers"] = total_servers
            
            sync_tasks_table.update(update_data, Task.id == task_id)
            
        except Exception as e:
            logger.error(f"Failed to update task status: {e}")
    
    async def get_task(self, task_id: str) -> Optional[dict]:
        """Get sync task by ID.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task data or None if not found
        """
        try:
            with database_service as db:
                sync_tasks_table = db.table("sync_tasks")
                from tinydb import Query
                Task = Query()
                return sync_tasks_table.get(Task.id == task_id)
        except Exception as e:
            logger.error(f"Error getting task {task_id}: {e}")
            return None
    
    async def list_tasks(self, limit: int = 50, offset: int = 0) -> dict:
        """List all sync tasks with pagination.
        
        Args:
            limit: Maximum number of tasks to return
            offset: Number of tasks to skip
            
        Returns:
            Dict with tasks list and pagination info
        """
        try:
            with database_service as db:
                sync_tasks_table = db.table("sync_tasks")
                all_tasks = sync_tasks_table.all()
                
                # Sort by created_at descending
                all_tasks.sort(
                    key=lambda x: x.get("created_at", ""),
                    reverse=True
                )
                
                total = len(all_tasks)
                tasks = all_tasks[offset:offset + limit]
                
                return {
                    "tasks": tasks,
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                }
        except Exception as e:
            logger.error(f"Error listing tasks: {e}")
            return {"tasks": [], "total": 0, "limit": limit, "offset": offset}
    
    async def get_task_logs(self, task_id: str, tail: int = 100) -> str:
        """Get logs for a sync task.
        
        Args:
            task_id: Task identifier
            tail: Number of lines to return from end of file
            
        Returns:
            Log content or empty string if not found
        """
        task = await self.get_task(task_id)
        if not task or not task.get("log_file_path"):
            return ""
        
        log_file = Path(task["log_file_path"])
        if not log_file.exists():
            return ""
        
        try:
            with open(log_file, "r") as f:
                lines = f.readlines()
                return "".join(lines[-tail:])
        except Exception as e:
            logger.error(f"Error reading logs for {task_id}: {e}")
            return ""


# Singleton instance
sync_service = SyncService()


def get_sync_service() -> SyncService:
    """Dependency for FastAPI to inject sync service."""
    return sync_service
