import logging, sys

from functools import lru_cache


_logger: logging.Logger | None = None

Logger = logging.Logger # exportable type alias

def get_logger() -> logging.Logger:
    """Get or create the singleton logger instance."""
    global _logger
    
    if _logger is not None:
        return _logger
    
    _logger = logging.getLogger("mcpzoo")
    _logger.setLevel(logging.DEBUG)
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    
    _logger.addHandler(handler)
    _logger.propagate = False
    
    return _logger


logger = get_logger()

@lru_cache()
def get_logging_service() -> logging.Logger:
    """Dependency for FastAPI to inject the logger."""
    return get_logger()
