# Phase 104: Server Form Component

## Objective

Implement the comprehensive server configuration form component.

## Prerequisites

- Phase 103 completed

## Steps

### 1.1: Create Server Form Component (src/components/ServerForm.tsx)

Create `frontend/src/components/ServerForm.tsx`:

```typescript
import React, { useState } from 'react'
import { apiClient } from '../api/client'

interface SupervisorConf {
  name: string
  group?: string
  command: string
  directory?: string
  autostart?: boolean
  autorestart?: string
  startsecs?: number
  startretries?: number
  priority?: number
  stopsignal?: string
  stopwaitsecs?: number
  stopasgroup?: boolean
  stdout_logfile?: string
  stdout_logfile_maxbytes?: number
  stdout_logfile_backups?: number
  stderr_logfile?: string
  stderr_logfile_maxbytes?: number
  stderr_logfile_backups?: number
  redirect_stderr?: boolean
  environment?: Record<string, string>
  numprocs?: number
  process_name?: string
}

interface MiseTool {
  name: string
  version?: string
}

interface ServerData {
  id?: number
  name: string
  transport: 'stdio' | 'http' | 'sse'
  url?: string
  command?: string
  arguments?: string[]
  port: number
  supervisor_conf: SupervisorConf
  tools?: MiseTool[]
  task_install?: string
  task_uninstall?: string
  task_run?: string
  envs?: Record<string, string>
  created_at?: string
  updated_at?: string
}

interface ServerFormProps {
  onSuccess: () => void
  onCancel: () => void
  editingId?: number | null
}

export function ServerForm({ onSuccess, onCancel, editingId }: ServerFormProps) {
  const [name, setName] = useState('')
  const [transport, setTransport] = useState<'stdio' | 'http' | 'sse'>('stdio')
  const [port, setPort] = useState(8100)
  const [command, setCommand] = useState('')
  const [url, setUrl] = useState('')
  const [arguments_, setArguments] = useState('')
  const [directory, setDirectory] = useState('')
  const [autostart, setAutostart] = useState(true)
  const [autorestart, setAutorestart] = useState('unexpected')
  const [priority, setPriority] = useState(100)
  const [stopsignal, setStopsignal] = useState('TERM')
  const [taskInstall, setTaskInstall] = useState('')
  const [taskRun, setTaskRun] = useState('')
  const [envVars, setEnvVars] = useState<Record<string, string>>({})
  const [tools, setTools] = useState<MiseTool[]>([])
  const [toolInput, setToolInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleAddTool = () => {
    if (toolInput.trim()) {
      const [name, version] = toolInput.split(':')
      setTools([...tools, { name: name.trim(), version: version?.trim() }])
      setToolInput('')
    }
  }

  const handleRemoveTool = (index: number) => {
    setTools(tools.filter((_, i) => i !== index))
  }

  const handleAddEnv = (key: string, value: string) => {
    if (key.trim()) {
      setEnvVars({ ...envVars, [key]: value })
    }
  }

  const handleRemoveEnv = (key: string) => {
    const newEnvs = { ...envVars }
    delete newEnvs[key]
    setEnvVars(newEnvs)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const supervisorConf: SupervisorConf = {
        name,
        command: transport === 'stdio' ? command : '',
        directory: directory || undefined,
        autostart,
        autorestart,
        priority,
        stopsignal,
        stdout_logfile: `/var/log/supervisor/mcp_${name}_stdout.log`,
        stdout_logfile_maxbytes: 50000000,
        stdout_logfile_backups: 10,
        stderr_logfile: `/var/log/supervisor/mcp_${name}_stderr.log`,
        stderr_logfile_maxbytes: 50000000,
        stderr_logfile_backups: 10,
        redirect_stderr: false,
        environment: envVars,
        numprocs: 1,
        process_name: `mcp_${name}`,
      }

      const serverData: ServerData = {
        id: editingId || Math.floor(Math.random() * 1000000),
        name,
        transport,
        port: parseInt(port as any),
        command: transport === 'stdio' ? command : undefined,
        url: transport !== 'stdio' ? url : undefined,
        arguments: arguments_ ? arguments_.split(/\s+/).filter(Boolean) : [],
        supervisor_conf: supervisorConf,
        tools,
        task_install: taskInstall || undefined,
        task_run: taskRun || undefined,
        envs: envVars,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }

      if (editingId) {
        await apiClient.updateServer(editingId, serverData)
      } else {
        await apiClient.createServer(serverData)
      }

      onSuccess()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save server')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form className="server-form" onSubmit={handleSubmit}>
      <h3>{editingId ? 'Edit Server Configuration' : 'Add New MCP Server'}</h3>

      {error && <div className="error-message">{error}</div>}

      {/* Basic Information */}
      <fieldset className="form-section">
        <legend>Basic Information</legend>
        
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="name">Server Name *</label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="my-mcp-server"
              required
            />
            <small>Identifier for the MCP server (used for supervisord process name)</small>
          </div>

          <div className="form-group">
            <label htmlFor="transport">Transport Type *</label>
            <select
              id="transport"
              value={transport}
              onChange={(e) => setTransport(e.target.value as any)}
              required
            >
              <option value="stdio">stdio (Standard I/O)</option>
              <option value="http">http (HTTP)</option>
              <option value="sse">sse (Server-Sent Events)</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="port">Port *</label>
            <input
              id="port"
              type="number"
              value={port}
              onChange={(e) => setPort(parseInt(e.target.value))}
              min={8100}
              max={8999}
              required
            />
            <small>Port number for the MCP server (8100-8999)</small>
          </div>
        </div>
      </fieldset>

      {/* Transport-Specific Configuration */}
      <fieldset className="form-section">
        <legend>Transport Configuration</legend>

        {transport === 'stdio' ? (
          <div className="form-group">
            <label htmlFor="command">Command *</label>
            <input
              id="command"
              type="text"
              value={command}
              onChange={(e) => setCommand(e.target.value)}
              placeholder="python server.py"
              required={transport === 'stdio'}
            />
            <small>Command to execute for stdio transport</small>
          </div>
        ) : transport === 'http' ? (
          <div className="form-group">
            <label htmlFor="url">URL *</label>
            <input
              id="url"
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="http://localhost:8080"
              required={transport !== 'stdio'}
            />
            <small>HTTP endpoint for the MCP server</small>
          </div>
        ) : (
          <div className="form-group">
            <label htmlFor="url">SSE URL *</label>
            <input
              id="url"
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="http://localhost:8080/events"
              required={transport !== 'stdio'}
            />
            <small>Server-Sent Events endpoint</small>
          </div>
        )}

        {transport === 'stdio' && (
          <div className="form-group">
            <label htmlFor="arguments">Command Arguments</label>
            <input
              id="arguments"
              type="text"
              value={arguments_}
              onChange={(e) => setArguments(e.target.value)}
              placeholder="--option value"
            />
            <small>Space-separated arguments (optional)</small>
          </div>
        )}

        <div className="form-group">
          <label htmlFor="directory">Working Directory</label>
          <input
            id="directory"
            type="text"
            value={directory}
            onChange={(e) => setDirectory(e.target.value)}
            placeholder="/app/servers/my-server"
          />
          <small>Directory to run the command from (optional)</small>
        </div>
      </fieldset>

      {/* Supervisord Configuration */}
      <fieldset className="form-section">
        <legend>Process Management (supervisord)</legend>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="autostart">
              <input
                id="autostart"
                type="checkbox"
                checked={autostart}
                onChange={(e) => setAutostart(e.target.checked)}
              />
              Autostart
            </label>
            <small>Automatically start on supervisord startup</small>
          </div>

          <div className="form-group">
            <label htmlFor="autorestart">Autorestart Policy</label>
            <select
              id="autorestart"
              value={autorestart}
              onChange={(e) => setAutorestart(e.target.value)}
            >
              <option value="false">Never</option>
              <option value="true">Always</option>
              <option value="unexpected">On unexpected exit</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="priority">Priority</label>
            <input
              id="priority"
              type="number"
              value={priority}
              onChange={(e) => setPriority(parseInt(e.target.value))}
              min={1}
              max={999}
            />
            <small>Lower numbers start first</small>
          </div>

          <div className="form-group">
            <label htmlFor="stopsignal">Stop Signal</label>
            <select
              id="stopsignal"
              value={stopsignal}
              onChange={(e) => setStopsignal(e.target.value)}
            >
              <option value="TERM">TERM</option>
              <option value="QUIT">QUIT</option>
              <option value="INT">INT</option>
              <option value="KILL">KILL</option>
            </select>
          </div>
        </div>
      </fieldset>

      {/* Tasks */}
      <fieldset className="form-section">
        <legend>Installation & Execution Tasks</legend>

        <div className="form-group">
          <label htmlFor="taskInstall">Install Task</label>
          <input
            id="taskInstall"
            type="text"
            value={taskInstall}
            onChange={(e) => setTaskInstall(e.target.value)}
            placeholder="pip install mcp-server"
          />
          <small>Command to install dependencies (optional)</small>
        </div>

        <div className="form-group">
          <label htmlFor="taskRun">Run Task</label>
          <input
            id="taskRun"
            type="text"
            value={taskRun}
            onChange={(e) => setTaskRun(e.target.value)}
            placeholder="python server.py"
          />
          <small>Custom run command (optional)</small>
        </div>
      </fieldset>

      {/* Tools/Dependencies */}
      <fieldset className="form-section">
        <legend>Tools & Dependencies</legend>

        <div className="form-group">
          <label htmlFor="toolInput">Add Tool</label>
          <div className="input-with-button">
            <input
              id="toolInput"
              type="text"
              value={toolInput}
              onChange={(e) => setToolInput(e.target.value)}
              placeholder="python:3.10 (optional)"
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault()
                  handleAddTool()
                }
              }}
            />
            <button type="button" onClick={handleAddTool} className="btn-sm btn-secondary">
              Add
            </button>
          </div>
          <small>Specify required tools and versions (e.g., python:3.10, node:20)</small>
        </div>

        {tools.length > 0 && (
          <div className="tools-list">
            {tools.map((tool, idx) => (
              <div key={idx} className="tool-badge">
                {tool.name}{tool.version ? `:${tool.version}` : ''}
                <button
                  type="button"
                  onClick={() => handleRemoveTool(idx)}
                  className="btn-remove"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}
      </fieldset>

      {/* Environment Variables */}
      <fieldset className="form-section">
        <legend>Environment Variables</legend>

        <div className="env-vars-editor">
          {Object.entries(envVars).map(([key, value]) => (
            <div key={key} className="env-var-item">
              <input type="text" value={key} disabled className="env-key" />
              <input type="text" value={value} disabled className="env-value" />
              <button
                type="button"
                onClick={() => handleRemoveEnv(key)}
                className="btn-remove"
              >
                Remove
              </button>
            </div>
          ))}
          <div className="env-var-item">
            <input
              type="text"
              placeholder="KEY"
              id="envKey"
              className="env-key"
            />
            <input
              type="text"
              placeholder="VALUE"
              id="envValue"
              className="env-value"
            />
            <button
              type="button"
              onClick={() => {
                const key = (document.getElementById('envKey') as HTMLInputElement).value
                const value = (document.getElementById('envValue') as HTMLInputElement).value
                if (key) {
                  handleAddEnv(key, value);
                  (document.getElementById('envKey') as HTMLInputElement).value = '';
                  (document.getElementById('envValue') as HTMLInputElement).value = ''
                }
              }}
              className="btn-sm btn-secondary"
            >
              Add
            </button>
          </div>
        </div>
      </fieldset>

      {/* Form Actions */}
      <div className="form-actions">
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? 'Saving...' : editingId ? 'Update Server' : 'Create Server'}
        </button>
        <button type="button" className="btn-secondary" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </form>
  )
}
```

---

## Verification Checklist

- [ ] `frontend/src/components/ServerForm.tsx` created
- [ ] Form displays all fields correctly
- [ ] Transport-specific fields show/hide appropriately
- [ ] Tools and environment variables can be added/removed
- [ ] Form submission works
- [ ] Edit mode loads existing data

## Next Step

Proceed to [105-process-and-shared-components.md](./105-process-and-shared-components.md)
