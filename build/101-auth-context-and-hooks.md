# Phase 101: Auth Context and Custom Hooks

## Objective

Implement authentication context and custom React hooks for managing servers and processes.

## Prerequisites

- Phase 100 completed
- API client functional

## Steps

### 1.1: Create Auth Context (src/context/AuthContext.tsx)

Create `frontend/src/context/AuthContext.tsx`:

```typescript
import React, { createContext, useContext, useState, useEffect } from 'react'
import { apiClient } from '../api/client'

interface AuthContextType {
  isAuthenticated: boolean
  username: string | null
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
  loading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [username, setUsername] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check if token exists on mount
    const token = localStorage.getItem('access_token')
    if (token) {
      setIsAuthenticated(true)
      setUsername('user') // In production, fetch from /api/auth/verify
    }
    setLoading(false)
  }, [])

  const login = async (user: string, password: string) => {
    const response = await apiClient.login(user, password)
    apiClient.setToken(response.access_token)
    setIsAuthenticated(true)
    setUsername(user)
  }

  const logout = async () => {
    await apiClient.logout()
    setIsAuthenticated(false)
    setUsername(null)
    // Navigate to login/home (router will redirect to login if not authenticated)
    window.location.href = '/login'
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, username, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
```

### 1.2: Create useServers Hook (src/hooks/useServers.ts)

Create `frontend/src/hooks/useServers.ts`:

```typescript
import { useState, useEffect } from 'react'
import { apiClient } from '../api/client'

export interface Server {
  id: number
  name: string
  transport: string
  port: number
  status?: string
  created_at: string
  updated_at: string
}

export function useServers() {
  const [servers, setServers] = useState<Server[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchServers = async () => {
    try {
      setLoading(true)
      const data = await apiClient.listServers()
      setServers(data)
      setError(null)
    } catch (err: any) {
      setError(err.message || 'Failed to fetch servers')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchServers()
  }, [])

  const deleteServer = async (id: number) => {
    try {
      await apiClient.deleteServer(id)
      setServers(servers.filter(s => s.id !== id))
    } catch (err: any) {
      setError(err.message || 'Failed to delete server')
      throw err
    }
  }

  const startServer = async (id: number) => {
    try {
      await apiClient.startServer(id)
      await fetchServers()
    } catch (err: any) {
      setError(err.message || 'Failed to start server')
      throw err
    }
  }

  const stopServer = async (id: number) => {
    try {
      await apiClient.stopServer(id)
      await fetchServers()
    } catch (err: any) {
      setError(err.message || 'Failed to stop server')
      throw err
    }
  }

  return {
    servers,
    loading,
    error,
    fetchServers,
    deleteServer,
    startServer,
    stopServer,
  }
}
```

### 1.3: Create useProcesses Hook (src/hooks/useProcesses.ts)

Create `frontend/src/hooks/useProcesses.ts`:

```typescript
import { useState, useEffect } from 'react'
import { apiClient } from '../api/client'

export interface Process {
  name: string
  status: string
}

export function useProcesses() {
  const [processes, setProcesses] = useState<Process[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [pollInterval, setPollInterval] = useState(1000) // 1 second default

  const fetchProcesses = async () => {
    try {
      setLoading(true)
      const data = await apiClient.listProcesses()
      const processList = Object.entries(data).map(([name, status]) => ({
        name,
        status: status as string,
      }))
      setProcesses(processList)
      setError(null)
    } catch (err: any) {
      setError(err.message || 'Failed to fetch processes')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchProcesses()
    // Poll at configurable interval (1, 5, or 10 seconds)
    const interval = setInterval(fetchProcesses, pollInterval)
    return () => clearInterval(interval)
  }, [pollInterval])

  const startProcess = async (name: string) => {
    try {
      await apiClient.startProcess(name)
      await fetchProcesses()
    } catch (err: any) {
      setError(err.message || 'Failed to start process')
      throw err
    }
  }

  const stopProcess = async (name: string) => {
    try {
      await apiClient.stopProcess(name)
      await fetchProcesses()
    } catch (err: any) {
      setError(err.message || 'Failed to stop process')
      throw err
    }
  }

  return {
    processes,
    loading,
    error,
    fetchProcesses,
    startProcess,
    stopProcess,
    setPollInterval,
  }
}
```

---

## Verification Checklist

- [ ] `frontend/src/context/AuthContext.tsx` created
- [ ] `frontend/src/hooks/useServers.ts` created
- [ ] `frontend/src/hooks/useProcesses.ts` created
- [ ] Auth context works with provider pattern
- [ ] Custom hooks fetch data correctly
- [ ] Process polling works at configurable intervals

## Next Step

Proceed to [102-login-and-auth-components.md](./102-login-and-auth-components.md)
