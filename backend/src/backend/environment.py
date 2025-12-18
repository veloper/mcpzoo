import os
from typing import Optional

# Global environment state
_current_env: Optional[str] = None


def get_env() -> str:
    """
    Get the current application environment.
    
    Priority:
    1. Current set environment (if set via set_env())
    2. APP_ENV environment variable
    3. Default to 'dev'
    
    Returns:
        str: Current environment (e.g., 'dev', 'prod', 'test')
    """
    global _current_env
    
    if _current_env is not None:
        return _current_env
    
    env = os.getenv('APP_ENV', 'dev').lower().strip()
    return env


def set_env(env: str) -> None:
    """
    Set the application environment.
    
    Args:
        env: Environment name (e.g., 'dev', 'prod', 'test')
    """
    global _current_env
    _current_env = env.lower().strip()


def get_env_file_path() -> str:
    """
    Get the path to the environment file for the current environment.
    
    Logic:
    1. Try to load .env.{APP_ENV}
    2. If not found, try .env
    3. Returns the path that will be used
    
    Returns:
        str: Path to the .env file to use
    """
    env = get_env()
    env_file = f".env.{env}"
    
    # Check if environment-specific file exists
    if os.path.exists(env_file):
        return env_file
    
    # Fallback to default .env
    return ".env"
