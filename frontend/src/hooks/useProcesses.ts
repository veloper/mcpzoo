import { useState, useEffect } from 'react'
import { apiClient } from '../api/client'

export interface Process {
  pid: number
  name: string
  state: string
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

export function useProcesses() {
  const [processes, setProcesses] = useState<Process[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchProcesses = async () => {
    try {
      setLoading(true)
      const data = await apiClient.getProcessTree()
      setProcesses(data)
      setError(null)
    } catch (err: any) {
      setError(err.message || 'Failed to fetch processes')
    } finally {
      setLoading(false)
    }
  }

  const refreshProcesses = async () => {
    try {
      console.log('🔄 Refreshing processes...')
      const data = await apiClient.getProcessTree()
      console.log('✅ Got processes data:', data?.length || 0, 'processes')
      setProcesses(data)
      setError(null)
      return data // Return data for timestamp tracking
    } catch (err: any) {
      console.error('❌ Failed to refresh processes:', err)
      setError(err.message || 'Failed to fetch processes')
      throw err
    }
  }

  useEffect(() => {
    fetchProcesses()
  }, [])

  return {
    processes,
    loading,
    error,
    refetch: fetchProcesses,
    refresh: refreshProcesses,
  }
}
