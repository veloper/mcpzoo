import React, { createContext, useState, useEffect, useRef, useContext } from 'react'
import { apiClient } from '../api/client'
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

interface ServerFormContextType {
  // Basic state
  name: string
  nameError: string
  transport: 'stdio' | 'http' | 'sse'
  command: string
  url: string
  args: string[]
  port: number | null
  editingId?: string | null

  // Process state
  autostart: boolean
  autorestart: string
  startsecs: number
  startretries: number
  priority: number
  stopsignal: string
  stopwaitsecs: number

  // Logging state
  redirectStderr: boolean
  stdoutLogfileMaxbytes: number
  stdoutLogfileBackups: number
  stderrLogfileMaxbytes: number
  stderrLogfileBackups: number
  logLevel: string

  // Tools state
  tools: MiseTool[]
  toolName: string
  toolVersion: string
  toolError: string
  toolValidating: boolean
  toolTyping: boolean
  toolValid: boolean | null
  availableVersions: string[]
  versionsLoading: boolean

  // Tasks state
  taskInstall: string
  taskUninstall: string

  // Environment state
  envVars: Record<string, string>
  envKey: string
  envValue: string

  // Headers state
  headers: Record<string, string>
  headerKey: string
  headerValue: string

  // UI state
  loading: boolean
  error: string
  importDialogOpen: boolean
  loaded: boolean

  // Computed values
  hasChanges: boolean

  // Handlers
  handleNameChange: (value: string) => void
  handleTransportChange: (value: string) => void
  handleCommandChange: (value: string) => void
  handleUrlChange: (value: string) => void
  handleArgsChange: (args: string[]) => void

  handleAutostartChange: (value: boolean) => void
  handleAutorestartChange: (value: string) => void
  handleStartsecsChange: (value: number) => void
  handleStartretriesChange: (value: number) => void
  handlePriorityChange: (value: number) => void
  handleStopsignalChange: (value: string) => void
  handleStopwaitsecsChange: (value: number) => void

  handleRedirectStderrChange: (value: boolean) => void
  handleStdoutLogfileMaxbytesChange: (value: number) => void
  handleStdoutLogfileBackupsChange: (value: number) => void
  handleStderrLogfileMaxbytesChange: (value: number) => void
  handleStderrLogfileBackupsChange: (value: number) => void
  handleLogLevelChange: (value: string) => void

  handleToolNameChange: (value: string) => void
  handleToolVersionChange: (value: string) => void
  handleAddTool: () => void
  handleRemoveTool: (index: number) => void

  handleTaskInstallChange: (value: string) => void
  handleTaskUninstallChange: (value: string) => void

  handleEnvKeyChange: (value: string) => void
  handleEnvValueChange: (value: string) => void
  handleAddEnv: () => void
  handleRemoveEnv: (key: string) => void

  handleHeaderKeyChange: (value: string) => void
  handleHeaderValueChange: (value: string) => void
  handleAddHeader: () => void
  handleRemoveHeader: (key: string) => void

  handleImport: (config: any) => void
  handleSubmit: (e: React.FormEvent) => Promise<void>
  setImportDialogOpen: (open: boolean) => void

  // Utilities
  getCurrentServerConfig: () => MCPServerConfig
}

const ServerFormContext = createContext<ServerFormContextType | undefined>(undefined)

interface ServerFormProviderProps {
  editingId?: number | null
  onSuccess: (serverId?: number) => void
  onCancel: () => void
  children: React.ReactNode
}

