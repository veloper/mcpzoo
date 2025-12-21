import React from 'react'
import { useProcesses } from '../hooks/useProcesses'
import { apiClient } from '../api/client'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Loader2, RefreshCw, Play, Square, RotateCcw, Settings, FileText } from 'lucide-react'
import { toast } from 'sonner'

export function ProcessesList() {
  const { processes, loading, error, startProcess, stopProcess, fetchProcesses } = useProcesses()
  const [logsDialogOpen, setLogsDialogOpen] = React.useState(false)
  const [selectedProcess, setSelectedProcess] = React.useState<string | null>(null)
  const [processLogs, setProcessLogs] = React.useState<string[]>([])
  const [logsLoading, setLogsLoading] = React.useState(false)

  if (loading && processes.length === 0) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    )
  }

  const allProcesses = processes

  const getStatusVariant = (status: string) => {
    const s = status.toUpperCase()
    if (s === 'RUNNING') return 'default'
    if (s === 'STOPPED') return 'secondary'
    if (s === 'FATAL') return 'destructive'
    return 'outline'
  }

  const formatUptime = (seconds?: number) => {
    if (seconds === undefined || seconds === 0) return '-'
    const h = Math.floor(seconds / 3600)
    const m = Math.floor((seconds % 3600) / 60)
    const s = seconds % 60
    return `${h}h ${m}m ${s}s`
  }



  const handleViewLogs = async (processName: string) => {
    setSelectedProcess(processName)
    setLogsLoading(true)
    setLogsDialogOpen(true)

    try {
      const data = await apiClient.getProcessLogs(processName)
      // Convert structured logs to display format
      const logLines = data.logs.map((log: any) => `[${log.type}] ${log.message}`)
      setProcessLogs(logLines)
    } catch (err: any) {
      setProcessLogs(['Error loading logs'])
    } finally {
      setLogsLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">MCP Server Processes</h1>
          <p className="text-muted-foreground">Managed by supervisord [group:mcp_servers]</p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchProcesses}
            disabled={loading}
          >
            {loading ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="mr-2 h-4 w-4" />
            )}
            Refresh
          </Button>
        </div>
      </div>

      {allProcesses.length === 0 ? (
        <Alert>
          <AlertDescription>
            No processes running.
          </AlertDescription>
        </Alert>
      ) : (
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Process Name</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>PID</TableHead>
                <TableHead>Uptime</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {allProcesses.map((proc) => (
                <TableRow key={proc.name}>
                  <TableCell className="font-medium">{proc.name}</TableCell>
                  <TableCell>
                    <Badge variant={getStatusVariant(proc.status) as any}>
                      {proc.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="font-mono text-xs">{proc.pid || '-'}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">{formatUptime(proc.uptime)}</TableCell>
                  <TableCell className="text-right space-x-2">
                    <Dialog open={logsDialogOpen && selectedProcess === proc.name} onOpenChange={(open) => {
                      setLogsDialogOpen(open)
                      if (!open) setSelectedProcess(null)
                    }}>
                      <DialogTrigger asChild>
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-8 w-8 p-0 text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                          onClick={() => handleViewLogs(proc.name)}
                          title="View Logs"
                        >
                          <FileText className="h-4 w-4" />
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="max-w-4xl max-h-[80vh]">
                        <DialogHeader>
                          <DialogTitle>Logs for {proc.name}</DialogTitle>
                          <DialogDescription>
                            Process logs (stdout/stderr)
                          </DialogDescription>
                        </DialogHeader>
                        <ScrollArea className="h-[60vh] w-full">
                          {logsLoading ? (
                            <div className="flex items-center justify-center h-32">
                              <Loader2 className="h-6 w-6 animate-spin" />
                              <span className="ml-2">Loading logs...</span>
                            </div>
                          ) : (
                            <Table>
                              <TableHeader>
                                <TableRow>
                                  <TableHead className="w-16">#</TableHead>
                                  <TableHead>Log Entry</TableHead>
                                </TableRow>
                              </TableHeader>
                              <TableBody>
                                {processLogs.map((log, index) => (
                                  <TableRow key={index}>
                                    <TableCell className="font-mono text-xs text-muted-foreground w-16">
                                      {index + 1}
                                    </TableCell>
                                    <TableCell className="font-mono text-sm">
                                      <pre className="whitespace-pre-wrap break-words">{log}</pre>
                                    </TableCell>
                                  </TableRow>
                                ))}
                              </TableBody>
                            </Table>
                          )}
                        </ScrollArea>
                      </DialogContent>
                    </Dialog>
                    {proc.status !== 'RUNNING' ? (
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-8 w-8 p-0 text-green-600 hover:text-green-700 hover:bg-green-50"
                        onClick={() => startProcess(proc.name)}
                        title="Start"
                      >
                        <Play className="h-4 w-4" />
                      </Button>
                    ) : (
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-8 w-8 p-0 text-amber-600 hover:text-amber-700 hover:bg-amber-50"
                        onClick={() => stopProcess(proc.name)}
                        title="Stop"
                      >
                        <Square className="h-4 w-4" />
                      </Button>
                    )}
                    <Button
                      size="sm"
                      variant="outline"
                      className="h-8 w-8 p-0"
                      onClick={() => {
                        stopProcess(proc.name)
                        setTimeout(() => startProcess(proc.name), 1000)
                      }}
                      title="Restart"
                    >
                      <RotateCcw className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  )
}
