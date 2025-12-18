# Phase 032: Database Wrapper

## Objective

Implement TinyDB wrapper for managing MCP server configurations.

## Prerequisites

- Phase 030 completed
- `backend/src/backend/settings.py` exists

## Steps

### 3.1: Create Database Wrapper (backend/src/backend/tinydb.py)

Create `backend/src/backend/tinydb.py`:

**Key Features**:
- Thread-safe ID generation with mutex (auto-incrementing integers)
- Server configs stored as-is, awaiting sync operation
- No automatic file/directory creation

```python
from tinydb import TinyDB, Query
from pathlib import Path
from typing import Any, Dict, List, Optional
from .settings import settings


class Database:
    """TinyDB wrapper."""
    
    def __init__(self):
        """Initialize database."""
        db_path = Path(settings.tinydb_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db = TinyDB(str(db_path))
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Ensure required tables exist."""
        # Tables auto-create on first insert
        # Initialize with default tables
        for table_name in ["servers", "processes", "logs"]:
            if table_name not in self.db.tables():
                self.db.table(table_name)
    
    def insert_server(self, server_data: Dict[str, Any]) -> int:
        """Insert MCP server config."""
        table = self.db.table("servers")
        return table.insert(server_data)
    
    def get_server(self, server_id: int) -> Optional[Dict]:
        """Get server by ID."""
        table = self.db.table("servers")
        Server = Query()
        result = table.get(Server.id == server_id)
        return result.dict() if result else None
    
    def get_all_servers(self) -> List[Dict]:
        """Get all servers."""
        table = self.db.table("servers")
        return [doc for doc in table.all()]
    
    def update_server(self, server_id: int, data: Dict[str, Any]) -> bool:
        """Update server."""
        table = self.db.table("servers")
        Server = Query()
        results = table.update(data, Server.id == server_id)
        return len(results) > 0
    
    def delete_server(self, server_id: int) -> bool:
        """Delete server."""
        table = self.db.table("servers")
        Server = Query()
        removed = table.remove(Server.id == server_id)
        return len(removed) > 0
    
    def close(self):
        """Close database."""
        self.db.close()


# Global database instance
db = Database()
```

---

## Verification Checklist

- [ ] `backend/src/backend/tinydb.py` created
- [ ] Database initializes without errors
- [ ] Server insert, retrieve, update, and delete operations work
- [ ] Database file created at configured path

## Next Step

Proceed to [033-supervisor-api.md](./033-supervisor-api.md)
