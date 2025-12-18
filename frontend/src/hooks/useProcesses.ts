import { useState, useEffect } from 'react'
import { apiClient } from '../api/client'

export interface Process {
  name: string
  status: string
  pid?: number
  uptime?: number
  exit_code?: number
}

export function useProcesses() {
  const [processes, setProcesses] = useState<Process[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchProcesses = async () => {
    try {
      setLoading(true)
      const data = await apiClient.listProcesses()
      
      // The backend returns a list of Program objects (config + process)
      // We need to extract the process info
      const processList = Array.isArray(data) ? data.map((p: any) => ({
        name: p.config.name,
        status: p.process?.state || 'UNKNOWN',
        pid: p.process?.pid,
        uptime: p.process?.uptime,
        exit_code: p.process?.exit_code
      })) : []
      
      setProcesses(processList)
      setError(null)
    } catch (err: any) {
      setError(err.message || 'Failed to fetch processes')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchProcesses()
  }, [])

  const startProcess = async (name: string) => {
    try {
      await apiClient.startProcess(name)
      await fetchProcesses()
    } catch (err: any) {
      setError(err.message || 'Failed to start process')
      throw err
    }
  }

  const stopProcess = async (name: string) => {
    try {
      await apiClient.stopProcess(name)
      await fetchProcesses()
    } catch (err: any) {
      setError(err.message || 'Failed to stop process')
      throw err
    }
  }

  return {
    processes,
    loading,
    error,
    fetchProcesses,
    startProcess,
    stopProcess,
  }
}
