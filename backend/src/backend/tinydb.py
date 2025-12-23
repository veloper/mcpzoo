import asyncio, json, uuid

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.backend.settings import get_settings
from tinydb import Query, TinyDB


settings = get_settings()

class Database:
    """TinyDB wrapper."""
    
    def __init__(self):
        """Initialize database."""
        db_path = Path(settings.tinydb_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Check if database file exists and is valid JSON
        if db_path.exists():
            try:
                with open(db_path, 'r') as f:
                    json.load(f)  # Validate JSON
            except json.JSONDecodeError as e:
                # JSON is corrupted, create backup and remove it
                backup_path = db_path.with_suffix('.json.backup')
                print(f"Warning: Database file {db_path} has corrupted JSON ({e}), creating backup at {backup_path} and creating new database")
                db_path.replace(backup_path)
            except IOError as e:
                # File is unreadable, create backup and remove it
                backup_path = db_path.with_suffix('.json.backup')
                print(f"Warning: Database file {db_path} is unreadable ({e}), creating backup at {backup_path} and creating new database")
                db_path.replace(backup_path)

        self.db = TinyDB(str(db_path))
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Ensure required tables exist."""
        for table_name in ["servers", "processes", "logs", "sync_tasks"]:
            if table_name not in self.db.tables():
                self.db.table(table_name)
    
    def generate_id(self) -> str:
        """Generate a UUID for database documents."""
        return str(uuid.uuid4())
    
    def insert_server(self, server_data: Dict[str, Any]) -> str:
        """Insert server."""
        doc_id = self.db.table("servers").insert(server_data)
        return str(doc_id)
    
    def get_server(self, server_id: str) -> Optional[Dict]:
        """Get server by ID."""
        Server = Query()
        return self.db.table("servers").get(Server.id == server_id)
    
    def get_all_servers(self) -> List[Dict]:
        """Get all servers."""
        return self.db.table("servers").all()
    
    def update_server(self, server_id: str, data: Dict[str, Any]) -> bool:
        """Update server."""
        Server = Query()
        results = self.db.table("servers").update(data, Server.id == server_id)
        return len(results) > 0
    
    def delete_server(self, server_id: str) -> bool:
        """Delete server."""
        Server = Query()
        removed = self.db.table("servers").remove(Server.id == server_id)
        return len(removed) > 0
    
    def close(self):
        """Close database."""
        self.db.close()


db = Database()


@asynccontextmanager
async def get_db():
    """Async context manager yielding the singleton TinyDB object."""
    try:
        yield db.db
    finally:
        pass
