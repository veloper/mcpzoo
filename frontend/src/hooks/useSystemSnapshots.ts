import { useState, useEffect, useMemo } from 'react'
import { apiClient } from '../api/client'

export interface SystemSnapshotProcess {
  id: number | null
  snapshot_id: number
  pid: number
  name: string
  state: string
  ppid?: number | null
  uptime?: number | null
  memory_rss?: number | null
  memory_percent?: number | null
  cpu_percent?: number | null
  user?: string | null
  command?: string | null
  arguments?: string | null
  cwd?: string | null
  manager?: string | null
  created_at?: string | null
  exit_code?: number | null
  num_threads?: number | null
  nice?: number | null
  io_read_bytes?: number | null
  io_write_bytes?: number | null
}

export interface SystemSnapshot {
  id: number | null
  timestamp: string  // ISO UTC - NEVER CONVERTED IN HOOK
  cpu_percent: number
  memory_percent: number
  load_average: number[]
  processes: SystemSnapshotProcess[]
}

export function useSystemSnapshots() {
  const [snapshots, setSnapshots] = useState<SystemSnapshot[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [processFilter, setProcessFilter] = useState<((p: SystemSnapshotProcess) => boolean) | null>(null)
  
  // Pagination state
  const [page, setPage] = useState(1)
  const [perPage, setPerPage] = useState(100)
  const [sort, setSort] = useState('timestamp')
  const [dir, setDir] = useState<'asc' | 'desc'>('desc')

  const fetchSnapshots = async () => {
    try {
      setLoading(true)
      // Always request with current pagination params
      const data = await apiClient.getSystemSnapshots({
        page,
        per_page: perPage,
        sort,
        dir
      })
      
      setSnapshots(data)
      setError(null)
    } catch (err: any) {
      // Silent failure - ignore error, keep stale data (like htop)
      setError(null)
    } finally {
      setLoading(false)
    }
  }

  const refreshSnapshots = async () => {
    try {
      const data = await apiClient.getSystemSnapshots({
        page,
        per_page: perPage,
        sort,
        dir
      })
      
      setSnapshots(data)
      setError(null)
      return data
    } catch (err: any) {
      // Silent failure - ignore error, keep stale data
      console.log('Refresh skipped, keeping stale data')
      setError(null)
      throw err
    }
  }

  useEffect(() => {
    fetchSnapshots()
  }, [page, perPage, sort, dir])

  // Get latest snapshot for current display
  const latestSnapshot = snapshots.length > 0 ? snapshots[0] : null
  const processes = latestSnapshot?.processes || []

  // Get filtered processes if filter is set
  const filteredProcesses = useMemo(() => {
    if (!processFilter) return processes
    return processes.filter(processFilter)
  }, [processes, processFilter])

  // Get historical data for a specific process across all snapshots
  // Used for spark chart data extraction
  const getProcessHistory = (pid: number) => {
    return snapshots
      .map(snapshot => {
        const process = snapshot.processes.find(p => p.pid === pid)
        return {
          timestamp: snapshot.timestamp,  // UTC - let consumer format
          cpu_percent: process?.cpu_percent ?? null,
          memory_percent: process?.memory_percent ?? null,
          memory_rss: process?.memory_rss ?? null,
        }
      })
      .filter(entry => entry.cpu_percent !== null || entry.memory_percent !== null)
  }

  // Get all unique processes across all snapshots (for charting)
  const getAllUniqueProcesses = useMemo(() => {
    const pidMap = new Map<number, SystemSnapshotProcess>()
    snapshots.forEach(snapshot => {
      snapshot.processes.forEach(process => {
        if (!pidMap.has(process.pid)) {
          pidMap.set(process.pid, process)
        }
      })
    })
    return Array.from(pidMap.values())
  }, [snapshots])

  return {
    snapshots,           // Full collection (UTC timestamps)
    processes,           // Latest snapshot's processes
    filteredProcesses,   // Filtered processes for search/UI
    latestSnapshot,      // Current system metrics
    loading,
    error,
    refetch: fetchSnapshots,
    refresh: refreshSnapshots,
    setProcessFilter,    // Set filter predicate for processes
    getProcessHistory,   // Extract historical data for PID
    getAllUniqueProcesses, // All processes across snapshots
    // Pagination controls
    page,
    setPage,
    perPage,
    setPerPage,
    sort,
    setSort,
    dir,
    setDir,
  }
}
