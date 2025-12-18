import React from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Navbar, Container, Nav, Button } from 'react-bootstrap'

export function Header() {
  const { username, logout } = useAuth()

  return (
    <Navbar bg="light" expand="lg" className="mb-3">
      <Container>
        <Navbar.Brand as={Link} to="/">MCPZoo</Navbar.Brand>
        <Navbar.Toggle />
        <Navbar.Collapse>
          <Nav className="me-auto">
            <Nav.Link as={Link} to="/">Home</Nav.Link>
            <Nav.Link as={Link} to="/servers">Servers</Nav.Link>
            <Nav.Link as={Link} to="/processes">Processes</Nav.Link>
          </Nav>
          <div className="d-flex align-items-center">
            {username && <span className="me-3">👤 {username}</span>}
            <Button variant="outline-secondary" size="sm" onClick={logout}>Logout</Button>
          </div>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  )
}

