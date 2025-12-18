import React, { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ServerForm } from '../components/ServerForm'
import { apiClient } from '../api/client'
import { Container, Spinner, Alert } from 'react-bootstrap'

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
        const data = await apiClient.getServer(id)
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
      <Container className="text-center py-5">
        <Spinner animation="border" />
      </Container>
    )
  }

  if (error) {
    return (
      <Container>
        <Alert variant="danger">{error}</Alert>
      </Container>
    )
  }

  if (!serverData) {
    return (
      <Container>
        <Alert variant="warning">Server not found</Alert>
      </Container>
    )
  }

  return (
    <ServerForm
      onSuccess={handleSuccess}
      onCancel={handleCancel}
      editingId={id}
    />
  )
}
