import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useServers } from '../hooks/useServers'
import { apiClient } from '../api/client'
import { Table, Button, Container, Row, Col, Alert, Spinner } from 'react-bootstrap'

export function ServersPage() {
  const navigate = useNavigate()
  const { servers, loading, error, deleteServer, fetchServers } = useServers()
  const [syncing, setSyncing] = React.useState(false)
  const [syncError, setSyncError] = React.useState('')

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

  const handleDeleteServer = async (id: string, name: string) => {
    if (confirm(`Are you sure you want to delete server "${name}"?`)) {
      try {
        await deleteServer(id)
      } catch (err: any) {
        alert(err.message || 'Failed to delete server')
      }
    }
  }

  if (loading) {
    return (
      <Container className="text-center py-5">
        <Spinner animation="border" />
      </Container>
    )
  }

  return (
    <Container className="py-4">
      {error && <Alert variant="danger">{error}</Alert>}
      {syncError && <Alert variant="danger">{syncError}</Alert>}

      <Row className="align-items-center mb-4">
        <Col>
          <h2>MCP Server Configurations</h2>
        </Col>
        <Col className="text-end">
          <Button 
            variant="primary" 
            className="me-2" 
            onClick={() => navigate('/servers/new')}
          >
            + Add Server
          </Button>
          <Button 
            variant="info" 
            onClick={handleSync} 
            disabled={syncing || servers.length === 0}
            title="Write all configs to disk and restart supervisord"
          >
            {syncing ? 'Syncing...' : '🔄 Sync Processes'}
          </Button>
        </Col>
      </Row>

      {servers.length === 0 ? (
        <Alert variant="info">
          No servers configured. <a href="/servers/new">Add one to get started.</a>
        </Alert>
      ) : (
        <div className="table-responsive">
          <Table striped bordered hover>
            <thead>
              <tr>
                <th>Name</th>
                <th>Transport</th>
                <th>Port</th>
                <th>Created</th>
                <th className="text-center">Actions</th>
              </tr>
            </thead>
            <tbody>
              {servers.map((server) => (
                <tr key={server.id}>
                  <td className="fw-bold">{server.name}</td>
                  <td>
                    <span className="badge bg-secondary">{server.transport}</span>
                  </td>
                  <td>{server.port}</td>
                  <td className="small text-muted">
                    {new Date(server.created_at).toLocaleDateString()}
                  </td>
                  <td className="text-center">
                    <Button 
                      size="sm" 
                      variant="primary" 
                      className="me-2"
                      onClick={() => navigate(`/servers/${server.id}/edit`)}
                    >
                      Edit
                    </Button>
                    <Button 
                      size="sm" 
                      variant="danger"
                      onClick={() => handleDeleteServer(server.id, server.name)}
                    >
                      Delete
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </div>
      )}
    </Container>
  )
}

