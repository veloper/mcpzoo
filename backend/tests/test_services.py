"""Test implementations of services."""

import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from src.backend.services.database import DatabaseService


class InMemoryDatabaseService(DatabaseService):
    """In-memory database service for testing."""

    def __init__(self):
        """Initialize with in-memory SQLite."""
        # Create in-memory SQLite database
        engine = create_engine("sqlite:///:memory:", echo=False)
        SQLModel.metadata.create_all(engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        # Create a mock database instance that uses the in-memory session
        class InMemoryDatabase:
            def __init__(self, session_factory):
                self.SessionLocal = session_factory
                self.servers = {}
                self.sync_tasks = {}

            def get_session(self):
                return self.SessionLocal()

            def insert_server(self, server_data):
                server_id = server_data.get("id", str(uuid.uuid4()))
                self.servers[server_id] = server_data.copy()
                return server_id

            def get_server(self, server_id):
                return self.servers.get(server_id)

            def get_all_servers(self):
                return list(self.servers.values())

            def update_server(self, server_id, data):
                if server_id in self.servers:
                    self.servers[server_id].update(data)
                    return True
                return False

            def delete_server(self, server_id):
                if server_id in self.servers:
                    del self.servers[server_id]
                    return True
                return False

            def insert_sync_task(self, task_data):
                task_id = task_data.get("id", str(uuid.uuid4()))
                self.sync_tasks[task_id] = task_data.copy()
                return task_id

            def get_sync_task(self, task_id):
                return self.sync_tasks.get(task_id)

            def get_all_sync_tasks(self):
                return list(self.sync_tasks.values())

            def update_sync_task(self, task_id, data):
                if task_id in self.sync_tasks:
                    self.sync_tasks[task_id].update(data)
                    return True
                return False

            def delete_sync_task(self, task_id):
                if task_id in self.sync_tasks:
                    del self.sync_tasks[task_id]
                    return True
                return False

        super().__init__(InMemoryDatabase(SessionLocal))
        self._id_counter = 0


