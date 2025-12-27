import re

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_serializer


class ProcessState(str, Enum):
    """Universal process states."""
    STOPPED = "STOPPED"
    RUNNING = "RUNNING"
    UNKNOWN = "UNKNOWN"
    # Supervisor-specific states
    BACKOFF = "BACKOFF"
    FATAL = "FATAL"
    EXITED = "EXITED"
    
class Process(BaseModel):
    """Universal Linux process model - pure data representation."""
    model_config = ConfigDict(use_enum_values=True)
    
    pid: int
    name: str
    state: ProcessState
    ppid: Optional[int] = None
    parent: Optional['Process'] = None
    children: Optional[List['Process']] = Field(default_factory=list)
    uptime: Optional[int] = None
    memory_rss: Optional[int] = None
    memory_percent: Optional[float] = None
    cpu_percent: Optional[float] = None
    user: Optional[str] = None
    command: Optional[str] = None
    arguments: Optional[str] = None
    cwd: Optional[str] = None
    manager: Optional[str] = None  # e.g., "supervisor", "systemd", or None
    created_at: Optional[datetime] = None
    exit_code: Optional[int] = None
    num_threads: Optional[int] = None
    nice: Optional[int] = None
    io_read_bytes: Optional[int] = None
    io_write_bytes: Optional[int] = None
    
    @property
    def is_child(self) -> bool:
        """Check if this process is a child process."""
        return self.parent is not None
    
    @property
    def parent_pid(self) -> Optional[int]:
        """Get parent process ID if this is a child process."""
        return self.parent.pid if self.parent else None
    
    @property
    def is_running(self) -> bool:
        """Check if process is in running state."""
        return self.state == ProcessState.RUNNING
    
    @property
    def is_stopped(self) -> bool:
        """Check if process is in stopped state."""
        return self.state in (ProcessState.STOPPED, ProcessState.EXITED, ProcessState.FATAL)
    
    @property
    def is_healthy(self) -> bool:
        """Check if process is in a healthy state."""
        return self.state in (ProcessState.RUNNING, ProcessState.EXITED)

    @model_serializer()
    def serialize_model(self) -> Dict[str, Any]:
        """Serialize model to JSON-compatible dict, excluding circular references."""
        data = {}
        for field_name in self.model_fields:
            if field_name not in ('parent',):
                value = getattr(self, field_name)
                if field_name == 'children' and value is not None:
                    data[field_name] = [child.serialize_model() for child in value]
                elif isinstance(value, datetime):
                    data[field_name] = value.isoformat()
                else:
                    data[field_name] = value
        return data


Process.model_rebuild()

