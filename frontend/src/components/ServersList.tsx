import React, { useState } from 'react'
import { useServers } from '../hooks/useServers'
import { ServerForm } from './ServerForm'
import { LogViewer } from './LogViewer'
import { apiClient } from '../api/client'
import { Table, Button, Container, Row, Col } from 'react-bootstrap'

export function ServersList() {
  const { servers, loading, error, deleteServer, fetchServers } = useServers()
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [syncing, setSyncing] = useState(false)
  const [syncError, setSyncError] = useState('')
  const [viewingLogs, setViewingLogs] = useState<string | null>(null)

  const handleSync = async () => {
    setSyncing(true)
    setSyncError('')

    try {
      const response = await apiClient.syncServers()
      await fetchServers()
      alert(`✓ ${response.message}`)
    } catch (err: any) {
      setSyncError(err.response?.data?.detail || 'Sync failed')
    } finally {
      setSyncing(false)
    }
  }

  if (loading) return <div>Loading servers...</div>
  if (error) return <div className="alert alert-danger">{error}</div>

  return (
    <Container>
      <Row className="align-items-center mb-3">
        <Col>
          <h2>MCP Server Configurations</h2>
        </Col>
        <Col className="text-end">
          <Button variant="primary" className="me-2" onClick={() => setShowForm(!showForm)} disabled={syncing}>
            {showForm ? 'Cancel' : '+ Add Server'}
          </Button>
          <Button variant="secondary" onClick={handleSync} disabled={syncing || servers.length === 0} title="Write all configs to disk and restart supervisord">
            {syncing ? 'Syncing...' : '🔄 Sync Processes'}
          </Button>
        </Col>
      </Row>

      {syncError && <div className="alert alert-danger">{syncError}</div>}

      {showForm && (
        <ServerForm
          onSuccess={() => {
            setShowForm(false)
            setEditingId(null)
            fetchServers()
          }}
          onCancel={() => {
            setShowForm(false)
            setEditingId(null)
          }}
          editingId={editingId}
        />
      )}

      {viewingLogs !== null && (
        <LogViewer
          serverId={viewingLogs}
          onClose={() => setViewingLogs(null)}
        />
      )}

      {servers.length === 0 ? (
        <p className="text-muted">No servers configured. Add one to get started.</p>
      ) : (
        <Table striped bordered hover responsive>
          <thead>
            <tr>
              <th>Name</th>
              <th>Transport</th>
              <th>Port</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {servers.map((server) => (
              <tr key={server.id}>
                <td>{server.name}</td>
                <td>{server.transport}</td>
                <td>{server.port}</td>
                <td>{new Date(server.created_at).toLocaleDateString()}</td>
                <td>
                  <Button size="sm" variant="info" className="me-2" onClick={() => { setEditingId(server.id); setShowForm(true) }}>Edit</Button>
                  <Button size="sm" variant="secondary" className="me-2" onClick={() => setViewingLogs(server.id)}>📋 Logs</Button>
                  <Button size="sm" variant="danger" onClick={() => { if (confirm(`Delete server "${server.name}"?`)) { deleteServer(server.id) } }}>Delete</Button>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}

      <div className="info-box">
        <h4>💡 How it works:</h4>
        <ol>
          <li>Add server configurations</li>
          <li>Click <strong>"Sync Processes"</strong> to write configs to disk</li>
          <li>supervisord automatically restarts the MCP servers group</li>
          <li>Monitor processes in the "Processes" tab</li>
        </ol>
      </div>
    </Container>
  )
}
