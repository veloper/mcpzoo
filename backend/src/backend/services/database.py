import asyncio, uuid

from contextlib import contextmanager
from functools import lru_cache
from typing import Any, AsyncGenerator, Dict, List, Optional

from src.backend.sqlmodel_db import Database, get_database_instance


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
