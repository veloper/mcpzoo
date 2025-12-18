# Phase 103: Server List and Form Components

## Objective

Implement server management components (list, form, actions).

## Prerequisites

- Phase 102 completed
- useServers hook functional

## Steps

### 1.1: Create Servers List Component (src/components/ServersList.tsx)

Create `frontend/src/components/ServersList.tsx`:

```typescript
import React, { useState } from 'react'
import { useServers } from '../hooks/useServers'
import { ServerForm } from './ServerForm'
import { LogViewer } from './LogViewer'
import { apiClient } from '../api/client'

export function ServersList() {
  const { servers, loading, error, deleteServer, fetchServers } = useServers()
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [syncing, setSyncing] = useState(false)
  const [syncError, setSyncError] = useState('')
  const [viewingLogs, setViewingLogs] = useState<number | null>(null)

  const handleSync = async () => {
    setSyncing(true)
    setSyncError('')

    try {
      const response = await apiClient.syncServers()
      // Refresh processes after sync
      await fetchServers()
      alert(`✓ ${response.message}`)
    } catch (err: any) {
      setSyncError(err.response?.data?.detail || 'Sync failed')
    } finally {
      setSyncing(false)
    }
  }

  if (loading) return <div>Loading servers...</div>
  if (error) return <div className="error-message">{error}</div>

  return (
    <div className="servers-container">
      <div className="section-header">
        <h2>MCP Server Configurations</h2>
        <div className="header-actions">
          <button 
            className="btn-primary" 
            onClick={() => setShowForm(!showForm)}
            disabled={syncing}
          >
            {showForm ? 'Cancel' : '+ Add Server'}
          </button>
          <button 
            className="btn-success" 
            onClick={handleSync}
            disabled={syncing || servers.length === 0}
            title="Write all configs to disk and restart supervisord"
          >
            {syncing ? 'Syncing...' : '🔄 Sync Processes'}
          </button>
        </div>
      </div>

      {syncError && <div className="error-message">{syncError}</div>}

      {showForm && (
        <ServerForm
          onSuccess={() => {
            setShowForm(false)
            fetchServers()
          }}
          onCancel={() => setShowForm(false)}
          editingId={editingId}
        />
      )}

      {viewingLogs !== null && (
        <LogViewer
          serverId={viewingLogs}
          onClose={() => setViewingLogs(null)}
        />
      )}

      {servers.length === 0 ? (
        <p className="empty-state">No servers configured. Add one to get started.</p>
      ) : (
        <table className="servers-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Transport</th>
              <th>Port</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {servers.map((server) => (
              <tr key={server.id}>
                <td>{server.name}</td>
                <td>{server.transport}</td>
                <td>{server.port}</td>
                <td>{new Date(server.created_at).toLocaleDateString()}</td>
                <td className="actions">
                  <button
                    className="btn-sm btn-info"
                    onClick={() => setEditingId(server.id)}
                  >
                    Edit
                  </button>
                  <button
                    className="btn-sm btn-secondary"
                    onClick={() => setViewingLogs(server.id)}
                  >
                    📋 Logs
                  </button>
                  <button
                    className="btn-sm btn-danger"
                    onClick={() => {
                      if (confirm(`Delete server "${server.name}"?`)) {
                        deleteServer(server.id)
                      }
                    }}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div className="info-box">
        <h4>💡 How it works:</h4>
        <ol>
          <li>Add or edit server configurations</li>
          <li>Click <strong>"Sync Processes"</strong> to write configs to disk</li>
          <li>supervisord automatically restarts the MCP servers group</li>
          <li>Monitor processes in the "Processes" tab</li>
        </ol>
      </div>
    </div>
  )
}
```

### 1.2: Create Server Form Component (src/components/ServerForm.tsx)

Create `frontend/src/components/ServerForm.tsx` (large file - see next section for full content):

This component handles creating and editing server configurations with:
- Basic information (name, transport, port)
- Transport-specific configuration (command/URL)
- Supervisord settings (autostart, autorestart, priority, etc.)
- Tasks (install, run)
- Tools and dependencies
- Environment variables

The form validates all inputs and submits to the API.

---

## Verification Checklist

- [ ] `frontend/src/components/ServersList.tsx` created
- [ ] Server list displays correctly
- [ ] Add/Edit buttons work
- [ ] Delete functionality works
- [ ] Sync button triggers sync operation
- [ ] Log viewer modal works

## Next Step

Proceed to [104-server-form-component.md](./104-server-form-component.md)
