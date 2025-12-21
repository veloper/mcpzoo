from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from src.backend.environment import get_env


class Settings(BaseSettings):
    """Application settings loaded from environment-specific .env file."""
    
    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields like NGINX_PORT
        env_file=None,  # Will be set dynamically
    )
    
    # Environment
    app_env: str = ""
    
    # Application - REQUIRED (no defaults)
    app_username: str
    app_password: str
    
    # JWT Configuration
    jwt_secret: str = "dev-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_expiration_days: int = 7
    jwt_token_refresh_days: int = 7
    
    # Server
    fastapi_host: str = "127.0.0.1"
    fastapi_port: int = 8001
    
    # Database
    tinydb_path: str = "/app/data/tinydb.json"
    
    # MCP
    mcp_port_min: int = 8100
    mcp_port_max: int = 8199
    mcp_server_path: str = "/app/servers"
    
    # Logging
    log_level: str = "INFO"
    
    def __init__(self, **data):
        # Determine the correct .env file path before initialization
        env = get_env()
        env_file = f".env.{env}"
        project_root = Path(__file__).parent.parent.parent.parent
        
        # Check if environment-specific file exists
        if (project_root / env_file).exists():
            self.model_config['env_file'] = str(project_root / env_file)
        else:
            # Fallback to default .env
            self.model_config['env_file'] = str(project_root / ".env")
        
        super().__init__(**data)
        
        # Set app_env to current environment
        if not self.app_env:
            self.app_env = get_env()
        
        if not self.app_username or not self.app_password:
            raise ValueError("APP_USERNAME and APP_PASSWORD are required")



# Instantiate settings singleton
@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
