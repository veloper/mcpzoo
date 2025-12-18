# Phase 105: Process List and Shared Components

## Objective

Implement process list component and shared UI components (header, log viewer).

## Prerequisites

- Phase 104 completed
- useProcesses hook functional

## Steps

### 1.1: Create Processes List Component (src/components/ProcessesList.tsx)

Create `frontend/src/components/ProcessesList.tsx`:

```typescript
import React, { useState } from 'react'
import { useProcesses } from '../hooks/useProcesses'

const POLL_INTERVALS = [1, 5, 10] // seconds

export function ProcessesList() {
  const { processes, loading, error, startProcess, stopProcess, setPollInterval } = useProcesses()
  const [interval, setInterval] = useState(1)

  if (loading) return <div>Loading processes...</div>
  if (error) return <div className="error-message">{error}</div>

  // Filter only MCP server processes (named mcp_{server_name})
  // Infer server config from process name — no separate mapping table needed
  const mcpProcesses = processes.filter(p => p.name.startsWith('mcp_'))

  const getStatusClass = (status: string) => {
    switch (status.toUpperCase()) {
      case 'RUNNING':
        return 'status-running'
      case 'STOPPED':
        return 'status-stopped'
      case 'FATAL':
        return 'status-fatal'
      default:
        return 'status-unknown'
    }
  }

  const handleIntervalChange = (newInterval: number) => {
    setInterval(newInterval)
    setPollInterval(newInterval * 1000) // Convert to ms
  }

  return (
    <div className="processes-container">
      <div className="section-header">
        <div>
          <h2>MCP Server Processes</h2>
          <p className="subtitle">supervisord [group:mcp_servers]</p>
        </div>
        <div className="poll-controls">
          <label htmlFor="pollInterval">Refresh every:</label>
          <select
            id="pollInterval"
            value={interval}
            onChange={(e) => handleIntervalChange(parseInt(e.target.value))}
            className="poll-select"
          >
            {POLL_INTERVALS.map(sec => (
              <option key={sec} value={sec}>{sec}s</option>
            ))}
          </select>
        </div>
      </div>

      {mcpProcesses.length === 0 ? (
        <p className="empty-state">No MCP server processes running. Click "Sync Processes" in the Servers tab.</p>
      ) : (
        <table className="processes-table">
          <thead>
            <tr>
              <th>Process Name</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {mcpProcesses.map((proc) => (
              <tr key={proc.name}>
                <td className="process-name">{proc.name}</td>
                <td>
                  <span className={`status-badge ${getStatusClass(proc.status)}`}>
                    {proc.status}
                  </span>
                </td>
                <td className="actions">
                  {proc.status !== 'RUNNING' && (
                    <button
                      className="btn-sm btn-success"
                      onClick={() => startProcess(proc.name)}
                    >
                      Start
                    </button>
                  )}
                  {proc.status === 'RUNNING' && (
                    <button
                      className="btn-sm btn-warning"
                      onClick={() => stopProcess(proc.name)}
                    >
                      Stop
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
```

### 1.2: Create Header Component (src/components/Header.tsx)

Create `frontend/src/components/Header.tsx`:

```typescript
import React from 'react'
import { useAuth } from '../context/AuthContext'

export function Header() {
  const { username, logout } = useAuth()

  return (
    <header className="header">
      <div className="header-content">
        <div className="logo">
          <h1>MCPZoo</h1>
        </div>
        <nav className="nav-menu">
          <a href="/">Home</a>
          <a href="/servers">Servers</a>
          <a href="/processes">Processes</a>
        </nav>
        <div className="user-section">
          {username && <span className="username">👤 {username}</span>}
          <button onClick={logout} className="btn-logout">Logout</button>
        </div>
      </div>
    </header>
  )
}
```

### 1.3: Create Log Viewer Component (src/components/LogViewer.tsx)

Create `frontend/src/components/LogViewer.tsx`:

```typescript
import React, { useState, useEffect } from 'react'
import { apiClient } from '../api/client'

interface LogViewerProps {
  serverId: number
  onClose: () => void
}

export function LogViewer({ serverId, onClose }: LogViewerProps) {
  const [logs, setLogs] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [logType, setLogType] = useState<'stdout' | 'stderr'>('stdout')

  const fetchLogs = async () => {
    try {
      setLoading(true)
      const data = await apiClient.getServerLogs(serverId, logType)
      setLogs(data.content)
      setError(null)
    } catch (err: any) {
      setError(err.message || 'Failed to fetch logs')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLogs()
    // Auto-refresh logs every 2 seconds
    const interval = setInterval(fetchLogs, 2000)
    return () => clearInterval(interval)
  }, [serverId, logType])

  return (
    <div className="log-viewer-modal">
      <div className="log-viewer-header">
        <h3>Logs: Server {serverId}</h3>
        <div className="log-controls">
          <select 
            value={logType} 
            onChange={(e) => setLogType(e.target.value as any)}
            className="log-type-select"
          >
            <option value="stdout">stdout</option>
            <option value="stderr">stderr</option>
          </select>
          <button onClick={onClose} className="btn-close">×</button>
        </div>
      </div>
      <div className="log-viewer-content">
        {loading && <p>Loading...</p>}
        {error && <p className="error-message">{error}</p>}
        {!loading && !error && (
          <pre className="log-output">{logs || '(no logs yet)'}</pre>
        )}
      </div>
    </div>
  )
}
```

---

## Verification Checklist

- [ ] `frontend/src/components/ProcessesList.tsx` created
- [ ] Process list filters MCP server processes correctly
- [ ] Status badges display with correct colors
- [ ] Start/Stop buttons work
- [ ] Poll interval selector works
- [ ] `frontend/src/components/Header.tsx` created
- [ ] `frontend/src/components/LogViewer.tsx` created
- [ ] Log viewer modal displays
- [ ] Log type selector works
- [ ] Logs auto-refresh

## Next Step

Proceed to [106-pages-and-routing.md](./106-pages-and-routing.md)
