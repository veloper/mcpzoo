from enum import Enum


class SyncTaskStatus(str, Enum):
    """Status of a sync task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SupervisorProcessState(str, Enum):
    """Supervisor process states."""
    STOPPED = "stopped"
    BACKOFF = "backoff"
    RUNNING = "running"
    FATAL = "fatal"
    EXITED = "exited"
    UNKNOWN = "unknown"


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
