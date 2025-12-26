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
import { LoggingTab } from './form/LoggingTab'
import { FilesTab } from './form/FilesTab'

import { McpServerImport } from './McpServerImport'
import { toast } from 'sonner'



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
  port?: number
  // Flat fields from ServerConfiguration model
  autostart?: boolean
  autorestart?: string
  priority?: number
  startsecs?: number
  startretries?: number
  stopsignal?: string
  stopwaitsecs?: number
  stdout_logfile?: string
  stdout_logfile_maxbytes?: number
  stdout_logfile_backups?: number
  stderr_logfile?: string
  stderr_logfile_maxbytes?: number
  stderr_logfile_backups?: number
  redirect_stderr?: boolean
  tools?: MiseTool[]
  task_install?: string
  task_uninstall?: string
  envs?: Record<string, string>
  log_level?: string
  created_at?: string
  updated_at?: string
  synced_at?: string
}

interface ServerFormProps {
  onSuccess: (serverId?: string) => void
  onCancel: () => void
  editingId?: string | null
}

export function ServerForm({ onSuccess, onCancel, editingId }: ServerFormProps) {
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
  const [stdoutLogfile, setStdoutLogfile] = useState('')
  const [stdoutLogfileMaxbytes, setStdoutLogfileMaxbytes] = useState(50_000_000)
  const [stdoutLogfileBackups, setStdoutLogfileBackups] = useState(10)
  const [stderrLogfile, setStderrLogfile] = useState('')
  const [stderrLogfileMaxbytes, setStderrLogfileMaxbytes] = useState(50_000_000)
  const [stderrLogfileBackups, setStderrLogfileBackups] = useState(10)

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
  const [originalServer, setOriginalServer] = useState<any>(null)
  const [initialFormHash, setInitialFormHash] = useState<string>('')
  const [importDialogOpen, setImportDialogOpen] = useState(false)

  // Simple hash function for form state comparison
  const hashFormState = () => {
    const state = {
      name: name.trim(),
      transport,
      command: transport === 'stdio' ? command.trim() : '',
      url: transport !== 'stdio' ? url.trim() : '',
      args,
      autostart,
      autorestart,
      startsecs,
      startretries,
      priority,
      stopsignal,
      stopwaitsecs,
      redirectStderr,
      stdoutLogfile,
      stdoutLogfileMaxbytes,
      stdoutLogfileBackups,
      stderrLogfile,
      stderrLogfileMaxbytes,
      stderrLogfileBackups,

      taskInstall: taskInstall.trim(),
      taskUninstall: taskUninstall.trim(),
      envVars,
      tools,
      logLevel
    }
    return JSON.stringify(state)
  }

  const nameRegex = /^[a-zA-Z][a-zA-Z0-9_-]*[a-zA-Z0-9]$/
  const toolValidationTimer = useRef<NodeJS.Timeout | null>(null)

  const getCurrentServerConfig = () => {
    // Compute log file paths based on server ID and redirect_stderr setting
    const serverId = editingId || '{id}'
    const logFileBase = `/var/log/supervisor/${serverId}`

    let stdoutLogfilePath: string
    let stderrLogfilePath: string

    if (redirectStderr) {
      // When stderr is redirected, both use the combined log file
      stdoutLogfilePath = `${logFileBase}_combined.log`
      stderrLogfilePath = `${logFileBase}_combined.log`
    } else {
      // Separate log files for stdout and stderr
      stdoutLogfilePath = `${logFileBase}_out.log`
      stderrLogfilePath = `${logFileBase}_err.log`
    }



    const config = {
      id: editingId || undefined,
      name: name.trim(),
      transport: transport as 'stdio' | 'http' | 'sse',
      // Port will be assigned by backend on save
      command: transport === 'stdio' ? command.trim() : undefined,
      url: transport !== 'stdio' ? url.trim() : undefined,
      arguments: args.length > 0 ? args : undefined,
      // Flat fields from ServerConfiguration model
      autostart,
      autorestart,
      priority: parseInt(priority.toString()),
      startsecs: parseInt(startsecs.toString()),
      startretries: parseInt(startretries.toString()),
      stopsignal,
      stopwaitsecs: parseInt(stopwaitsecs.toString()),
      stdout_logfile: stdoutLogfilePath,
      stdout_logfile_maxbytes: stdoutLogfileMaxbytes,
      stdout_logfile_backups: stdoutLogfileBackups,
      stderr_logfile: stderrLogfilePath,
      stderr_logfile_maxbytes: stderrLogfileMaxbytes,
      stderr_logfile_backups: stderrLogfileBackups,
      redirect_stderr: redirectStderr,
      tools: tools && tools.length > 0 ? tools : [],
      task_install: taskInstall.trim() || undefined,
      task_uninstall: taskUninstall.trim() || undefined,
      envs: Object.keys(envVars).length > 0 ? envVars : {},
      log_level: logLevel,
      created_at: editingId ? undefined : new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }



    // Remove undefined values to keep payload clean
    Object.keys(config).forEach(k => {
      if (config[k as keyof typeof config] === undefined) {
        delete config[k as keyof typeof config]
      }
    })

    return config
  }

  // Check if current form state differs from original server data
  const hasChanges = React.useMemo(() => {
    if (!editingId) {
      // For new servers, always allow saving if there's a name
      return name.trim().length > 0
    }

    // For editing servers, compare current hash with initial hash
    if (!initialFormHash) {
      return false // No changes if we haven't set the initial hash yet
    }

    const currentHash = hashFormState()
    return currentHash !== initialFormHash
  }, [editingId, initialFormHash, name, transport, command, url, args, autostart, autorestart, startsecs, startretries, priority, stopsignal, stopwaitsecs, redirectStderr, taskInstall, taskUninstall, envVars, tools, logLevel])

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

          // Load supervisor config (now flat fields)
          console.log('Loading supervisor config...')
          setAutostart(server.autostart ?? true)
          setAutorestart(server.autorestart || 'unexpected')
          setStartsecs(server.startsecs || 1)
          setStartretries(server.startretries || 3)
          setPriority(server.priority || 999)
          setStopsignal(server.stopsignal || 'TERM')
          setStopwaitsecs(server.stopwaitsecs || 10)
          setRedirectStderr(server.redirect_stderr ?? false)
          setStdoutLogfile(server.stdout_logfile || '')
          setStdoutLogfileMaxbytes(server.stdout_logfile_maxbytes || 50_000_000)
          setStdoutLogfileBackups(server.stdout_logfile_backups || 10)
          setStderrLogfile(server.stderr_logfile || '')
          setStderrLogfileMaxbytes(server.stderr_logfile_maxbytes || 50_000_000)
          setStderrLogfileBackups(server.stderr_logfile_backups || 10)

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

          // Load timestamps
          console.log('Loading timestamps...')

          // Load log level
          console.log('Loading log level...')
          setLogLevel(server.log_level || 'INFO')

          console.log('Server data loaded successfully')
        } catch (err: any) {
          console.error('Failed to load server - detailed error:', err)
          console.error('Error stack:', err.stack)
          console.error('Error response:', err.response)
          setError(`Failed to load server: ${err.message || 'Unknown error'}`)
        }
      }
      loadServer()
    } else {
      // For new servers, set initial hash to empty (will be set when form changes)
      setInitialFormHash('')
    }
  }, [editingId])

  // Set initial hash after form state is loaded
  useEffect(() => {
    if (editingId && !initialFormHash && name) {
      // Only set initial hash when we have loaded data and name is set
      setInitialFormHash(hashFormState())
    }
  }, [editingId, name, transport, command, url, args, autostart, autorestart, startsecs, startretries, priority, stopsignal, stopwaitsecs, redirectStderr, taskInstall, taskUninstall, envVars, tools, logLevel, initialFormHash])

  const handleNameChange = (value: string) => {
    setName(value)
    if (value && !nameRegex.test(value)) {
      setNameError('Server name must start with a letter and contain only letters, numbers, hyphens, and underscores (cannot start or end with a dash or underscore)')
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

  const handleImport = (config: any) => {
    try {
      // Update form fields with imported config
      setName(config.name || '')
      setTransport(config.transport || 'stdio')
      setCommand(config.command || '')
      setUrl(config.url || '')
      setArgs(Array.isArray(config.arguments) ? config.arguments : [])
      setPort(config.port || null)

      // Load supervisor config
      if (config.supervisor_conf) {
        setAutostart(config.supervisor_conf.autostart ?? true)
        setAutorestart(config.supervisor_conf.autorestart || 'unexpected')
        setStartsecs(config.supervisor_conf.startsecs || 1)
        setStartretries(config.supervisor_conf.startretries || 3)
        setPriority(config.supervisor_conf.priority || 999)
        setStopsignal(config.supervisor_conf.stopsignal || 'TERM')
        setStopwaitsecs(config.supervisor_conf.stopwaitsecs || 10)
        setRedirectStderr(config.supervisor_conf.redirect_stderr ?? false)
        setStdoutLogfile(config.supervisor_conf.stdout_logfile || '')
        setStdoutLogfileMaxbytes(config.supervisor_conf.stdout_logfile_maxbytes || 50_000_000)
        setStdoutLogfileBackups(config.supervisor_conf.stdout_logfile_backups || 10)
        setStderrLogfile(config.supervisor_conf.stderr_logfile || '')
        setStderrLogfileMaxbytes(config.supervisor_conf.stderr_logfile_maxbytes || 50_000_000)
        setStderrLogfileBackups(config.supervisor_conf.stderr_logfile_backups || 10)

        if (config.supervisor_conf.environment && typeof config.supervisor_conf.environment === 'object') {
          setEnvVars(config.supervisor_conf.environment)
        }
      }

      // Load tools
      if (Array.isArray(config.tools)) {
        setTools(config.tools.map((t: any) => ({
          name: t.name || '',
          version: t.version
        })))
      }

      // Load tasks
      setTaskInstall(config.task_install || '')
      setTaskUninstall(config.task_uninstall || '')

      // Load envs
      if (config.envs && typeof config.envs === 'object') {
        setEnvVars(config.envs)
      }

      // Load log level
      setLogLevel(config.log_level || 'INFO')

      // Clear any existing errors
      setError('')
      setNameError('')

      // Show success message
      toast.success('Configuration imported successfully')

      // Reset initial hash to allow saving
      setInitialFormHash('')
    } catch (err: any) {
      console.error('Failed to import configuration:', err)
      setError('Failed to import configuration')
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      // Validate required fields
      if (!name.trim()) throw new Error('Server name is required')
      if (!nameRegex.test(name)) throw new Error('Server name must start with a letter and contain only letters, numbers, hyphens, and underscores (cannot start or end with a dash or underscore)')
      if (transport === 'stdio' && !command.trim()) throw new Error('Command is required for stdio transport')
      if (transport !== 'stdio' && !url.trim()) throw new Error('URL is required for http/sse transport')

      // Use the unified config creation function
      const config = getCurrentServerConfig()

      let savedServer
      if (editingId) {
        savedServer = await apiClient.updateServer(editingId, config)
        // Show success toast
        toast.success("All changes saved")
        // Update hashes to match current state, disabling the save button
        setOriginalServer(getCurrentServerConfig())
        setInitialFormHash(hashFormState())
      } else {
        savedServer = await apiClient.createServer(config)
        // Show success toast
        toast.success("Server created successfully")
        // Redirect to edit page for the new server
        onSuccess(savedServer.id)
        return
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to save server')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
        <div className="max-w-7xl">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">
              {editingId ? 'Edit Server' : 'Add New MCP Server'}
            </h1>
            <p className="text-muted-foreground mt-2">
              Configure your Model Context Protocol server instance.
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              className="h-10 text-sm font-medium"
              onClick={() => setImportDialogOpen(true)}
            >
              <Download className="mr-2 h-5 w-5" />
              Import
            </Button>
            <Button onClick={handleSubmit} disabled={loading || !hasChanges} className="h-10 text-sm font-medium">
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Save
            </Button>
          </div>
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
                <TabsList className="grid w-full grid-cols-6">
                  <TabsTrigger value="basic">Basic</TabsTrigger>
                  <TabsTrigger value="process">Process</TabsTrigger>
                  <TabsTrigger value="logging">Logging</TabsTrigger>
                  <TabsTrigger value="tools">Tools</TabsTrigger>
                  <TabsTrigger value="tasks">Tasks</TabsTrigger>
                  <TabsTrigger value="files">Files</TabsTrigger>
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
                envVars={envVars}
                envKey={envKey}
                envValue={envValue}
                onNameChange={handleNameChange}
                onTransportChange={(v) => setTransport(v as any)}
                onCommandChange={setCommand}
                onUrlChange={setUrl}
                onArgsChange={setArgs}
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

                stopsignal={stopsignal}
                stopwaitsecs={stopwaitsecs}
                onAutostart={setAutostart}
                onAutorestart={setAutorestart}
                onStartsecs={setStartsecs}
                onStartretries={setStartretries}
                onPriority={setPriority}

                onStopsignal={setStopsignal}
                onStopwaitsecs={setStopwaitsecs}
              />
            </TabsContent>

            <TabsContent value="logging">
              <LoggingTab
                redirectStderr={redirectStderr}
                stdoutLogfileMaxbytes={stdoutLogfileMaxbytes}
                stdoutLogfileBackups={stdoutLogfileBackups}
                stderrLogfileMaxbytes={stderrLogfileMaxbytes}
                stderrLogfileBackups={stderrLogfileBackups}
                logLevel={logLevel}
                serverId={editingId || undefined}
                onRedirectStderr={setRedirectStderr}
                onStdoutLogfileMaxbytes={setStdoutLogfileMaxbytes}
                onStdoutLogfileBackups={setStdoutLogfileBackups}
                onStderrLogfileMaxbytes={setStderrLogfileMaxbytes}
                onStderrLogfileBackups={setStderrLogfileBackups}
                onLogLevelChange={setLogLevel}
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

            <TabsContent value="files">
              <FilesTab
                serverId={editingId || ''}
                serverConfig={getCurrentServerConfig()}
              />
            </TabsContent>
              </Tabs>
            </div>

              {/* Computed Values Sidebar */}
              <div className="w-80 space-y-4">
                <div className="bg-muted/50 rounded-lg p-4">
                  <h3 className="text-sm font-medium text-muted-foreground mb-3">Computed Values</h3>
                  <div className="space-y-3">
                    <div>
                      <label className="text-xs text-muted-foreground">Working Directory</label>
                      <div className="text-sm font-mono bg-background rounded px-2 py-1 mt-1">
                        {editingId ? `/app/servers/${editingId}` : name ? `/app/servers/{id}` : '/app/servers/{id}'}
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


          </form>
      </div>

      <McpServerImport
        open={importDialogOpen}
        onOpenChange={setImportDialogOpen}
        onImport={handleImport}
      />
    </div>
  )
}
