import React from 'react'
import { useProcesses } from '../hooks/useProcesses'
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
import { Loader2, RefreshCw, Play, Square, RotateCcw } from 'lucide-react'

export function ProcessesList() {
  const { processes, loading, error, startProcess, stopProcess, fetchProcesses } = useProcesses()

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

  const mcpProcesses = processes.filter(p => p.name.startsWith('mcp_'))

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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">MCP Server Processes</h2>
          <p className="text-sm text-muted-foreground">Managed by supervisord [group:mcp_servers]</p>
        </div>
        <Button 
          variant="outline" 
          size="sm"
          onClick={() => fetchProcesses()}
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

      {mcpProcesses.length === 0 ? (
        <Alert>
          <AlertDescription>
            No MCP server processes running. Click "Sync Processes" in the Servers tab to generate them.
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
              {mcpProcesses.map((proc) => (
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