class ProcessTree(BaseModel):
    """Tree structure of Linux processes."""
    model_config = ConfigDict()
    
    processes: List[Process] = Field(default_factory=list)
    
    def __init__(self, processes: List[Process]):
        super().__init__(processes=processes)
        self._build_tree()
    
    def _build_tree(self):
        """Build the process tree by linking parents and children."""
        proc_dict = {p.pid: p for p in self.processes}
        for p in self.processes:
            if p.ppid and p.ppid in proc_dict:
                parent = proc_dict[p.ppid]
                if parent.children is None:
                    parent.children = []
                parent.children.append(p)
                p.parent = parent
                
    def get_all_by_pids(self, pids: List[int]) -> List[Process]:
        """Get processes by a list of PIDs."""
        return [p for p in self.processes if p.pid in pids]
    
    def get_by_pid(self, pid: int) -> Optional[Process]:
        """Find a process by its PID."""
        return next((p for p in self.processes if p.pid == pid), None)
    
    def get_descendants_of_pid(self, pid: int) -> List[Process]:
        """Given a pid, return all descendant in DFS order
        
                A
                ├── B
                │   ├── C
                │   └── D
                └── E
                    └── F
        """
        proc = self.find_by_pid(pid)
        if not proc:
            return []
        
        descendants = []
        
        def dfs(p: Process):
            for child in p.children or []:
                descendants.append(child)
                dfs(child)
        
        dfs(proc)
        return descendants
    
    def find_first_leaf_descendant_of_pid(self, pid: int) -> Optional[Process]:
        """Given a pid, traverse the descendants to find the first descendant with no children."""
        
        dfs = self.get_descendants_of_pid(pid)
        if not dfs:
            return None
        
        for proc in dfs:
            if not proc.children:
                return proc # first descendant with no children
    
        
    @classmethod
    def create(cls) -> "ProcessTree":
        """Create a ProcessTree by running ps and parsing all processes."""
        import subprocess

        from datetime import datetime

        result = subprocess.run([
            "ps", "-axo",
            "pid,ppid,user,pcpu,pmem,rss,etime,lstart,state,nice,nlwp,comm,args"
        ], capture_output=True, text=True, check=True)
        
        # Regex for ps -o format: PID PPID USER %CPU %MEM RSS ELAPSED STARTED S NI NLWP COMMAND ARGS
        pattern = re.compile(
            r'^\s*(?P<pid>\d+)\s+'
            r'(?P<ppid>\d+|-)\s+'
            r'(?P<user>\S+)\s+'
            r'(?P<pcpu>[\d\.]+)\s+'
            r'(?P<pmem>[\d\.]+)\s+'
            r'(?P<rss>\d+)\s+'
            r'(?P<etime>[\d:-]+)\s+'
            r'(?P<lstart>\w{3}\s+\w{3}\s+\d{1,2}\s+\d{1,2}:\d{2}:\d{2}\s+\d{4})\s+'
            r'(?P<state>\S)\s+'
            r'(?P<nice>-?\d+)\s+'
            r'(?P<nlwp>\d+)\s+'
            r'(?P<comm>\S+)\s+'
            r'(?P<args>.+)$'
        )
        
        lines = result.stdout.splitlines()
        if lines and lines[0].strip().startswith('PID'):
            lines = lines[1:]
        
        print(f"Found {len(lines)} process lines to parse")

        processes = []
        parse_errors = 0
        
        def parse_etime(etime_str: str) -> int:
            """Parse ps etime format to seconds."""
            parts = etime_str.split('-')
            if len(parts) == 2:
                days = int(parts[0])
                time_part = parts[1]
            else:
                days = 0
                time_part = parts[0]
            
            time_parts = time_part.split(':')
            if len(time_parts) == 3:
                h, m, s = map(int, time_parts)
            elif len(time_parts) == 2:
                h = 0
                m, s = map(int, time_parts)
            else:
                h = 0
                m = 0
                s = int(time_parts[0])
            
            return days * 86400 + h * 3600 + m * 60 + s
        
        def map_ps_state(state_char: str) -> ProcessState:
            """Map ps state character to ProcessState enum."""
            if state_char == 'R':
                return ProcessState.RUNNING
            elif state_char in ('S', 'D', 'I'):
                return ProcessState.RUNNING  # Sleeping, uninterruptible, idle
            elif state_char == 'T':
                return ProcessState.STOPPED
            elif state_char == 'Z':
                return ProcessState.EXITED  # Zombie
            else:
                return ProcessState.UNKNOWN

        for i, line in enumerate(lines):  # Iterate over all process lines
            if line.strip():
                match = pattern.match(line)
                
                if not match:
                    print(f"ERROR: Failed to parse line {int(i)+1}: {line}")
                    parse_errors += 1
                    continue
                
                parts = match.groupdict()
                
                # Parse uptime
                etime_str = parts['etime']
                uptime = parse_etime(etime_str)
                
                # Parse created_at
                created_at = datetime.strptime(parts['lstart'], '%a %b %d %H:%M:%S %Y')
                
                # Map state
                state = map_ps_state(parts['state'])
                
                # Create process dict
                process_data = {
                    "pid": int(parts['pid']),
                    "ppid": int(parts['ppid']) if parts['ppid'] != '-' else None,
                    "user": parts['user'],
                    "cpu_percent": float(parts['pcpu']),
                    "memory_percent": float(parts['pmem']),
                    "memory_rss": int(parts['rss']) * 1024,  # Convert KB to bytes
                    "uptime": uptime,
                    "created_at": created_at,
                    "state": state,
                    "nice": int(parts['nice']),
                    "num_threads": int(parts['nlwp']),
                    "name": parts['comm'],  # Short command name
                    "command": parts['args'],  # Full command line
                    "arguments": parts['args'],
                }
                
                process = Process(**process_data)
                processes.append(process)
        
        return cls(processes)
    
    @staticmethod
    def _parse_etime(etime_str: str) -> int:
        """Parse ps etime format to seconds."""
        parts = etime_str.split('-')
        if len(parts) == 2:
            days = int(parts[0])
            time_part = parts[1]
        else:
            days = 0
            time_part = parts[0]
        
        time_parts = time_part.split(':')
        if len(time_parts) == 3:
            h, m, s = map(int, time_parts)
        elif len(time_parts) == 2:
            h = 0
            m, s = map(int, time_parts)
        else:
            h = 0
            m = 0
            s = int(time_parts[0])
        
        return days * 86400 + h * 3600 + m * 60 + s
    
    @staticmethod
    def _map_ps_state(state_char: str) -> ProcessState:
        """Map ps state character to ProcessState enum."""
        if state_char == 'R':
            return ProcessState.RUNNING
        elif state_char in ('S', 'D', 'I'):
            return ProcessState.RUNNING  # Sleeping, uninterruptible, idle
        elif state_char == 'T':
            return ProcessState.STOPPED
        elif state_char == 'Z':
            return ProcessState.EXITED  # Zombie
        else:
            return ProcessState.UNKNOWN
