import React from 'react'
import { useAuth } from '../hooks/useAuth'
import { Sidebar } from './ui/sidebar'
import { Button } from './ui/button'
import { Separator } from './ui/separator'
import { LogOut, Menu } from 'lucide-react'
import { cn } from '@/lib/utils'

interface DashboardLayoutProps {
  children: React.ReactNode
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
  const { username, logout } = useAuth()

  return (
    <div className="min-h-screen bg-background grid grid-cols-[280px_1fr]">
      <aside className="border-r bg-background">
        <div className="flex h-full flex-col">
          <Sidebar />
          <div className="flex items-center justify-between p-4 border-t mt-auto">
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium">
                Admin
              </span>
            </div>
            <Button variant="ghost" size="sm" onClick={logout}>
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </aside>

      <main className="min-h-screen">
        <div className="container mx-auto p-6">
          {children}
        </div>
      </main>
    </div>
  )
}
