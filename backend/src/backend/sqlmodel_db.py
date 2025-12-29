import uuid

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlmodel import SQLModel, select
from src.backend.models import Server, SyncTask
from src.backend.settings import get_settings


settings = get_settings()

class Database:
    """SQLModel/SQLite wrapper."""

    def __init__(self):
        """Initialize database."""
        db_path = Path(settings.sqlite_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Create SQLite engine
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        # Create tables
        SQLModel.metadata.create_all(bind=self.engine)

    def generate_id(self) -> str:
        """Generate a UUID for database documents."""
        return str(uuid.uuid4())

    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()

    def insert_server(self, server_data: Dict[str, Any]) -> str:
        """Insert server."""
        with self.get_session() as session:
            # Convert dict to ServerConfiguration, handling JSON fields
            server = Server(**server_data)
            session.add(server)
            session.commit()
            session.refresh(server)
            return server.id

    def get_server(self, server_id: str) -> Optional[Dict]:
        """Get server by ID."""
        with self.get_session() as session:
            server = session.get(Server, server_id)
            if server:
                return server.model_dump()
            return None

    def get_all_servers(self) -> List[Dict]:
        """Get all servers."""
        with self.get_session() as session:
            servers = session.execute(select(Server)).scalars().all()
            return [server.model_dump() for server in servers]

    def update_server(self, server_id: str, data: Dict[str, Any]) -> bool:
        """Update server."""
        with self.get_session() as session:
            server = session.get(Server, server_id)
            if server:
                for key, value in data.items():
                    setattr(server, key, value)
                session.commit()
                return True
            return False

    def delete_server(self, server_id: str) -> bool:
        """Delete server."""
        with self.get_session() as session:
            server = session.get(Server, server_id)
            if server:
                session.delete(server)
                session.commit()
                return True
            return False

    # SyncTask methods
    def insert_sync_task(self, task_data: Dict[str, Any]) -> int | None:
        """Insert sync task."""
        with self.get_session() as session:
            task = SyncTask(**task_data)
            session.add(task)
            session.commit()
            session.refresh(task)
            return task.id

    def get_sync_task(self, task_id: int) -> Optional[Dict]:
        """Get sync task by ID."""
        with self.get_session() as session:
            task = session.get(SyncTask, task_id)
            if task:
                return task.model_dump()
            return None

    def get_all_sync_tasks(self) -> List[Dict]:
        """Get all sync tasks."""
        with self.get_session() as session:
            tasks = session.execute(select(SyncTask)).scalars().all()
            return [task.model_dump() for task in tasks]

    def update_sync_task(self, task_id: int, data: Dict[str, Any]) -> bool:
        """Update sync task."""
        with self.get_session() as session:
            task = session.get(SyncTask, task_id)
            if task:
                for key, value in data.items():
                    setattr(task, key, value)
                session.commit()
                return True
            return False

    def delete_sync_task(self, task_id: int) -> bool:
        """Delete sync task."""
        with self.get_session() as session:
            task = session.get(SyncTask, task_id)
            if task:
                session.delete(task)
                session.commit()
                return True
            return False

    def delete_all_sync_tasks(self) -> int:
        """Delete all sync tasks. Returns the number of tasks deleted."""
        with self.get_session() as session:
            # Get count before deletion
            count = session.query(SyncTask).count()
            # Delete all tasks
            session.query(SyncTask).delete()
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
