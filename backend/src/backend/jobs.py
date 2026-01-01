
"""Jobs that run primarily in the monitoring agent."""

from datetime import datetime, timezone
from functools import cached_property
from typing import Callable

import psutil

# Assuming these are defined elsewhere in your codebase
from src.backend.models import SystemSnapshotProcessRecord, SystemSnapshotRecord
from src.backend.services.database import get_database_service
from src.backend.settings import get_settings


settings = get_settings()

class BaseJob:
    """Base class for jobs."""

    @classmethod
    def execute(cls):
        """Given to the scheduler to run the job."""
        job = cls()
        return job.run()
    
    def run(self):
        """Run the job."""
        raise NotImplementedError("Subclasses must implement the run method.")

class SnapshotSystemCleanupJob(BaseJob):
    """Cleanup logs older than retention period of 30 minutes."""
    
    def run(self):
        db = get_database_service().get_db()
        retention_minutes = settings.process_snapshot_retention_minutes
        cutoff_time = datetime.now(timezone.utc).timestamp() - (retention_minutes * 60) 
        
        with db.get_session() as session:
            old_snapshots = session.query(SystemSnapshotRecord).filter(
                SystemSnapshotRecord.timestamp < datetime.fromtimestamp(cutoff_time, tz=timezone.utc)
            ).all()
            
            for snapshot in old_snapshots:
                # Delete associated process records first
                session.query(SystemSnapshotProcessRecord).filter(
                    SystemSnapshotProcessRecord.snapshot_id == snapshot.id
                ).delete()
                
                # Then delete the snapshot record
                session.delete(snapshot)
            
            session.commit()
        
        print(f"Cleaned up {len(old_snapshots)} old system snapshots.")

class SnapshotSystemJob(BaseJob):
    
    """Collect system metrics snapshot."""
    
    @cached_property
    def cpu_percent(self) -> float:
        return psutil.cpu_percent(interval=0.1)

    @cached_property
    def memory_percent(self) -> float:
        return psutil.virtual_memory().percent

    @cached_property
    def load_average(self) -> list[float]:
        return list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else [0.0, 0.0, 0.0]
        
    @cached_property
    def timestamp(self) -> datetime:
        return datetime.now(timezone.utc)    
    
    @cached_property
    def process_records(self) -> list[SystemSnapshotProcessRecord]:
        psutil_processes = psutil.process_iter()
        process_records = []
        for proc in psutil_processes:
            try:
                with proc.oneshot():
                    io_read_bytes : int | None = None
                    io_write_bytes : int | None = None
                    if hasattr(proc, 'io_counters') and callable(getattr(proc, 'io_counters')):
                        io_counters : Callable = getattr(proc, 'io_counters')
                        if io_counters and hasattr(io_counters, 'read_bytes') and hasattr(io_counters, 'write_bytes'):
                            io_read_bytes = getattr(io_counters, 'read_bytes')
                            io_write_bytes = getattr(io_counters, 'write_bytes')
                    
                    process_record = SystemSnapshotProcessRecord(
                        snapshot_id=None,  # To be set after snapshot is created
                        pid=proc.pid,
                        name=proc.name(),
                        state=proc.status(),
                        ppid=proc.ppid(),
                        uptime=int(self.timestamp.timestamp()) - int(proc.create_time()),
                        memory_rss=proc.memory_info().rss,
                        memory_percent=proc.memory_percent(),
                        cpu_percent=proc.cpu_percent(interval=None),
                        user=proc.username(),
                        command=proc.cmdline()[0] if proc.cmdline() else "",
                        arguments=" ".join(proc.cmdline()[1:]) if len(proc.cmdline()) > 1 else "",
                        cwd=proc.cwd() if proc.cwd() else "",
                        manager=None,
                        created_at=datetime.fromtimestamp(proc.create_time(), tz=timezone.utc),
                        exit_code=proc.wait(timeout=0) if proc.is_running() == False else None,
                        num_threads=proc.num_threads(),
                        nice=proc.nice(),
                        io_read_bytes=io_read_bytes,
                        io_write_bytes=io_write_bytes,
                    )
                    process_records.append(process_record)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue  # Process terminated or access denied during iteration    
        return process_records
    
    @cached_property
    def system_snapshot_record(self) -> SystemSnapshotRecord:
        return SystemSnapshotRecord(
            timestamp=self.timestamp,
            cpu_percent=self.cpu_percent,
            memory_percent=self.memory_percent,
            load_average=self.load_average
        )


    def run(self) -> SystemSnapshotRecord:
            
        db = get_database_service().get_db()
        snapshot_record = self.system_snapshot_record
        process_records = self.process_records
        
        with db.get_session() as session:
            session.add(snapshot_record)
            session.commit()
            session.refresh(snapshot_record)

            for process_record in process_records:
                process_record.snapshot_id = snapshot_record.id
                session.add(process_record)
            
            session.commit()        
    
        return snapshot_record
