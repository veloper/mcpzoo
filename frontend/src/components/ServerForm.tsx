import React, { useState, useEffect, useRef } from 'react'
import { apiClient } from '../api/client'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Loader2, Download } from 'lucide-react'
import { BasicTab } from './form/BasicTab'
import { ProcessTab } from './form/ProcessTab'
import { ToolsTab } from './form/ToolsTab'
import { TasksTab } from './form/TasksTab'
import { EnvironmentTab } from './form/EnvironmentTab'

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
  const [args, setArgs] = useState<string[]>([])
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
  const [envVars, setEnvVars] = useState<Record<string, string>>({})
  const [tools, setTools] = useState<MiseTool[]>([])
  const [toolName, setToolName] = useState('')
  const [toolVersion, setToolVersion] = useState('')
  const [toolError, setToolError] = useState('')
  const [toolValidating, setToolValidating] = useState(false)
  const [toolTyping, setToolTyping] = useState(false)
  const [toolValid, setToolValid] = useState<boolean | null>(null)
  const [availableVersions, setAvailableVersions] = useState<string[]>([])
  const [versionsLoading, setVersionsLoading] = useState(false)
  const [envKey, setEnvKey] = useState('')
  const [envValue, setEnvValue] = useState('')
  const [logLevel, setLogLevel] = useState('INFO')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const nameRegex = /^[a-zA-Z0-9\-_]+$/
  const toolValidationTimer = useRef<NodeJS.Timeout | null>(null)

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
          setArgs(Array.isArray(server.arguments) ? server.arguments : [])

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
    if (toolName.trim()) {
      const toolSpec = toolVersion.trim() ? `${toolName.trim()}:${toolVersion.trim()}` : toolName.trim()

      setToolValidating(true)
      setToolError('')
      try {
        const response = await apiClient.get(`/tools/mise/check/${encodeURIComponent(toolSpec)}`)
        if (response.available) {
          setTools([...tools, { name: toolName.trim(), version: toolVersion.trim() || undefined }])
          setToolName('')
          setToolVersion('')
          setToolValid(null) // Reset validation state
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

  const handleToolNameChange = (value: string) => {
    setToolName(value)
    setToolValid(null)
    setToolError('')

    // Clear existing timer
    if (toolValidationTimer.current) {
      clearTimeout(toolValidationTimer.current)
    }

    const name = value.trim()
    const version = toolVersion.trim()
    const toolSpec = version ? `${name}:${version}` : name

    if (name && name.length >= 2) {
      // Start typing indicator immediately
      setToolTyping(true)

      // Set debounced validation
      toolValidationTimer.current = setTimeout(async () => {
        setToolValidating(true)
        try {
          const response = await apiClient.get(`/tools/mise/check/${encodeURIComponent(toolSpec)}`)
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
            if (data.available) {
              // Tool is valid, fetch available versions
              fetchToolVersions(name)
            } else {
              setToolError(`"${name}" is not a valid mise tool`)
              setAvailableVersions([])
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
          setToolError(`Failed to validate "${name}": ${errorMessage}`)
        } finally {
          setToolValidating(false)
          setToolTyping(false)
        }
      }, 750)
    } else {
      // Reset states for short input
      setToolTyping(false)
      setToolValidating(false)
    }
  }

  const handleToolVersionChange = (value: string) => {
    setToolVersion(value)
    // Re-validate if we have a tool name
    if (toolName.trim()) {
      handleToolNameChange(toolName)
    }
  }

  const fetchToolVersions = async (toolName: string) => {
    setVersionsLoading(true)
    try {
      const response = await apiClient.get(`/tools/mise/versions/${encodeURIComponent(toolName)}`)
      console.log('Tool versions response:', response)

      let data = response
      if (typeof response === 'object' && response.data) {
        data = response.data
      } else if (typeof response === 'string') {
        try {
          data = JSON.parse(response)
        } catch (e) {
          console.error('Failed to parse versions response as JSON:', response)
          throw new Error('Invalid API response format')
        }
      }

      if (data && typeof data === 'object' && 'versions' in data) {
        setAvailableVersions(Array.isArray(data.versions) ? data.versions : [])
      } else {
        console.error('Invalid versions response format:', data)
        setAvailableVersions([])
      }
    } catch (err: any) {
      console.error('Failed to fetch tool versions:', err)
      setAvailableVersions([])
    } finally {
      setVersionsLoading(false)
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
        arguments: args.length > 0 ? args : undefined,
        supervisor_conf: supervisorConf,
        tools: tools && tools.length > 0 ? tools : [],
        task_install: taskInstall.trim() || undefined,
        task_uninstall: taskUninstall.trim() || undefined,
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
    <div>
        <div className="max-w-7xl">
        <div className="mb-6">
          <h1 className="text-3xl font-bold tracking-tight">
            {editingId ? 'Edit Server' : 'Add New MCP Server'}
          </h1>
          <p className="text-muted-foreground mt-2">
            Configure your Model Context Protocol server instance.
          </p>
        </div>

        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <form onSubmit={handleSubmit} className="space-y-8">
          <div className="flex gap-6">
            <div className="flex-1">
              <Tabs defaultValue="basic" className="w-full">
                <TabsList className="grid w-full grid-cols-4">
                  <TabsTrigger value="basic">Basic</TabsTrigger>
                  <TabsTrigger value="process">Process</TabsTrigger>
                  <TabsTrigger value="tools">Tools</TabsTrigger>
                  <TabsTrigger value="tasks">Tasks</TabsTrigger>
                </TabsList>

            <TabsContent value="basic">
              <BasicTab
                name={name}
                nameError={nameError}
                transport={transport}
                command={command}
                url={url}
                args={args}
                port={port}
                logLevel={logLevel}
                envVars={envVars}
                envKey={envKey}
                envValue={envValue}
                onNameChange={handleNameChange}
                onTransportChange={(v) => setTransport(v as any)}
                onCommandChange={setCommand}
                onUrlChange={setUrl}
                onArgsChange={setArgs}
                onLogLevelChange={setLogLevel}
                onEnvKeyChange={setEnvKey}
                onEnvValueChange={setEnvValue}
                onAddEnv={handleAddEnv}
                onRemoveEnv={handleRemoveEnv}
              />
            </TabsContent>



            <TabsContent value="process">
              <ProcessTab
                autostart={autostart}
                autorestart={autorestart}
                startsecs={startsecs}
                startretries={startretries}
                priority={priority}
                numprocs={numprocs}
                stopsignal={stopsignal}
                stopwaitsecs={stopwaitsecs}
                redirectStderr={redirectStderr}
                onAutostart={setAutostart}
                onAutorestart={setAutorestart}
                onStartsecs={setStartsecs}
                onStartretries={setStartretries}
                onPriority={setPriority}
                onNumprocs={setNumprocs}
                onStopsignal={setStopsignal}
                onStopwaitsecs={setStopwaitsecs}
                onRedirectStderr={setRedirectStderr}
              />
            </TabsContent>

            <TabsContent value="tools">
              <ToolsTab
                tools={tools}
                toolName={toolName}
                toolVersion={toolVersion}
                toolError={toolError}
                toolValid={toolValid}
                toolValidating={toolValidating}
                toolTyping={toolTyping}
                availableVersions={availableVersions}
                versionsLoading={versionsLoading}
                onToolNameChange={handleToolNameChange}
                onToolVersionChange={handleToolVersionChange}
                onAddTool={handleAddTool}
                onRemoveTool={handleRemoveTool}
              />
            </TabsContent>

            <TabsContent value="tasks">
              <TasksTab
                taskInstall={taskInstall}
                taskUninstall={taskUninstall}
                onTaskInstallChange={setTaskInstall}
                onTaskUninstallChange={setTaskUninstall}
              />
            </TabsContent>
              </Tabs>
            </div>

              {/* Computed Values Sidebar */}
              <div className="w-80 space-y-4">
                <Button className="w-full h-10 text-sm font-medium">
                  <Download className="mr-2 h-5 w-5" />
                  Import
                </Button>
                <div className="bg-muted/50 rounded-lg p-4">
                  <h3 className="text-sm font-medium text-muted-foreground mb-3">Computed Values</h3>
                  <div className="space-y-3">
                    <div>
                      <label className="text-xs text-muted-foreground">Working Directory</label>
                      <div className="text-sm font-mono bg-background rounded px-2 py-1 mt-1">
                        {name ? `/app/servers/${name}` : '/app/servers/{name}'}
                      </div>
                    </div>
                    <div>
                      <label className="text-xs text-muted-foreground">Program Name</label>
                      <div className="text-sm font-mono bg-background rounded px-2 py-1 mt-1">
                        {name ? `mcp_${name}` : 'mcp_{name}'}
                      </div>
                    </div>
                    <div>
                      <label className="text-xs text-muted-foreground">Port</label>
                      <div className="text-sm font-mono bg-background rounded px-2 py-1 mt-1">
                        {port !== null ? port.toString() : 'auto-assigned'}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-2 border-t pt-6">
              <Button type="submit" disabled={loading}>
                {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {editingId ? 'Update Server' : 'Create Server'}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={onCancel}
                disabled={loading}
              >
                Cancel
              </Button>
            </div>
          </form>
      </div>
    </div>
  )
}
