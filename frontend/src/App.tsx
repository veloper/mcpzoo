import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import { Header } from './components/Header'
import { LoginPage } from './pages/LoginPage'
import { HomePage } from './pages/HomePage'
import { ServersPage } from './pages/ServersPage'
import { ServerCreatePage } from './pages/ServerCreatePage'
import { ServerEditPage } from './pages/ServerEditPage'
import { ProcessesPage } from './pages/ProcessesPage'
import { Container, Spinner } from 'react-bootstrap'

function AppContent() {
  const { isAuthenticated, loading } = useAuth()

  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center" style={{ height: '100vh' }}>
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Loading...</span>
        </Spinner>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <LoginPage />
  }

  return (
    <>
      <Header />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/servers" element={<ServersPage />} />
        <Route path="/servers/new" element={<ServerCreatePage />} />
        <Route path="/servers/:id/edit" element={<ServerEditPage />} />
        <Route path="/processes" element={<ProcessesPage />} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  )
}
