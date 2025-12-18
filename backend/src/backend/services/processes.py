"""Processes service for managing system processes."""
import os
import signal
from typing import List, Optional, Callable
from src.backend.models import Process, ProcessState


class ProcessesService:
    """Service for querying and managing system processes."""
    
    def __init__(self):
        pass
    
    def get_all_processes(self) -> List[Process]:
        """Get all processes on the system.
        
        Returns:
            List of Process models representing all system processes.
        """
        # Placeholder for future implementation
        # Could use psutil to query system processes
        return []
    
    def get_process_by_pid(self, pid: int) -> Optional[Process]:
        """Get process information by PID.
        
        Args:
            pid: Process ID
            
        Returns:
            Process model if found, None otherwise.
        """
        # Placeholder for future implementation
        return None
    
    def get_process_by_name(self, name: str) -> Optional[Process]:
        """Get process information by name.
        
        Args:
            name: Process name
            
        Returns:
            Process model if found, None otherwise.
        """
        # Placeholder for future implementation
        return None
    
    def filter_processes(self, 
                        state: Optional[ProcessState] = None,
                        manager: Optional[str] = None,
                        user: Optional[str] = None) -> List[Process]:
        """Filter processes by state, manager, and/or user.
        
        Args:
            state: Filter by ProcessState
            manager: Filter by manager (e.g., "supervisor", "systemd")
            user: Filter by user running the process
            
        Returns:
            List of filtered Process models.
        """
        # Placeholder for future implementation
        return []
    
    def find_processes(self, predicate: Callable[[Process], bool]) -> List[Process]:
        """Find processes matching a custom predicate.
        
        Args:
            predicate: Function that takes a Process and returns bool
            
        Returns:
            List of processes matching the predicate.
        """
        return [p for p in self.get_all_processes() if predicate(p)]
    
    def send_signal(self, process: Process, sig: int) -> bool:
        """Send OS signal to process.
        
        Args:
            process: Process to send signal to
            sig: Signal number to send
            
        Returns:
            True if signal sent successfully, False otherwise.
        """
        try:
            os.kill(process.pid, sig)
            return True
        except (ProcessLookupError, PermissionError, OSError):
            return False
    
    def send_term(self, process: Process) -> bool:
        """Send SIGTERM to gracefully stop process.
        
        Args:
            process: Process to terminate
            
        Returns:
            True if signal sent successfully, False otherwise.
        """
        return self.send_signal(process, signal.SIGTERM)
    
    def send_kill(self, process: Process) -> bool:
        """Send SIGKILL to force stop process.
        
        Args:
            process: Process to kill
            
        Returns:
            True if signal sent successfully, False otherwise.
        """
        return self.send_signal(process, signal.SIGKILL)
    
    def send_stop(self, process: Process) -> bool:
        """Send SIGSTOP to pause process.
        
        Args:
            process: Process to pause
            
        Returns:
            True if signal sent successfully, False otherwise.
        """
        return self.send_signal(process, signal.SIGSTOP)
    
    def send_cont(self, process: Process) -> bool:
        """Send SIGCONT to resume process.
        
        Args:
            process: Process to resume
            
        Returns:
            True if signal sent successfully, False otherwise.
        """
        return self.send_signal(process, signal.SIGCONT)
    
    def send_hup(self, process: Process) -> bool:
        """Send SIGHUP to reload process configuration.
        
        Args:
            process: Process to reload
            
        Returns:
            True if signal sent successfully, False otherwise.
        """
        return self.send_signal(process, signal.SIGHUP)
    
    def send_int(self, process: Process) -> bool:
        """Send SIGINT to interrupt process (Ctrl+C equivalent).
        
        Args:
            process: Process to interrupt
            
        Returns:
            True if signal sent successfully, False otherwise.
        """
        return self.send_signal(process, signal.SIGINT)
    
    def send_usr1(self, process: Process) -> bool:
        """Send SIGUSR1 for custom notification.
        
        Args:
            process: Process to notify
            
        Returns:
            True if signal sent successfully, False otherwise.
        """
        return self.send_signal(process, signal.SIGUSR1)
    
    def send_usr2(self, process: Process) -> bool:
        """Send SIGUSR2 for custom notification.
        
        Args:
            process: Process to notify
            
        Returns:
            True if signal sent successfully, False otherwise.
        """
        return self.send_signal(process, signal.SIGUSR2)
    
    def send_abrt(self, process: Process) -> bool:
        """Send SIGABRT for abnormal termination.
        
        Args:
            process: Process to abort
            
        Returns:
            True if signal sent successfully, False otherwise.
        """
        return self.send_signal(process, signal.SIGABRT)
    
    def send_quit(self, process: Process) -> bool:
        """Send SIGQUIT for quit with core dump.
        
        Args:
            process: Process to quit
            
        Returns:
            True if signal sent successfully, False otherwise.
        """
        return self.send_signal(process, signal.SIGQUIT)
    
    def is_running(self, process: Process) -> bool:
        """Check if process is currently running.
        
        Args:
            process: Process to check
            
        Returns:
            True if process is running, False otherwise.
        """
        try:
            os.kill(process.pid, 0)  # Signal 0 checks existence without sending
            return True
        except (ProcessLookupError, OSError):
            return False
    
    def get_children(self, process: Process) -> List[Process]:
        """Get all child processes of a given process.
        
        Args:
            process: Parent process
            
        Returns:
            List of child processes.
        """
        return [p for p in self.get_all_processes() if p.parent_pid == process.pid]
    
    def terminate_tree(self, process: Process) -> bool:
        """Terminate process and all its children.
        
        Args:
            process: Process to terminate (and its children)
            
        Returns:
            True if all processes terminated successfully, False otherwise.
        """
        success = True
        for child in self.get_children(process):
            success = self.terminate_tree(child) and success
        success = self.send_term(process) and success
        return success
    
    def kill_tree(self, process: Process) -> bool:
        """Kill process and all its children forcefully.
        
        Args:
            process: Process to kill (and its children)
            
        Returns:
            True if all processes killed successfully, False otherwise.
        """
        success = True
        for child in self.get_children(process):
            success = self.kill_tree(child) and success
        success = self.send_kill(process) and success
        return success
    
    def refresh(self, process: Process, **updates) -> bool:
        """Refresh process information from system in place.
        
        Fetches latest process data and updates the process object dynamically.
        Can also accept optional field overrides.
        
        Args:
            process: Process to refresh (modified in place)
            **updates: Optional field overrides to apply
            
        Returns:
            True if process was updated successfully, False if process no longer exists.
        """
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


# Global service instance
processes_service = ProcessesService()


def get_processes_service() -> ProcessesService:
    """Dependency for FastAPI to inject processes service."""
    return processes_service
