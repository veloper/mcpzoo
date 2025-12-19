import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import { DashboardLayout } from './components/DashboardLayout'
import { LoginPage } from './pages/LoginPage'
import { HomePage } from './pages/HomePage'
import { ServersPage } from './pages/ServersPage'
import { ServerCreatePage } from './pages/ServerCreatePage'
import { ServerEditPage } from './pages/ServerEditPage'
import { ProcessesPage } from './pages/ProcessesPage'
import { Loader2 } from "lucide-react"
import { TooltipProvider } from "@/components/ui/tooltip"

function AppContent() {
  const { isAuthenticated, loading } = useAuth()

  if (loading) {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return <LoginPage />
  }

  return (
    <DashboardLayout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/servers" element={<ServersPage />} />
        <Route path="/servers/new" element={<ServerCreatePage />} />
        <Route path="/servers/:id/edit" element={<ServerEditPage />} />
        <Route path="/processes" element={<ProcessesPage />} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </DashboardLayout>
  )
}

export default function App() {
  return (
    <TooltipProvider>
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </TooltipProvider>
  )
}
