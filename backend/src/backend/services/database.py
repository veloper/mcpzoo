import asyncio, uuid

from contextlib import contextmanager
from typing import Any, AsyncGenerator, Dict, List, Optional

from src.backend.tinydb import db


class DatabaseService:
    """Service for database operations."""
    
    def __init__(self, database=None):
        """Initialize with optional database instance (for testing)."""
        self._db = database or db
    
    def __enter__(self):
        """Context manager entry - yields raw TinyDB object."""
        return self._db.db
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass


# Singleton instance
database_service = DatabaseService()


def get_database_service() -> DatabaseService:
    """Dependency for FastAPI to inject database service."""
    return database_service
