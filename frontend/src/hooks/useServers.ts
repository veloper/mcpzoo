import { useState, useEffect, useCallback } from 'react'
import { apiClient } from '../api/client'

export interface Server {
  id: string
  name: string
  transport: string
  port: number
  status?: string
  created_at: string
  updated_at: string
}

export function useServers() {
  const [servers, setServers] = useState<Server[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchServers = async () => {
    try {
      setLoading(true)
      const data = await apiClient.listServers()
      setServers(Array.isArray(data) ? data : [])
      setError(null)
    } catch (err: any) {
      setError(err.message || 'Failed to fetch servers')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchServers()
  }, [])

  const deleteServer = async (id: string) => {
    try {
      await apiClient.deleteServer(id)
      setServers(servers.filter(s => s.id !== id))
    } catch (err: any) {
      setError(err.message || 'Failed to delete server')
      throw err
    }
  }

  const startServer = async (id: string) => {
    try {
      await apiClient.startProcess(`mcp_${servers.find(s => s.id === id)?.name}`)
      await fetchServers()
    } catch (err: any) {
      setError(err.message || 'Failed to start server')
      throw err
    }
  }

  const stopServer = async (id: string) => {
    try {
      await apiClient.stopProcess(`mcp_${servers.find(s => s.id === id)?.name}`)
      await fetchServers()
    } catch (err: any) {
      setError(err.message || 'Failed to stop server')
      throw err
    }
  }

  const fetchServerFiles = useCallback(async (serverId: string, serverConfig?: any) => {
    try {
      const response = await apiClient.getServerFiles(serverId, serverConfig)
      return response
    } catch (err: any) {
      setError(err.message || 'Failed to fetch server files')
      throw err
    }
  }, [])

  return {
    servers,
    loading,
    error,
    fetchServers,
    deleteServer,
    startServer,
    stopServer,
    fetchServerFiles,
  }
}
