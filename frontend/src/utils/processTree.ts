export interface Process {
  pid?: number
  name: string
  status: string
  ppid?: number
  parent?: Process
  children?: Process[]
  uptime?: number
  memory_rss?: number
  memory_percent?: number
  cpu_percent?: number
  user?: string
  command?: string
  arguments?: string
  cwd?: string
  manager?: string
  created_at?: string
  exit_code?: number
  num_threads?: number
  nice?: number
  io_read_bytes?: number
  io_write_bytes?: number
}

export class ProcessTree {
  processes: Process[]

  constructor(processes: Process[]) {
    this.processes = processes
    this._buildTree()
  }

  private _buildTree() {
    const procDict: { [pid: number]: Process } = {}
    this.processes.forEach(p => {
      if (p.pid) procDict[p.pid] = p
    })
    this.processes.forEach(p => {
      if (p.ppid && procDict[p.ppid]) {
        const parent = procDict[p.ppid]
        if (!parent.children) parent.children = []
        parent.children.push(p)
        p.parent = parent
      }
    })
  }

  getAllByPids(pids: number[]): Process[] {
    return this.processes.filter(p => p.pid && pids.includes(p.pid))
  }

  getByPid(pid: number): Process | undefined {
    return this.processes.find(p => p.pid === pid)
  }

  getDescendantsOfPid(pid: number): Process[] {
    const proc = this.getByPid(pid)
    if (!proc) return []

    const descendants: Process[] = []
    const dfs = (p: Process) => {
      if (p.children) {
        p.children.forEach(child => {
          descendants.push(child)
          dfs(child)
        })
      }
    }
    dfs(proc)
    return descendants
  }

  findFirstLeafDescendantOfPid(pid: number): Process | undefined {
    const proc = this.getByPid(pid)
    if (!proc) return undefined
    
    // If this process has no children, it's a leaf
    if (!proc.children || proc.children.length === 0) {
      return proc
    }
    
    const descendants = this.getDescendantsOfPid(pid)
    return descendants.find(p => !p.children || p.children.length === 0)
  }

  getLeafPids(): number[] {
    return this.processes
      .filter(p => p.pid && (!p.children || p.children.length === 0))
      .map(p => p.pid!)
  }
}