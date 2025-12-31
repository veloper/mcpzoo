import React, { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ServerForm } from '../components/ServerForm'
import { apiClient } from '../api/client'
import { Loader2 } from 'lucide-react'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'

export function ServerEditPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [serverData, setServerData] = useState<any>(null)

  useEffect(() => {
    const fetchServer = async () => {
      try {
        if (!id) {
          setError('Server ID is required')
          return
        }
        const data = await apiClient.getServer(parseInt(id))
        setServerData(data)
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load server')
      } finally {
        setLoading(false)
      }
    }

    fetchServer()
  }, [id])

  const handleSuccess = () => {
    navigate('/servers')
  }

  const handleCancel = () => {
    navigate('/servers')
  }

  if (loading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="container py-8">
        <Alert variant="destructive">
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    )
  }

  if (!serverData) {
    return (
      <div className="container py-8">
        <Alert>
          <AlertTitle>Not Found</AlertTitle>
          <AlertDescription>Server not found</AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <ServerForm
      onSuccess={handleSuccess}
      onCancel={handleCancel}
      editingId={parseInt(id!)}
    />
  )
}