export function ServerFormProvider({ editingId, onSuccess, onCancel, children }: ServerFormProviderProps) {
  // Basic state
  const [name, setName] = useState('')
  const [nameError, setNameError] = useState('')
  const [transport, setTransport] = useState<'stdio' | 'http' | 'sse'>('stdio')
  const [command, setCommand] = useState('')
  const [url, setUrl] = useState('')
  const [args, setArgs] = useState<string[]>([])
  const [port, setPort] = useState<number | null>(null)

  // Process state
  const [autostart, setAutostart] = useState(true)
  const [autorestart, setAutorestart] = useState('unexpected')
  const [startsecs, setStartsecs] = useState(1)
  const [startretries, setStartretries] = useState(3)
  const [priority, setPriority] = useState(999)
  const [stopsignal, setStopsignal] = useState('TERM')
  const [stopwaitsecs, setStopwaitsecs] = useState(10)

  // Logging state
  const [redirectStderr, setRedirectStderr] = useState(false)
  const [stdoutLogfileMaxbytes, setStdoutLogfileMaxbytes] = useState(50_000_000)
  const [stdoutLogfileBackups, setStdoutLogfileBackups] = useState(10)
  const [stderrLogfileMaxbytes, setStderrLogfileMaxbytes] = useState(50_000_000)
  const [stderrLogfileBackups, setStderrLogfileBackups] = useState(10)
  const [logLevel, setLogLevel] = useState('INFO')

  // Tools state
  const [tools, setTools] = useState<MiseTool[]>([])
  const [toolName, setToolName] = useState('')
  const [toolVersion, setToolVersion] = useState('')
  const [toolError, setToolError] = useState('')
  const [toolValidating, setToolValidating] = useState(false)
  const [toolTyping, setToolTyping] = useState(false)
  const [toolValid, setToolValid] = useState<boolean | null>(null)
  const [availableVersions, setAvailableVersions] = useState<string[]>([])
  const [versionsLoading, setVersionsLoading] = useState(false)

  // Tasks state
  const [taskInstall, setTaskInstall] = useState('')
  const [taskUninstall, setTaskUninstall] = useState('')

  // Environment state
  const [envVars, setEnvVars] = useState<Record<string, string>>({})
  const [envKey, setEnvKey] = useState('')
  const [envValue, setEnvValue] = useState('')

  // Headers state
  const [headers, setHeaders] = useState<Record<string, string>>({})
  const [headerKey, setHeaderKey] = useState('')
  const [headerValue, setHeaderValue] = useState('')

  // UI state
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [originalServer, setOriginalServer] = useState<any>(null)
  const [initialFormHash, setInitialFormHash] = useState<string>('')
  const [loaded, setLoaded] = useState(false)
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
      stdoutLogfileMaxbytes,
      stdoutLogfileBackups,
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

  // Check if current form state differs from original server data
  const hasChanges = React.useMemo(() => {
    // Always allow saving
    return true
  }, [])

  const getCurrentServerConfig = (): MCPServerConfig => {
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
      headers: Object.keys(headers).length > 0 ? headers : {},
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

  // Load server data for editing
  useEffect(() => {
    if (editingId) {
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
          setStdoutLogfileMaxbytes(server.stdout_logfile_maxbytes || 50_000_000)
          setStdoutLogfileBackups(server.stdout_logfile_backups || 10)
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

          // Load headers
          console.log('Loading headers...')
          if (server.headers && typeof server.headers === 'object') {
            setHeaders(server.headers)
          }

          // Load log level
          console.log('Loading log level...')
          setLogLevel(server.log_level || 'INFO')

          console.log('Server data loaded successfully')

          // Set initial hash after all data is loaded
          setInitialFormHash(hashFormState())

          // Mark as loaded
          setLoaded(true)
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

  // Handlers
  const handleNameChange = (value: string) => {
    setName(value)
    if (value && !nameRegex.test(value)) {
      setNameError('Server name must start with a letter and contain only letters, numbers, hyphens, and underscores (cannot start or end with a dash or underscore)')
    } else {
      setNameError('')
    }
  }

  const handleTransportChange = (value: string) => {
    setTransport(value as 'stdio' | 'http' | 'sse')
  }

  const handleCommandChange = (value: string) => {
    setCommand(value)
  }

  const handleUrlChange = (value: string) => {
    setUrl(value)
  }

  const handleArgsChange = (args: string[]) => {
    setArgs(args)
  }

  const handleAutostartChange = (value: boolean) => {
    setAutostart(value)
  }

  const handleAutorestartChange = (value: string) => {
    setAutorestart(value)
  }

  const handleStartsecsChange = (value: number) => {
    setStartsecs(value)
  }

  const handleStartretriesChange = (value: number) => {
    setStartretries(value)
  }

  const handlePriorityChange = (value: number) => {
    setPriority(value)
  }

  const handleStopsignalChange = (value: string) => {
    setStopsignal(value)
  }

  const handleStopwaitsecsChange = (value: number) => {
    setStopwaitsecs(value)
  }

  const handleRedirectStderrChange = (value: boolean) => {
    setRedirectStderr(value)
  }

  const handleStdoutLogfileMaxbytesChange = (value: number) => {
    setStdoutLogfileMaxbytes(value)
  }

  const handleStdoutLogfileBackupsChange = (value: number) => {
    setStdoutLogfileBackups(value)
  }

  const handleStderrLogfileMaxbytesChange = (value: number) => {
    setStderrLogfileMaxbytes(value)
  }

  const handleStderrLogfileBackupsChange = (value: number) => {
    setStderrLogfileBackups(value)
  }

  const handleLogLevelChange = (value: string) => {
    setLogLevel(value)
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

  const handleRemoveTool = (index: number) => {
    setTools(tools.filter((_, i) => i !== index))
  }

  const handleTaskInstallChange = (value: string) => {
    setTaskInstall(value)
  }

  const handleTaskUninstallChange = (value: string) => {
    setTaskUninstall(value)
  }

  const handleEnvKeyChange = (value: string) => {
    setEnvKey(value)
  }

  const handleEnvValueChange = (value: string) => {
    setEnvValue(value)
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

  const handleHeaderKeyChange = (value: string) => {
    setHeaderKey(value)
  }

  const handleHeaderValueChange = (value: string) => {
    setHeaderValue(value)
  }

  const handleAddHeader = () => {
    if (headerKey.trim()) {
      setHeaders({ ...headers, [headerKey]: headerValue })
      setHeaderKey('')
      setHeaderValue('')
    }
  }

  const handleRemoveHeader = (key: string) => {
    const newHeaders = { ...headers }
    delete newHeaders[key]
    setHeaders(newHeaders)
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
        setStdoutLogfileMaxbytes(config.supervisor_conf.stdout_logfile_maxbytes || 50_000_000)
        setStdoutLogfileBackups(config.supervisor_conf.stdout_logfile_backups || 10)
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

      // Load headers
      if (config.headers && typeof config.headers === 'object') {
        setHeaders(config.headers)
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

  const contextValue: ServerFormContextType = {
    // Basic state
    name,
    nameError,
    transport,
    command,
    url,
    args,
    port,
    editingId,

    // Process state
    autostart,
    autorestart,
    startsecs,
    startretries,
    priority,
    stopsignal,
    stopwaitsecs,

    // Logging state
    redirectStderr,
    stdoutLogfileMaxbytes,
    stdoutLogfileBackups,
    stderrLogfileMaxbytes,
    stderrLogfileBackups,
    logLevel,

    // Tools state
    tools,
    toolName,
    toolVersion,
    toolError,
    toolValidating,
    toolTyping,
    toolValid,
    availableVersions,
    versionsLoading,

    // Tasks state
    taskInstall,
    taskUninstall,

    // Environment state
    envVars,
    envKey,
    envValue,

    // Headers state
    headers,
    headerKey,
    headerValue,

    // UI state
    loading,
    error,
    importDialogOpen,
    loaded,

    // Computed values
    hasChanges,

    // Handlers
    handleNameChange,
    handleTransportChange,
    handleCommandChange,
    handleUrlChange,
    handleArgsChange,

    handleAutostartChange,
    handleAutorestartChange,
    handleStartsecsChange,
    handleStartretriesChange,
    handlePriorityChange,
    handleStopsignalChange,
    handleStopwaitsecsChange,

    handleRedirectStderrChange,
    handleStdoutLogfileMaxbytesChange,
    handleStdoutLogfileBackupsChange,
    handleStderrLogfileMaxbytesChange,
    handleStderrLogfileBackupsChange,
    handleLogLevelChange,

    handleToolNameChange,
    handleToolVersionChange,
    handleAddTool,
    handleRemoveTool,

    handleTaskInstallChange,
    handleTaskUninstallChange,

    handleEnvKeyChange,
    handleEnvValueChange,
    handleAddEnv,
    handleRemoveEnv,

    handleHeaderKeyChange,
    handleHeaderValueChange,
    handleAddHeader,
    handleRemoveHeader,

    handleImport,
    handleSubmit,
    setImportDialogOpen,

    // Utilities
    getCurrentServerConfig,
  }

  return (
    <ServerFormContext.Provider value={contextValue}>
      {children}
    </ServerFormContext.Provider>
  )
}

export function useServerForm() {
  const context = useContext(ServerFormContext)
  if (context === undefined) {
    throw new Error('useServerForm must be used within a ServerFormProvider')
  }
  return context
}

export { ServerFormContext }
