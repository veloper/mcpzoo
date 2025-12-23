import { useState, useEffect } from 'react'
import { apiClient } from '../api/client'

// Module-level cache & in-flight fetch promise to deduplicate requests
let cachedProcesses: Process[] | null = null
let inFlightFetch: Promise<void> | null = null


export interface Process {
  name: string
  status: string
  pid?: number
  uptime?: number
  exit_code?: number
}

export function usePrograms() {
  const [processes, setProcesses] = useState<Process[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [startingProcesses, setStartingProcesses] = useState<Set<string>>(new Set())
  const [stoppingProcesses, setStoppingProcesses] = useState<Set<string>>(new Set())
  const [restartingProcesses, setRestartingProcesses] = useState<Set<string>>(new Set())

  // fetchProcesses supports a `force` flag to bypass module cache
  const fetchProcesses = async (force = false) => {
    try {
      // If we already have cached data and caller didn't force, use it
      if (!force && cachedProcesses) {
        setProcesses(cachedProcesses)
        setError(null)
        return
      }

      // If a fetch is already in-flight, await it and reuse the cached result
      if (!force && inFlightFetch) {
        await inFlightFetch
        setProcesses(cachedProcesses || [])
        setError(null)
        return
      }

      setLoading(true)

      // Start an in-flight fetch and store the promise so other instances can await it
      inFlightFetch = (async () => {
        const data = await apiClient.listPrograms()
        const processesData = data.test || data

        // The backend returns a list of Program objects (config + process)
        // We need to extract the process info
        const processList = Array.isArray(processesData) ? processesData.map((p: any) => ({
          name: p.config.name,
          status: p.process?.state || 'UNKNOWN',
          pid: p.process?.pid,
          uptime: p.process?.uptime,
          exit_code: p.process?.exit_code
        })) : []

        cachedProcesses = processList
        setProcesses(processList)
        setError(null)
      })()

      await inFlightFetch
    } catch (err: any) {
      setError(err.message || 'Failed to fetch processes')
      throw err
    } finally {
      inFlightFetch = null
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchProcesses()
  }, [])

  // Map backend Program object to our simple Process type
  const mapProgramToProcess = (p: any): Process => ({
    name: p?.config?.name,
    status: p?.process?.state || 'UNKNOWN',
    pid: p?.process?.pid,
    uptime: p?.process?.uptime,
    exit_code: p?.process?.exit_code
  })

  // Refresh a single process row by calling the backend status endpoint
  const refreshProcess = async (name: string) => {
    try {
      const data = await apiClient.getProgram(name)
      const prog = data.test || data
      const proc = mapProgramToProcess(prog)

      if (cachedProcesses) {
        const newList = cachedProcesses.slice()
        const idx = newList.findIndex(p => p.name === name)
        if (idx >= 0) newList[idx] = proc
        else newList.push(proc)
        cachedProcesses = newList
        setProcesses(newList)
      } else {
        cachedProcesses = [proc]
        setProcesses([proc])
      }
    } catch (err: any) {
      // If single-row refresh fails, fall back to a full refresh
      await fetchProcesses(true)
      throw err
    }
  }

  const startProcess = async (name: string) => {
    setStartingProcesses(prev => new Set(prev).add(name))
    try {
      await apiClient.startProgram(name)
      // Wait for the process to fully start and supervisor to update
      await new Promise(resolve => setTimeout(resolve, 2000))
      await refreshProcess(name)
    } catch (err: any) {
      setError(err.message || 'Failed to start process')
      throw err
    } finally {
      setStartingProcesses(prev => {
        const newSet = new Set(prev)
        newSet.delete(name)
        return newSet
      })
    }
  }

  const stopProcess = async (name: string) => {
    setStoppingProcesses(prev => new Set(prev).add(name))
    try {
      await apiClient.stopProgram(name)
      // Wait for the process to fully stop and supervisor to update
      await new Promise(resolve => setTimeout(resolve, 2000))
      await refreshProcess(name)
    } catch (err: any) {
      setError(err.message || 'Failed to stop process')
      throw err
    } finally {
      setStoppingProcesses(prev => {
        const newSet = new Set(prev)
        newSet.delete(name)
        return newSet
      })
    }
  }

  const restartProcess = async (name: string) => {
    // Mark restarting (also mark as starting/stopping to disable both buttons)
    setRestartingProcesses(prev => new Set(prev).add(name))
    setStoppingProcesses(prev => new Set(prev).add(name))
    setStartingProcesses(prev => new Set(prev).add(name))
    try {
      // Stop
      await apiClient.stopProgram(name)
      // Wait for supervisor to settle
      await new Promise(resolve => setTimeout(resolve, 2000))
      // Update row after stop
      await refreshProcess(name)

      // Start
      await apiClient.startProgram(name)
      // Wait again for start
      await new Promise(resolve => setTimeout(resolve, 2000))
      // Update row after start
      await refreshProcess(name)
    } catch (err: any) {
      setError(err.message || 'Failed to restart process')
      throw err
    } finally {
      setRestartingProcesses(prev => {
        const newSet = new Set(prev)
        newSet.delete(name)
        return newSet
      })
      setStoppingProcesses(prev => {
        const newSet = new Set(prev)
        newSet.delete(name)
        return newSet
      })
      setStartingProcesses(prev => {
        const newSet = new Set(prev)
        newSet.delete(name)
        return newSet
      })
    }
  }

  return {
    processes,
    loading,
    error,
    fetchProcesses,
    startProcess,
    stopProcess,
    restartProcess,
    startingProcesses,
    stoppingProcesses,
    restartingProcesses,
  }
}
