from enum import Enum


class SyncTaskStatus(str, Enum):
    """Status of a sync task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class LogLevel(str, Enum):
    """Log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class MCPServerTransport(str, Enum):
    """MCP server transport type."""
    SSE = "sse"
    HTTP = "http"
    STDIO = "stdio"
