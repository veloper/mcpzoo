"""Processes service for managing system processes."""
import os, signal

from functools import lru_cache
from typing import Callable, List, Optional

from src.backend.process import Process, ProcessState


class ProcessesService:
    """Service for querying and managing system processes."""
    
    def __init__(self):
        pass
    
    def get_all_processes(self) -> List[Process]:
        """Get all processes on the system."""
        try:
            # Use the ProcessTree.create() method which implements ps parsing
            from src.backend.process import ProcessTree
            tree = ProcessTree.create()
            return tree.processes
        except Exception as e:
            # Log the error but return empty list on failure
            import logging
            logging.error(f"Failed to get processes: {e}")
            return []
    
    def get_process_by_pid(self, pid: int) -> Optional[Process]:
        """Get process information by PID."""
        try:
            # Use the ProcessTree.create() method which implements ps parsing
            from src.backend.process import ProcessTree
            tree = ProcessTree.create()
            return tree.get_by_pid(pid)
        except Exception as e:
            # Log the error but return None on failure
            import logging
            logging.error(f"Failed to get process by PID {pid}: {e}")
            return None
    
    def get_process_by_name(self, name: str) -> Optional[Process]:
        """Get process information by name."""
        try:
            # Use the ProcessTree.create() method which implements ps parsing
            from src.backend.process import ProcessTree
            tree = ProcessTree.create()

            # Find first process with matching name
            for process in tree.processes:
                if process.name == name:
                    return process
            return None
        except Exception as e:
            # Log the error but return None on failure
            import logging
            logging.error(f"Failed to get process by name {name}: {e}")
            return None
    
    def filter_processes(self,
                        state: Optional[ProcessState] = None,
                        manager: Optional[str] = None,
                        user: Optional[str] = None) -> List[Process]:
        """Filter processes by state, manager, and/or user."""
        try:
            # Use the ProcessTree.create() method which implements ps parsing
            from src.backend.process import ProcessTree
            tree = ProcessTree.create()

            filtered = []
            for process in tree.processes:
                # Apply filters
                if state and process.state != state:
                    continue
                if manager and process.manager != manager:
                    continue
                if user and process.user != user:
                    continue
                filtered.append(process)

            return filtered
        except Exception as e:
            # Log the error but return empty list on failure
            import logging
            logging.error(f"Failed to filter processes: {e}")
            return []
    
    def find_processes(self, predicate: Callable[[Process], bool]) -> List[Process]:
        """Find processes matching a custom predicate."""
        return [p for p in self.get_all_processes() if predicate(p)]
    
    def send_signal(self, process: Process, sig: int) -> bool:
        """Send OS signal to process."""
        try:
            os.kill(process.pid, sig)
            return True
        except (ProcessLookupError, PermissionError, OSError):
            return False
        
        
    def send_term(self, process: Process) -> bool: return self.send_signal(process, signal.SIGTERM)
    def send_kill(self, process: Process) -> bool: return self.send_signal(process, signal.SIGKILL)
    def send_stop(self, process: Process) -> bool: return self.send_signal(process, signal.SIGSTOP)
    def send_cont(self, process: Process) -> bool: return self.send_signal(process, signal.SIGCONT)
    def send_hup(self, process: Process) -> bool: return self.send_signal(process, signal.SIGHUP)
    def send_int(self, process: Process) -> bool: return self.send_signal(process, signal.SIGINT)
    def send_usr1(self, process: Process) -> bool: return self.send_signal(process, signal.SIGUSR1)
    def send_usr2(self, process: Process) -> bool: return self.send_signal(process, signal.SIGUSR2)
    def send_abrt(self, process: Process) -> bool: return self.send_signal(process, signal.SIGABRT)
    def send_quit(self, process: Process) -> bool: return self.send_signal(process, signal.SIGQUIT)
    
    def is_running(self, process: Process) -> bool:
        """Check if process is currently running."""
        try:
            os.kill(process.pid, 0)  # Signal 0 checks existence without sending
            return True
        except (ProcessLookupError, OSError):
            return False
    
    def get_children(self, process: Process) -> List[Process]:
        """Get all child processes of a given process."""
        return [p for p in self.get_all_processes() if p.parent_pid == process.pid]
    
    def terminate_tree(self, process: Process) -> bool:
        """Terminate process and all its children."""
        success = True
        for child in self.get_children(process):
            success = self.terminate_tree(child) and success
        success = self.send_term(process) and success
        return success
    
    def kill_tree(self, process: Process) -> bool:
        """Kill process and all its children forcefully."""
        success = True
        for child in self.get_children(process):
            success = self.kill_tree(child) and success
        success = self.send_kill(process) and success
        return success
    
    def refresh(self, process: Process, **updates) -> bool:
        """Refresh process information from system in place."""
        updated = self.get_process_by_pid(process.pid)
        if updated is None:
            return False
        
        # Get all current fields from updated process
        updated_data = updated.model_dump()
        
        # Apply any explicit overrides
        updated_data.update(updates)
        
        # Update all fields on the original process object
        for field, value in updated_data.items():
            if hasattr(process, field):
                object.__setattr__(process, field, value)
        
        return True


@lru_cache()
def get_processes_service() -> ProcessesService:
    """Dependency for FastAPI to inject processes service."""
    return ProcessesService()
