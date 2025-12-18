import React from 'react'
import { useServers } from '../hooks/useServers'
import { useProcesses } from '../hooks/useProcesses'
import { Container, Row, Col, Card, Alert, Spinner } from 'react-bootstrap'

export function HomePage() {
  const { servers, loading: serversLoading } = useServers()
  const { processes, loading: processesLoading } = useProcesses()

  const runningProcesses = processes.filter(p => p.status === 'RUNNING').length
  const totalServers = servers.length

  if (serversLoading || processesLoading) {
    return (
      <div className="text-center py-5">
        <Spinner animation="border" />
      </div>
    )
  }

  return (
    <Container className="py-4">
      <section className="mb-5">
        <h1 className="display-4 mb-2">Welcome to MCPZoo</h1>
        <p className="lead text-muted">Manage your MCP servers with ease</p>
      </section>

      <section className="mb-5">
        <Row>
          <Col lg={6} className="mb-3">
            <Card className="h-100">
              <Card.Body>
                <Card.Title>Server Configurations</Card.Title>
                <div className="display-6 fw-bold text-primary">{totalServers}</div>
                <p className="text-muted small mt-2">Total servers configured</p>
              </Card.Body>
            </Card>
          </Col>
          <Col lg={6} className="mb-3">
            <Card className="h-100">
              <Card.Body>
                <Card.Title>Running Processes</Card.Title>
                <div className="display-6 fw-bold text-success">{runningProcesses}</div>
                <p className="text-muted small mt-2">Currently active processes</p>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      </section>

      <section>
        <Card>
          <Card.Body>
            <Card.Title className="mb-3">Quick Actions</Card.Title>
            <div className="d-flex gap-2 flex-wrap">
              <a href="/servers" className="btn btn-primary">Manage Servers</a>
              <a href="/processes" className="btn btn-secondary">View Processes</a>
            </div>
          </Card.Body>
        </Card>
      </section>
    </Container>
  )
}

