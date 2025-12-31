import asyncio, uuid

from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from alembic import command
from alembic.config import Config
from src.backend.models import Base, Server, ServerRecord, SyncTask, SyncTaskRecord
from src.backend.settings import get_settings


settings = get_settings()


class Database:
    """SQLAlchemy 2.0/SQLite wrapper."""

    def __init__(self):
        """Initialize database."""
        db_path = Path(settings.sqlite_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Create SQLite engine
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        # Create tables if they don't exist (for development)
        Base.metadata.create_all(self.engine)

        # Note: Migrations are run manually via task runner, not on startup

    def generate_id(self) -> str:
        """Generate a UUID for database documents."""
        return str(uuid.uuid4())

    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()

    def insert_server(self, server_record: ServerRecord) -> Server:
        """Insert server record and return Pydantic model."""
        with self.get_session() as session:
            session.add(server_record)
            session.commit()
            session.refresh(server_record)

            return server_record.to_pydantic_model()

    def get_server(self, server_id: int) -> Optional[Server]:
        """Get server by ID and return Pydantic model."""
        with self.get_session() as session:
            server_record = session.get(ServerRecord, server_id)
            if server_record:
                return server_record.to_pydantic_model()
            return None

    def get_all_servers(self) -> List[Server]:
        """Get all servers and return Pydantic models."""
        with self.get_session() as session:
            server_records = session.execute(select(ServerRecord)).scalars().all()
            return [record.to_pydantic_model() for record in server_records]

    def update_server(self, server_id: int, server_record: ServerRecord) -> Optional[Server]:
        """Update server with new record and return Pydantic model."""
        with self.get_session() as session:
            # Merge the updated record into the session and commit
            server_record.id = server_id  # Ensure ID is set
            merged_record = session.merge(server_record)
            session.commit()
            session.refresh(merged_record)
            return merged_record.to_pydantic_model()

    def delete_server(self, server_id: int) -> bool:
        """Delete server."""
        with self.get_session() as session:
            server_record = session.get(ServerRecord, server_id)
            if server_record:
                session.delete(server_record)
                session.commit()
                return True
            return False

    # SyncTask methods
    def insert_sync_task(self, task_record: SyncTaskRecord) -> SyncTask:
        """Insert sync task record and return Pydantic model."""
        with self.get_session() as session:
            session.add(task_record)
            session.commit()
            session.refresh(task_record)

            return task_record.to_pydantic_model()

    def get_sync_task(self, task_id: int) -> Optional[SyncTask]:
        """Get sync task by ID and return Pydantic model."""
        with self.get_session() as session:
            task_record = session.get(SyncTaskRecord, task_id)
            if task_record:
                return task_record.to_pydantic_model()
            return None

    def get_all_sync_tasks(self) -> List[SyncTask]:
        """Get all sync tasks and return Pydantic models."""
        with self.get_session() as session:
            task_records = session.execute(select(SyncTaskRecord)).scalars().all()
            return [record.to_pydantic_model() for record in task_records]

    def update_sync_task(self, task_id: int, task_record: SyncTaskRecord) -> Optional[SyncTask]:
        """Update sync task with new record and return Pydantic model."""
        with self.get_session() as session:
            task_record.id = task_id  # Ensure ID is set
            merged_record = session.merge(task_record)
            session.commit()
            session.refresh(merged_record)
            return merged_record.to_pydantic_model()

    def delete_sync_task(self, task_id: int) -> bool:
        """Delete sync task."""
        with self.get_session() as session:
            task_record = session.get(SyncTaskRecord, task_id)
            if task_record:
                session.delete(task_record)
                session.commit()
                return True
            return False

    def delete_all_sync_tasks(self) -> int:
        """Delete all sync tasks. Returns the number of tasks deleted."""
        with self.get_session() as session:
            # Get count before deletion
            count = len(session.execute(select(SyncTaskRecord)).scalars().all())
            # Delete all tasks
            session.query(SyncTaskRecord).delete()
            session.commit()
            return count

    def close(self):
        """Close database."""
        self.engine.dispose()


# Singleton instance - lazy initialization
db = None


def get_database_instance() -> Database:
    """Get database instance, creating it if necessary."""
    global db
    if db is None:
        db = Database()
    return db


@contextmanager
def get_db():
    """Context manager yielding the database instance."""
    try:
        yield db
    finally:
        pass


class DatabaseService:
    """Service for database operations."""

    def __init__(self, database=None):
        """Initialize with optional database instance (for testing)."""
        self._db = database or get_database_instance()

    def get_db(self) -> Database:
        """Get the underlying database instance."""
        return self._db


@lru_cache()
def get_database_service() -> DatabaseService:
    """Dependency for FastAPI to inject database service."""
    return DatabaseService()
