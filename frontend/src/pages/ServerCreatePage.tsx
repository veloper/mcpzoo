import React from 'react'
import { useNavigate } from 'react-router-dom'
import { ServerForm } from '../components/ServerForm'

export function ServerCreatePage() {
  const navigate = useNavigate()

  const handleSuccess = (serverId?: number) => {
    if (serverId) {
      // Redirect to edit page for the newly created server
      navigate(`/servers/${serverId}/edit`)
    } else {
      // Fallback to servers list if no ID provided
      navigate('/servers')
    }
  }

  const handleCancel = () => {
    navigate('/servers')
  }

  return (
    <ServerForm
      onSuccess={handleSuccess}
      onCancel={handleCancel}
    />
  )
}
