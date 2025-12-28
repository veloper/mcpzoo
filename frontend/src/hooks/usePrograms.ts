import { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { apiClient } from '../api/client'


export interface Program {
  name: string
  status: string
  pid?: number
  uptime?: number
  exit_code?: number
}

export function usePrograms() {
  const location = useLocation()
  const [programs, setPrograms] = useState<Program[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [startingPrograms, setStartingPrograms] = useState<Set<string>>(new Set())
  const [stoppingPrograms, setStoppingPrograms] = useState<Set<string>>(new Set())
  const [restartingPrograms, setRestartingPrograms] = useState<Set<string>>(new Set())

  const fetchPrograms = async () => {
    try {
      setLoading(true)
      const data = await apiClient.listPrograms()
      const programsData = data.test || data

      // The backend returns SupervisorProcess objects directly
      // Map SupervisorProcess fields to our Program interface
      const programList = Array.isArray(programsData) ? programsData
        .filter((p: any) => p && p.name)
        .map((p: any) => {
          // Calculate uptime: if running (state=20), uptime = now - start, else 0
          const uptime = (p.state === 20 && p.now && p.start) ? (p.now - p.start) : 0

          return {
            name: p.name,
            status: p.statename || 'UNKNOWN',  // Use statename (human-readable) instead of state (int)
            pid: p.pid || undefined,
            uptime: uptime || undefined,
            exit_code: p.exitstatus || undefined
          }
        }) : []

      setPrograms(programList)
      setError(null)
    } catch (err: any) {
      setError(err.message || 'Failed to fetch programs')
      throw err
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPrograms()
  }, [location.pathname])



  // Refresh a single program row by calling the backend status endpoint
  const refreshProgram = async (name: string) => {
    try {
      const data = await apiClient.getProgram(name)
      const progData = data.test || data

      // Backend returns a single SupervisorProcess object, map it to Program interface
      const uptime = (progData.state === 20 && progData.now && progData.start) ? (progData.now - progData.start) : 0
      const prog: Program = {
        name: progData.name,
        status: progData.statename || 'UNKNOWN',
        pid: progData.pid || undefined,
        uptime: uptime || undefined,
        exit_code: progData.exitstatus || undefined
      }

      setPrograms(prevPrograms => {
        const newList = prevPrograms.slice()
        const idx = newList.findIndex(p => p.name === name)
        if (idx >= 0) {
          newList[idx] = prog
        } else {
          newList.push(prog)
        }
        return newList
      })
    } catch (err: any) {
      // If single-row refresh fails, fall back to a full refresh
      await fetchPrograms()
      throw err
    }
  }

  const startProgram = async (name: string) => {
    setStartingPrograms(prev => new Set(prev).add(name))
    try {
      await apiClient.startProgram(name)
      // Wait for the program to fully start and supervisor to update
      await new Promise(resolve => setTimeout(resolve, 2000))
      await refreshProgram(name)
    } catch (err: any) {
      setError(err.message || 'Failed to start program')
      throw err
    } finally {
      setStartingPrograms(prev => {
        const newSet = new Set(prev)
        newSet.delete(name)
        return newSet
      })
    }
  }

  const stopProgram = async (name: string) => {
    setStoppingPrograms(prev => new Set(prev).add(name))
    try {
      await apiClient.stopProgram(name)
      // Wait for the program to fully stop and supervisor to update
      await new Promise(resolve => setTimeout(resolve, 2000))
      await refreshProgram(name)
    } catch (err: any) {
      setError(err.message || 'Failed to stop program')
      throw err
    } finally {
      setStoppingPrograms(prev => {
        const newSet = new Set(prev)
        newSet.delete(name)
        return newSet
      })
    }
  }

  const restartProgram = async (name: string) => {
    // Mark restarting (also mark as starting/stopping to disable both buttons)
    setRestartingPrograms(prev => new Set(prev).add(name))
    setStoppingPrograms(prev => new Set(prev).add(name))
    setStartingPrograms(prev => new Set(prev).add(name))
    try {
      // Stop
      await apiClient.stopProgram(name)
      // Wait for supervisor to settle
      await new Promise(resolve => setTimeout(resolve, 2000))
      // Update row after stop
      await refreshProgram(name)

      // Start
      await apiClient.startProgram(name)
      // Wait again for start
      await new Promise(resolve => setTimeout(resolve, 2000))
      // Update row after start
      await refreshProgram(name)
    } catch (err: any) {
      setError(err.message || 'Failed to restart program')
      throw err
    } finally {
      setRestartingPrograms(prev => {
        const newSet = new Set(prev)
        newSet.delete(name)
        return newSet
      })
      setStoppingPrograms(prev => {
        const newSet = new Set(prev)
        newSet.delete(name)
        return newSet
      })
      setStartingPrograms(prev => {
        const newSet = new Set(prev)
        newSet.delete(name)
        return newSet
      })
    }
  }

  return {
    programs,
    loading,
    error,
    fetchPrograms,
    startProgram,
    stopProgram,
    restartProgram,
    startingPrograms,
    stoppingPrograms,
    restartingPrograms,
  }
}
