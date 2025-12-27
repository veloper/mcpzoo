import asyncio, uuid

from contextlib import contextmanager
from typing import Any, AsyncGenerator, Dict, List, Optional

from src.backend.sqlmodel_db import get_database_instance


class DatabaseService:
    """Service for database operations."""
    
    def __init__(self, database=None):
        """Initialize with optional database instance (for testing)."""
        self._db = database or get_database_instance()
    
    def __enter__(self):
        """Context manager entry - yields database instance."""
        return self._db
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass


# Singleton instance
# Lazy initialization
_database_service = None


def get_database_service() -> DatabaseService:
    """Dependency for FastAPI to inject database service."""
    global _database_service
    if _database_service is None:
        _database_service = DatabaseService()
    return _database_service
