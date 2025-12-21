import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { Button } from './button'
import { ScrollArea } from './scroll-area'
import { Separator } from './separator'
import {
  Home,
  Server,
  Activity,
  Settings,
  LogOut
} from 'lucide-react'

interface SidebarProps {
  className?: string
}

export function Sidebar({ className }: SidebarProps) {
  const location = useLocation()

  const navItems = [
    { label: 'Dashboard', path: '/', icon: Home },
    { label: 'Server Configs', path: '/servers', icon: Server },
    { label: 'Processes', path: '/processes', icon: Activity },
  ]

  return (
    <div className={cn("flex-1 overflow-auto", className)}>
      <div className="space-y-4 py-4">
        <div className="px-3 py-2">
          <h2 className="mb-2 px-4 text-lg font-semibold tracking-tight">
            MCPZoo
          </h2>
          <div className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon
              return (
                <Button
                  key={item.path}
                  variant={location.pathname === item.path ? "secondary" : "ghost"}
                  className="w-full justify-start"
                  asChild
                >
                  <Link to={item.path}>
                    <Icon className="mr-2 h-4 w-4" />
                    {item.label}
                  </Link>
                </Button>
              )
            })}
          </div>
        </div>
        <Separator />
        <div className="px-3 py-2">
          <h2 className="mb-2 px-4 text-lg font-semibold tracking-tight">
            Settings
          </h2>
          <div className="space-y-1">
            <Button variant="ghost" className="w-full justify-start">
              <Settings className="mr-2 h-4 w-4" />
              Configuration
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
