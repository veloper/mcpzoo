import React from 'react'
import { useNavigate } from 'react-router-dom'
import { ServerForm } from '../components/ServerForm'

export function ServerCreatePage() {
  const navigate = useNavigate()

  const handleSuccess = () => {
    navigate('/servers')
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
