import React, { useState } from 'react'
import { useProcesses } from '../hooks/useProcesses'
import { Table, Badge, Button, Container, Row, Col, Form } from 'react-bootstrap'

export function ProcessesList() {
  const { processes, loading, error, startProcess, stopProcess, fetchProcesses } = useProcesses()

  if (loading && processes.length === 0) return <div className="text-center py-5">Loading processes...</div>
  if (error) return <div className="alert alert-danger">{error}</div>

  const mcpProcesses = processes.filter(p => p.name.startsWith('mcp_'))

  const getStatusVariant = (status: string) => {
    const s = status.toUpperCase()
    if (s === 'RUNNING') return 'success'
    if (s === 'STOPPED') return 'secondary'
    if (s === 'FATAL') return 'danger'
    return 'warning'
  }

  const formatUptime = (seconds?: number) => {
    if (seconds === undefined || seconds === 0) return '-'
    const h = Math.floor(seconds / 3600)
    const m = Math.floor((seconds % 3600) / 60)
    const s = seconds % 60
    return `${h}h ${m}m ${s}s`
  }

  return (
    <Container className="py-4">
      <Row className="align-items-center mb-4">
        <Col>
          <h2>MCP Server Processes</h2>
          <p className="text-muted">supervisord [group:mcp_servers]</p>
        </Col>
        <Col className="text-end">
          <Button 
            variant="outline-primary" 
            onClick={() => fetchProcesses()}
            disabled={loading}
          >
            {loading ? 'Refreshing...' : '🔄 Refresh'}
          </Button>
        </Col>
      </Row>

      {mcpProcesses.length === 0 ? (
        <p className="text-muted">No MCP server processes running. Click "Sync Processes" in the Servers tab.</p>
      ) : (
        <Table striped bordered hover responsive>
          <thead>
            <tr>
              <th>Process Name</th>
              <th>Status</th>
              <th>PID</th>
              <th>Uptime</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {mcpProcesses.map((proc) => (
              <tr key={proc.name}>
                <td>{proc.name}</td>
                <td>
                  <Badge bg={getStatusVariant(proc.status)}>
                    {proc.status}
                  </Badge>
                </td>
                <td>{proc.pid || '-'}</td>
                <td>{formatUptime(proc.uptime)}</td>
                <td>
                  {proc.status !== 'RUNNING' && (
                    <Button
                      size="sm"
                      variant="success"
                      className="me-2"
                      onClick={() => startProcess(proc.name)}
                    >
                      Start
                    </Button>
                  )}
                  {proc.status === 'RUNNING' && (
                    <Button
                      size="sm"
                      variant="warning"
                      className="me-2"
                      onClick={() => stopProcess(proc.name)}
                    >
                      Stop
                    </Button>
                  )}
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => {
                      stopProcess(proc.name)
                      setTimeout(() => startProcess(proc.name), 1000)
                    }}
                  >
                    Restart
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}
    </Container>
  )
}

