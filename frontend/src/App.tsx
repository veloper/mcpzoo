import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import { DashboardLayout } from './components/DashboardLayout'
import { LoginPage } from './pages/LoginPage'
import { HomePage } from './pages/HomePage'
import { ServersPage } from './pages/ServersPage'
import { ServerCreatePage } from './pages/ServerCreatePage'
import { ServerEditPage } from './pages/ServerEditPage'
import { ProgramsPage } from './pages/ProgramsPage'
import { SyncsPage } from './pages/SyncsPage'
import SystemPage from './pages/SystemPage'
import { Loader2 } from "lucide-react"
import { TooltipProvider } from "@/components/ui/tooltip"
import { Toaster } from "@/components/ui/sonner"

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
        <Route path="/programs" element={<ProgramsPage />} />
        <Route path="/system" element={<SystemPage />} />
        <Route path="/syncs" element={<SyncsPage />} />
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
      <Toaster position="top-center" />
    </TooltipProvider>
  )
}
