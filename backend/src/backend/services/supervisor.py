"""Supervisord service wrapper with typed Program models."""

from functools import lru_cache

from src.backend.supervisor import SupervisorService


@lru_cache()
def get_supervisor_service() -> SupervisorService:
    """Dependency for FastAPI to inject supervisord service."""
    return SupervisorService()
