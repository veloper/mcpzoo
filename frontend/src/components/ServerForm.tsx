import React, { useState, useEffect } from 'react'
import { apiClient } from '../api/client'
import { Form, Button, Container, Row, Col, Alert, Badge, Tab, Tabs } from 'react-bootstrap'

interface SupervisorConf {
  name: string
  group: string
  command: string
  directory?: string
  umask: string
  user: string
  autostart?: boolean
  autorestart?: string
  startsecs?: number
  startretries?: number
  priority?: number
  stopsignal?: string
  stopwaitsecs?: number
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

interface MCPServerConfig {
  id?: string
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
  editingId?: string | null
}

export function ServerForm({ onSuccess, onCancel, editingId }: ServerFormProps) {
  // Test HMR - change this comment once more to trigger hot reload - final test - last attempt - final - last - final - last - final - final - final
  const [name, setName] = useState('')
  const [nameError, setNameError] = useState('')
  const [transport, setTransport] = useState<'stdio' | 'http' | 'sse'>('stdio')
  const [command, setCommand] = useState('')
  const [url, setUrl] = useState('')
  const [arguments_, setArguments] = useState('')
  const [port, setPort] = useState<number | null>(null)
  const [autostart, setAutostart] = useState(true)
  const [autorestart, setAutorestart] = useState('unexpected')
  const [startsecs, setStartsecs] = useState(1)
  const [startretries, setStartretries] = useState(3)
  const [priority, setPriority] = useState(999)
  const [stopsignal, setStopsignal] = useState('TERM')
  const [stopwaitsecs, setStopwaitsecs] = useState(10)
  const [redirectStderr, setRedirectStderr] = useState(false)
  const [numprocs, setNumprocs] = useState(1)
  const [taskInstall, setTaskInstall] = useState('')
  const [taskUninstall, setTaskUninstall] = useState('')
  const [taskRun, setTaskRun] = useState('')
  const [envVars, setEnvVars] = useState<Record<string, string>>({})
  const [tools, setTools] = useState<MiseTool[]>([])
  const [toolInput, setToolInput] = useState('')
  const [toolError, setToolError] = useState('')
  const [toolValidating, setToolValidating] = useState(false)
  const [toolValid, setToolValid] = useState<boolean | null>(null)
  const [envKey, setEnvKey] = useState('')
  const [envValue, setEnvValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const nameRegex = /^[a-zA-Z0-9\-_]+$/

  useEffect(() => {
    if (editingId) {
      // Load server data for editing
      const loadServer = async () => {
        try {
          console.log('Starting to load server data for editingId:', editingId)
          const server = await apiClient.getServer(editingId)
          console.log('Received server data:', server)

          if (!server) {
            throw new Error('Server data is null or undefined')
          }

          // Load basic fields
          console.log('Loading basic fields...')
          setName(server.name || '')
          setTransport(server.transport || 'stdio')
          setCommand(server.command || '')
          setUrl(server.url || '')
          setPort(server.port || null)
          setArguments(Array.isArray(server.arguments) ? server.arguments.join(' ') : '')

          // Load supervisor config
          console.log('Loading supervisor config...')
          if (server.supervisor_conf) {
            setAutostart(server.supervisor_conf.autostart ?? true)
            setAutorestart(server.supervisor_conf.autorestart || 'unexpected')
            setStartsecs(server.supervisor_conf.startsecs || 1)
            setStartretries(server.supervisor_conf.startretries || 3)
            setPriority(server.supervisor_conf.priority || 999)
            setStopsignal(server.supervisor_conf.stopsignal || 'TERM')
            setStopwaitsecs(server.supervisor_conf.stopwaitsecs || 10)
            setRedirectStderr(server.supervisor_conf.redirect_stderr ?? false)
            setNumprocs(server.supervisor_conf.numprocs || 1)
            if (server.supervisor_conf.environment && typeof server.supervisor_conf.environment === 'object') {
              setEnvVars(server.supervisor_conf.environment)
            }
          }

          // Load tools
          console.log('Loading tools...')
          if (Array.isArray(server.tools)) {
            setTools(server.tools.map((t: any) => ({
              name: t.name || '',
              version: t.version
            })))
          }

          // Load tasks
          console.log('Loading tasks...')
          setTaskInstall(server.task_install || '')
          setTaskUninstall(server.task_uninstall || '')
          setTaskRun(server.task_run || '')

          // Load envs
          console.log('Loading envs...')
          if (server.envs && typeof server.envs === 'object') {
            setEnvVars(server.envs)
          }

          console.log('Server data loaded successfully')
        } catch (err: any) {
          console.error('Failed to load server - detailed error:', err)
          console.error('Error stack:', err.stack)
          console.error('Error response:', err.response)
          setError(`Failed to load server: ${err.message || 'Unknown error'}`)
        }
      }
      loadServer()
    }
  }, [editingId])

  const handleNameChange = (value: string) => {
    setName(value)
    if (value && !nameRegex.test(value)) {
      setNameError('Server name may only contain letters, numbers, hyphens, and underscores')
    } else {
      setNameError('')
    }
  }

  const handleAddTool = async () => {
    if (toolInput.trim()) {
      const [n, v] = toolInput.split(':')
      const toolName = n.trim()
      
      setToolValidating(true)
      setToolError('')
      try {
        const response = await apiClient.get(`/tools/mise/check/${toolName}`)
        if (response.available) {
          setTools([...tools, { name: toolName, version: v?.trim() }])
          setToolInput('')
        } else {
          setToolError(`Tool "${toolName}" not found in mise: ${response.error}`)
        }
      } catch (err: any) {
        setToolError(`Failed to validate tool "${toolName}": ${err.response?.data?.detail || err.message}`)
      } finally {
        setToolValidating(false)
      }
    }
  }

  const handleToolInputChange = async (value: string) => {
    console.log('Tool input changed to!!!:', value)
    setToolInput(value)
    setToolValid(null)
    setToolError('')

    if (!value.includes(':')) {
      // Validate tool name on input
      const toolName = value.trim()
      if (toolName && toolName.length >= 2) {

        setToolValidating(true)
        try {
          const response = await apiClient.get(`/tools/mise/check/${toolName}`)
          console.log('Tool validation response:', response)

          let data = response
          if (typeof response === 'object' && response.data) {
            data = response.data
          } else if (typeof response === 'string') {
            try {
              data = JSON.parse(response)
            } catch (e) {
              console.error('Failed to parse response as JSON:', response)
              throw new Error('Invalid API response format')
            }
          }

          if (data && typeof data === 'object' && 'available' in data) {
            setToolValid(data.available)
            if (!data.available) {
              setToolError(`"${toolName}" is not a valid mise tool`)
            }
          } else {
            console.error('Invalid response format:', data)
            throw new Error('Invalid API response')
          }
        } catch (err: any) {
          setToolValid(false)
          const errorMessage = err.response?.data?.detail ||
                              err.response?.data?.message ||
                              err.message ||
                              'Unknown error'
          setToolError(`Failed to validate "${toolName}": ${errorMessage}`)
        } finally {
          setToolValidating(false)
        }
      }
    } else {
      // Reset validation for versioned tools (validate on add)
      setToolValidating(false)
    }
  }

  const handleRemoveTool = (idx: number) => {
    setTools(tools.filter((_, i) => i !== idx))
  }

  const handleAddEnv = () => {
    if (envKey.trim()) {
      setEnvVars({ ...envVars, [envKey]: envValue })
      setEnvKey('')
      setEnvValue('')
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
      // Validate required fields
      if (!name.trim()) throw new Error('Server name is required')
      if (!nameRegex.test(name)) throw new Error('Server name may only contain letters, numbers, hyphens, and underscores')
      if (transport === 'stdio' && !command.trim()) throw new Error('Command is required for stdio transport')
      if (transport !== 'stdio' && !url.trim()) throw new Error('URL is required for http/sse transport')

      const supervisorConf = {
        name,
        group: 'mcp_servers',
        command: transport === 'stdio' ? command : '',
        directory: name ? `/app/servers/${name}` : undefined,
        umask: '022',
        user: 'root',
        autostart,
        autorestart,
        startsecs: parseInt(startsecs.toString()),
        startretries: parseInt(startretries.toString()),
        priority: parseInt(priority.toString()),
        stopsignal,
        stopwaitsecs: parseInt(stopwaitsecs.toString()),
        stdout_logfile: `/var/log/supervisor/mcp_${name}_stdout.log`,
        stdout_logfile_maxbytes: 50_000_000,
        stdout_logfile_backups: 10,
        stderr_logfile: `/var/log/supervisor/mcp_${name}_stderr.log`,
        stderr_logfile_maxbytes: 50_000_000,
        stderr_logfile_backups: 10,
        redirect_stderr: redirectStderr,
        environment: Object.keys(envVars).length > 0 ? envVars : {},
        numprocs: parseInt(numprocs.toString()),
      }

      const config = {
        id: editingId || undefined,
        name: name.trim(),
        transport: transport as 'stdio' | 'http' | 'sse',
        // Port will be assigned by backend on save
        command: transport === 'stdio' ? command.trim() : undefined,
        url: transport !== 'stdio' ? url.trim() : undefined,
        arguments: arguments_.trim() ? arguments_.split(/\s+/).filter(Boolean) : [],
        supervisor_conf: supervisorConf,
        tools: tools && tools.length > 0 ? tools : [],
        task_install: taskInstall.trim() || undefined,
        task_uninstall: taskUninstall.trim() || undefined,
        task_run: taskRun.trim() || undefined,
        envs: Object.keys(envVars).length > 0 ? envVars : {},
        created_at: editingId ? undefined : new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }

      // Remove undefined values to keep payload clean
      Object.keys(config).forEach(k => {
        if (config[k as keyof typeof config] === undefined) {
          delete config[k as keyof typeof config]
        }
      })

      if (editingId) {
        await apiClient.updateServer(editingId, config)
      } else {
        await apiClient.createServer(config)
      }

      onSuccess()
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to save server')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Container className="py-4">
      <Row>
        <Col lg={8}>
          <h3 className="mb-4">{editingId ? 'Edit Server' : 'Add New MCP Server'}</h3>

          {error && <Alert variant="danger">{error}</Alert>}

          <Form onSubmit={handleSubmit}>
            <Tabs defaultActiveKey="basic" className="mb-4">
              <Tab eventKey="basic" title="Basic Configuration">
                {/* Basic Info */}
                <Form.Group className="mb-3">
                  <Form.Label>Server Name *</Form.Label>
                  <Form.Control
                    value={name}
                    onChange={(e) => handleNameChange(e.target.value)}
                    placeholder="my-server"
                    isInvalid={!!nameError}
                    required
                  />
                  {nameError && <Form.Control.Feedback type="invalid">{nameError}</Form.Control.Feedback>}
                </Form.Group>

                <Row>
                  <Col md={12}>
                    <Form.Group className="mb-3">
                      <Form.Label>Transport Type *</Form.Label>
                      <Form.Select value={transport} onChange={(e) => setTransport(e.target.value as any)} required>
                        <option value="stdio">stdio (Standard I/O)</option>
                        <option value="http">http (HTTP)</option>
                        <option value="sse">sse (Server-Sent Events)</option>
                      </Form.Select>
                    </Form.Group>
                  </Col>
                </Row>

                {/* Transport-specific config */}
                {transport === 'stdio' && (
                  <Form.Group className="mb-3">
                    <Form.Label>Command *</Form.Label>
                    <Form.Control value={command} onChange={(e) => setCommand(e.target.value)} placeholder="python server.py" required />
                  </Form.Group>
                )}

                {transport !== 'stdio' && (
                  <Form.Group className="mb-3">
                    <Form.Label>URL *</Form.Label>
                    <Form.Control type="url" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="http://localhost:8080" required />
                  </Form.Group>
                )}

                {transport === 'stdio' && (
                  <Form.Group className="mb-3">
                    <Form.Label>Arguments</Form.Label>
                    <Form.Control value={arguments_} onChange={(e) => setArguments(e.target.value)} placeholder="--option value" />
                    <Form.Text>Space-separated arguments</Form.Text>
                  </Form.Group>
                )}

                {/* Working Directory and Program Name */}
                <Form.Group className="mb-3">
                  <Form.Label>Working Directory</Form.Label>
                  <Form.Control
                    value={name ? `/app/servers/${name}` : ''}
                    disabled
                    placeholder="/app/servers/{name}"
                  />
                  <Form.Text>Auto-generated based on server name</Form.Text>
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Program Name</Form.Label>
                  <Form.Control
                    value={name ? `mcp_${name}` : ''}
                    disabled
                    placeholder="mcp_{name}"
                  />
                  <Form.Text>Auto-generated based on server name</Form.Text>
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Port</Form.Label>
                  <Form.Control
                    value={port !== null ? port : 'auto'}
                    disabled
                  />
                  <Form.Text>{port !== null ? 'Assigned port' : 'Will be auto-assigned on save'}</Form.Text>
                </Form.Group>
              </Tab>

              <Tab eventKey="process" title="Process Management">
                <Row>
                  <Col md={6}>
                    <Form.Group className="mb-3">
                      <Form.Check
                        type="checkbox"
                        label="Autostart"
                        checked={autostart}
                        onChange={(e) => setAutostart(e.target.checked)}
                      />
                      <Form.Text>Start process when supervisord starts</Form.Text>
                    </Form.Group>
                  </Col>
                  <Col md={6}>
                    <Form.Group className="mb-3">
                      <Form.Label>Autorestart Policy</Form.Label>
                      <Form.Select value={autorestart} onChange={(e) => setAutorestart(e.target.value)}>
                        <option value="false">Never</option>
                        <option value="true">Always</option>
                        <option value="unexpected">On unexpected exit</option>
                      </Form.Select>
                    </Form.Group>
                  </Col>
                </Row>

                <Row>
                  <Col md={3}>
                    <Form.Group className="mb-3">
                      <Form.Label>Start Secs</Form.Label>
                      <Form.Control type="number" value={startsecs} onChange={(e) => setStartsecs(parseInt(e.target.value))} min={1} />
                      <Form.Text>Seconds to stay up to consider started</Form.Text>
                    </Form.Group>
                  </Col>
                  <Col md={3}>
                    <Form.Group className="mb-3">
                      <Form.Label>Start Retries</Form.Label>
                      <Form.Control type="number" value={startretries} onChange={(e) => setStartretries(parseInt(e.target.value))} min={0} />
                      <Form.Text>Retries before giving up</Form.Text>
                    </Form.Group>
                  </Col>
                  <Col md={3}>
                    <Form.Group className="mb-3">
                      <Form.Label>Priority</Form.Label>
                      <Form.Control type="number" value={priority} onChange={(e) => setPriority(parseInt(e.target.value))} min={1} max={999} />
                      <Form.Text>Lower = starts first</Form.Text>
                    </Form.Group>
                  </Col>
                  <Col md={3}>
                    <Form.Group className="mb-3">
                      <Form.Label>Numprocs</Form.Label>
                      <Form.Control type="number" value={numprocs} onChange={(e) => setNumprocs(parseInt(e.target.value))} min={1} />
                    </Form.Group>
                  </Col>
                </Row>

                <Row>
                  <Col md={4}>
                    <Form.Group className="mb-3">
                      <Form.Label>Stop Signal</Form.Label>
                      <Form.Select value={stopsignal} onChange={(e) => setStopsignal(e.target.value)}>
                        <option value="TERM">TERM</option>
                        <option value="QUIT">QUIT</option>
                        <option value="INT">INT</option>
                        <option value="KILL">KILL</option>
                      </Form.Select>
                    </Form.Group>
                  </Col>
                  <Col md={4}>
                    <Form.Group className="mb-3">
                      <Form.Label>Stop Wait (secs)</Form.Label>
                      <Form.Control type="number" value={stopwaitsecs} onChange={(e) => setStopwaitsecs(parseInt(e.target.value))} min={1} />
                    </Form.Group>
                  </Col>
                </Row>

                <Form.Group className="mb-3">
                  <Form.Check
                    type="checkbox"
                    label="Redirect stderr to stdout"
                    checked={redirectStderr}
                    onChange={(e) => setRedirectStderr(e.target.checked)}
                  />
                </Form.Group>
              </Tab>

              <Tab eventKey="tools" title="Tools & Dependencies">
                <div className="mb-3">
                  <Form.Label>Add Tool</Form.Label>
                  <div className="d-flex gap-2">
                    <div className="flex-grow-1 position-relative">
                      <Form.Control
                        value={toolInput}
                        onChange={(e) => handleToolInputChange((e.target as HTMLInputElement).value)}
                        placeholder="python:3.10"
                        isInvalid={!!toolError}
                        isValid={toolValid === true}
                      />
                      {toolValidating && (
                        <div className="position-absolute top-50 end-0 translate-middle-y me-3">
                          <div className="spinner-border spinner-border-sm text-secondary" role="status">
                            <span className="visually-hidden">Validating...</span>
                          </div>
                        </div>
                      )}
                    </div>
                    <Button variant="secondary" onClick={handleAddTool} disabled={toolValidating}>
                      {toolValidating ? 'Validating...' : 'Add'}
                    </Button>
                  </div>
                  {toolError && <Form.Text className="text-danger">{toolError}</Form.Text>}
                  <Form.Text>Tool name and optional version (e.g., python:3.10, node:20)</Form.Text>
                </div>

                {tools.length > 0 && (
                  <div className="mb-3">
                    {tools.map((t, i) => (
                      <Badge key={i} bg="light" text="dark" className="me-2 mb-2">
                        {t.name}{t.version ? `:${t.version}` : ''}
                        <button
                          type="button"
                          onClick={() => handleRemoveTool(i)}
                          className="btn-close btn-sm ms-2"
                          style={{ fontSize: '0.7rem' }}
                        />
                      </Badge>
                    ))}
                  </div>
                )}
              </Tab>

              <Tab eventKey="environment" title="Environment & Tasks">
                <h6 className="mb-3">Installation & Execution Tasks</h6>

                <Form.Group className="mb-3">
                  <Form.Label>Install Task</Form.Label>
                  <Form.Control value={taskInstall} onChange={(e) => setTaskInstall(e.target.value)} placeholder="pip install mcp-server" />
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Uninstall Task</Form.Label>
                  <Form.Control value={taskUninstall} onChange={(e) => setTaskUninstall(e.target.value)} placeholder="pip uninstall mcp-server -y" />
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Run Task</Form.Label>
                  <Form.Control value={taskRun} onChange={(e) => setTaskRun(e.target.value)} placeholder="python server.py" />
                  <Form.Text>Custom run command (optional override)</Form.Text>
                </Form.Group>

                <hr />

                <h6 className="mb-3">Environment Variables</h6>

                {Object.entries(envVars).map(([k, v]) => (
                  <div key={k} className="d-flex gap-2 mb-2 align-items-center">
                    <Form.Control value={k} disabled size="sm" style={{ flex: 1 }} />
                    <Form.Control value={v} disabled size="sm" style={{ flex: 1 }} />
                    <Button size="sm" variant="outline-danger" onClick={() => handleRemoveEnv(k)}>Remove</Button>
                  </div>
                ))}

                <div className="d-flex gap-2 mb-3">
                  <Form.Control
                    value={envKey}
                    onChange={(e) => setEnvKey(e.target.value)}
                    placeholder="KEY"
                    size="sm"
                    style={{ flex: 1 }}
                  />
                  <Form.Control
                    value={envValue}
                    onChange={(e) => setEnvValue(e.target.value)}
                    placeholder="VALUE"
                    size="sm"
                    style={{ flex: 1 }}
                  />
                  <Button size="sm" variant="secondary" onClick={handleAddEnv}>Add</Button>
                </div>
              </Tab>
            </Tabs>

            {/* Actions */}
            <div className="d-flex gap-2 align-items-center border-top pt-3">
              <Button type="submit" variant="primary" disabled={loading}>
                {loading ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                    Saving...
                  </>
                ) : (
                  editingId ? 'Update Server' : 'Create Server'
                )}
              </Button>
              <Button type="button" variant="secondary" onClick={onCancel} disabled={loading}>Cancel</Button>
            </div>
          </Form>
        </Col>
      </Row>
    </Container>
  )
}
