import React, { useState, useEffect } from 'react'
import { Modal, Button, Form, Spinner, Alert } from 'react-bootstrap'
import { apiClient } from '../api/client'

interface LogViewerProps {
  serverId: string
  onClose: () => void
}

export function LogViewer({ serverId, onClose }: LogViewerProps) {
  const [logs, setLogs] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [logType, setLogType] = useState<'stdout' | 'stderr'>('stdout')

  const fetchLogs = async () => {
    try {
      setLoading(true)
      const data = await apiClient.getServerLogs(serverId, logType)
      setLogs(data.content || data)
      setError(null)
    } catch (err: any) {
      setError(err.message || 'Failed to fetch logs')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLogs()
    const interval = setInterval(fetchLogs, 2000)
    return () => clearInterval(interval)
  }, [serverId, logType])

  return (
    <Modal show onHide={onClose} size="lg">
      <Modal.Header closeButton>
        <Modal.Title>Logs: Server {serverId}</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <Form.Select value={logType} onChange={(e) => setLogType(e.target.value as any)} className="mb-3">
          <option value="stdout">stdout</option>
          <option value="stderr">stderr</option>
        </Form.Select>
        {loading && (
          <div className="text-center">
            <Spinner animation="border" />
          </div>
        )}
        {error && <Alert variant="danger">{error}</Alert>}
        {!loading && !error && (
          <pre style={{ maxHeight: '60vh', overflow: 'auto', backgroundColor: '#f5f5f5', padding: '1rem', borderRadius: '4px' }}>
            {logs || '(no logs yet)'}
          </pre>
        )}
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={onClose}>Close</Button>
      </Modal.Footer>
    </Modal>
  )
}

